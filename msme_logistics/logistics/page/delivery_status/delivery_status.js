frappe.pages['delivery-status'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Delivery Status'),
		single_column: true,
	});

	// ── Build the page HTML ──
	$(page.body).html(get_page_html());

	// ── Wire up interactions ──
	let $input = page.body.find('#ds-tracking-input');
	let $btn = page.body.find('#ds-track-btn');
	let $error = page.body.find('#ds-error');
	let $spinner = page.body.find('#ds-spinner');
	let $results = page.body.find('#ds-results');

	$btn.on('click', function () {
		track($input.val().trim().toUpperCase());
	});

	$input.on('keydown', function (e) {
		if (e.key === 'Enter') {
			track($input.val().trim().toUpperCase());
		}
	});

	function track(trackingId) {
		if (!trackingId) {
			show_error(__('Please enter a tracking ID'));
			return;
		}
		hide_error();
		$spinner.removeClass('hide');
		$results.addClass('hide');

		frappe.call({
			method: 'msme_logistics.api.tracking.track_order',
			args: { tracking_id: trackingId },
			callback: function (r) {
				$spinner.addClass('hide');
				if (r.message) {
					render_results(r.message);
				}
			},
			error: function (err) {
				$spinner.addClass('hide');
				var msg =
					(err && (err.message || err._error_message)) ||
					__('No order found for this tracking ID. Please check and try again.');
				show_error(msg);
			},
		});
	}

	function render_results(data) {
		$results.removeClass('hide');

		// ── Stepper ──
		render_stepper(data.status);

		// ── Badges ──
		page.body.find('#ds-failed-badge').toggle(data.status === 'Failed');
		page.body.find('#ds-rescheduled-badge').toggle(data.status === 'Rescheduled');

		// ── Info cards ──
		page.body.find('#ds-location').text(data.current_location || '—');
		page.body.find('#ds-eta').text(format_date(data.estimated_delivery_date) || '—');

		// ── Timeline ──
		render_timeline(data.timeline || []);
	}

	function render_stepper(status) {
		var $steps = page.body.find('.ds-step');
		var $connectors = page.body.find('.ds-connector-line');

		$steps.removeClass('active completed failed');
		$connectors.removeClass('completed');

		// ── Status to stepper step mapping ──
		var stepOrder = ['Pending', 'Shipped', 'In Transit', 'Out for Delivery', 'Delivered'];
		var stepKeys = ['shipped', 'in_transit', 'out_for_delivery', 'delivered'];

		if (status === 'Failed') {
			set_step('shipped', 'completed');
			set_connector(0, true);
			set_step('in_transit', 'completed');
			set_connector(1, true);
			set_step('out_for_delivery', 'failed');
			return;
		}

		if (status === 'Rescheduled') {
			set_step('shipped', 'completed');
			set_connector(0, true);
			set_step('in_transit', 'completed');
			set_connector(1, true);
			set_step('out_for_delivery', 'active');
			return;
		}

		// Find index in the step order
		var idx = stepOrder.indexOf(status);
		if (idx < 0) idx = 1; // Unknown status → treat as 'Shipped'

		if (idx >= 5) {
			// Delivered — all completed
			set_step('shipped', 'completed');
			set_connector(0, true);
			set_step('in_transit', 'completed');
			set_connector(1, true);
			set_step('out_for_delivery', 'completed');
			set_connector(2, true);
			set_step('delivered', 'completed');
			return;
		}

		// Steps before idx = completed, step at idx = active, rest = untouched
		for (var i = 0; i < stepKeys.length; i++) {
			if (i < idx) {
				set_step(stepKeys[i], 'completed');
				if (i < stepKeys.length - 1) set_connector(i, true);
			} else if (i === idx) {
				set_step(stepKeys[i], 'active');
			} else {
				break;
			}
		}
	}

	function set_step(key, cls) {
		page.body.find('.ds-step[data-step="' + key + '"]').addClass(cls);
	}

	function set_connector(idx, completed) {
		if (completed) {
			$connectors.eq(idx).addClass('completed');
		}
	}

	function render_timeline(timeline) {
		var $container = page.body.find('#ds-timeline-list');
		if (!timeline.length) {
			$container.html(
				'<div class="text-muted text-center py-4">' + __('No tracking history yet') + '</div>'
			);
			return;
		}

		var html = '';
		timeline.forEach(function (entry) {
			var statusClass = 'status-' + (entry.status || '').toLowerCase().replace(/\s+/g, '-');
			var statusLabel = entry.status || 'Unknown';
			var locationHtml = entry.location_label
				? '<div class="ds-timeline-location">📍 ' +
				  frappe.utils.escapeHtml(entry.location_label) +
				  '</div>'
				: '';
			var timeHtml = entry.timestamp
				? '<div class="ds-timeline-time">' + format_timestamp(entry.timestamp) + '</div>'
				: '';
			var remarksHtml = entry.remarks
				? '<div class="ds-timeline-remarks">"' +
				  frappe.utils.escapeHtml(entry.remarks) +
				  '"</div>'
				: '';

			html +=
				'<div class="ds-timeline-entry">' +
				'<div class="ds-timeline-marker">' +
				'<div class="ds-timeline-dot ' + statusClass + '"></div>' +
				'<div class="ds-timeline-line"></div>' +
				'</div>' +
				'<div class="ds-timeline-content">' +
				'<div class="ds-timeline-status">' + frappe.utils.escapeHtml(statusLabel) + '</div>' +
				locationHtml +
				timeHtml +
				remarksHtml +
				'</div>' +
				'</div>';
		});
		$container.html(html);
	}

	function format_date(dateStr) {
		if (!dateStr) return null;
		try {
			var d = new Date(dateStr + 'T00:00:00');
			return d.toLocaleDateString('en-IN', {
				day: 'numeric',
				month: 'long',
				year: 'numeric',
			});
		} catch (e) {
			return dateStr;
		}
	}

	function format_timestamp(ts) {
		if (!ts) return '';
		try {
			var d = new Date(ts);
			return d.toLocaleDateString('en-IN', {
				day: 'numeric',
				month: 'short',
				year: 'numeric',
				hour: '2-digit',
				minute: '2-digit',
			});
		} catch (e) {
			return ts;
		}
	}

	function show_error(msg) {
		$error.text(msg).removeClass('hide');
	}

	function hide_error() {
		$error.text('').addClass('hide');
	}
};

// ── Page HTML template ──
function get_page_html() {
	return `
<div class="ds-page" style="max-width: 780px; margin: 0 auto; padding: 1rem 0;">
	<!-- Search Form -->
	<div class="frappe-card p-4 mb-4">
		<div class="row">
			<div class="col-md-8">
				<label class="form-label" for="ds-tracking-input">
					${__('Tracking ID')}
				</label>
				<div class="input-group">
					<input
						type="text"
						id="ds-tracking-input"
						class="form-control"
						placeholder="e.g. TRK-A7X9K2M1"
						style="text-transform: uppercase; letter-spacing: 1px;"
						maxlength="12"
						autocomplete="off"
					/>
					<button id="ds-track-btn" class="btn btn-primary" type="button">
						${__('Track')}
					</button>
				</div>
				<div id="ds-error" class="text-danger mt-2 hide" style="font-size: 0.9rem;"></div>
			</div>
			<div class="col-md-4 d-flex align-items-end">
				<div class="text-muted small">
					${__('Enter the 12-character tracking ID (TRK-XXXXXXXX) shared with you.')}
				</div>
			</div>
		</div>
	</div>

	<!-- Loading Spinner -->
	<div id="ds-spinner" class="text-center py-5 hide">
		<div class="spinner-border text-primary" role="status">
			<span class="sr-only">${__('Loading...')}</span>
		</div>
		<p class="text-muted mt-2">${__('Looking up your order...')}</p>
	</div>

	<!-- Results Panel -->
	<div id="ds-results" class="hide">
		<!-- Stepper -->
		<div class="frappe-card p-4 mb-3">
			<div class="ds-stepper">
				<div class="ds-step" data-step="shipped">
					<div class="ds-step-indicator"><div class="ds-step-dot"></div></div>
					<div class="ds-step-label">${__('Shipped')}</div>
				</div>
				<div class="ds-step-connector"><div class="ds-connector-line"></div></div>
				<div class="ds-step" data-step="in_transit">
					<div class="ds-step-indicator"><div class="ds-step-dot"></div></div>
					<div class="ds-step-label">${__('In Transit')}</div>
				</div>
				<div class="ds-step-connector"><div class="ds-connector-line"></div></div>
				<div class="ds-step" data-step="out_for_delivery">
					<div class="ds-step-indicator"><div class="ds-step-dot"></div></div>
					<div class="ds-step-label">${__('Out for Delivery')}</div>
				</div>
				<div class="ds-step-connector"><div class="ds-connector-line"></div></div>
				<div class="ds-step" data-step="delivered">
					<div class="ds-step-indicator"><div class="ds-step-dot"></div></div>
					<div class="ds-step-label">${__('Delivered')}</div>
				</div>
			</div>
			<div id="ds-failed-badge" class="text-center mt-3 hide">
				<span class="badge badge-danger" style="font-size: 0.95rem; padding: 0.4rem 1rem; border-radius: 20px;">
					⚠ ${__('Delivery Failed')}
				</span>
			</div>
			<div id="ds-rescheduled-badge" class="text-center mt-3 hide">
				<span class="badge badge-warning" style="font-size: 0.95rem; padding: 0.4rem 1rem; border-radius: 20px;">
					🔄 ${__('Rescheduled')}
				</span>
			</div>
		</div>

		<!-- Info Cards -->
		<div class="row mb-3">
			<div class="col-md-6 mb-2 mb-md-0">
				<div class="frappe-card p-3 h-100">
					<div class="text-muted text-uppercase small font-weight-bold mb-1">
						${__('Current Location')}
					</div>
					<div id="ds-location" class="h5 font-weight-bold mb-0" style="color: #1a1a2e;">—</div>
				</div>
			</div>
			<div class="col-md-6">
				<div class="frappe-card p-3 h-100">
					<div class="text-muted text-uppercase small font-weight-bold mb-1">
						${__('Delivery Expected')}
					</div>
					<div id="ds-eta" class="h5 font-weight-bold mb-0" style="color: #1a1a2e;">—</div>
				</div>
			</div>
		</div>

		<!-- Timeline -->
		<div class="frappe-card p-4">
			<h6 class="text-uppercase small font-weight-bold text-muted mb-3">
				📋 ${__('Tracking History')}
			</h6>
			<div id="ds-timeline-list">
				<div class="text-muted text-center py-4">${__('No tracking history yet')}</div>
			</div>
		</div>
	</div>
</div>

<style>
.ds-stepper {
	display: flex;
	align-items: flex-start;
	justify-content: center;
	padding: 0.5rem 0;
}

.ds-step {
	display: flex;
	flex-direction: column;
	align-items: center;
	flex: 0 0 auto;
}

.ds-step-indicator {
	display: flex;
	align-items: center;
	justify-content: center;
}

.ds-step-dot {
	width: 20px;
	height: 20px;
	border-radius: 50%;
	background: #e2e8f0;
	border: 3px solid #cbd5e1;
	transition: all 0.3s ease;
	position: relative;
}

.ds-step.active .ds-step-dot {
	background: #2490ef;
	border-color: #2490ef;
	box-shadow: 0 0 0 4px rgba(36, 144, 239, 0.2);
}

.ds-step.completed .ds-step-dot {
	background: #28a745;
	border-color: #28a745;
}

.ds-step.completed .ds-step-dot::after {
	content: "\\2713";
	position: absolute;
	top: 50%;
	left: 50%;
	transform: translate(-50%, -50%);
	color: #fff;
	font-size: 11px;
	font-weight: bold;
}

.ds-step.failed .ds-step-dot {
	background: #dc3545;
	border-color: #dc3545;
	box-shadow: 0 0 0 4px rgba(220, 53, 69, 0.2);
}

.ds-step.failed .ds-step-dot::after {
	content: "\\2717";
	position: absolute;
	top: 50%;
	left: 50%;
	transform: translate(-50%, -50%);
	color: #fff;
	font-size: 11px;
	font-weight: bold;
}

.ds-step-label {
	font-size: 0.7rem;
	color: #94a3b8;
	margin-top: 0.4rem;
	text-align: center;
	font-weight: 500;
	line-height: 1.2;
	transition: color 0.3s ease;
}

.ds-step.active .ds-step-label { color: #2490ef; font-weight: 600; }
.ds-step.completed .ds-step-label { color: #28a745; font-weight: 600; }
.ds-step.failed .ds-step-label { color: #dc3545; }

.ds-step-connector {
	flex: 1;
	display: flex;
	align-items: center;
	padding: 0 4px;
	min-width: 30px;
	max-width: 60px;
}

.ds-connector-line {
	height: 3px;
	background: #e2e8f0;
	width: 100%;
	border-radius: 2px;
	transition: background 0.3s ease;
	position: relative;
	top: -10px;
}

.ds-connector-line.completed { background: #28a745; }

/* Timeline */
.ds-timeline-entry {
	display: flex;
	gap: 0.75rem;
	padding: 0.75rem 0;
	border-bottom: 1px solid #f1f5f9;
}
.ds-timeline-entry:last-child { border-bottom: none; }

.ds-timeline-marker {
	flex: 0 0 12px;
	display: flex;
	flex-direction: column;
	align-items: center;
}

.ds-timeline-dot {
	width: 12px;
	height: 12px;
	border-radius: 50%;
	background: #e2e8f0;
	flex-shrink: 0;
}

.ds-timeline-dot.status-delivered { background: #28a745; }
.ds-timeline-dot.status-failed { background: #dc3545; }
.ds-timeline-dot.status-rescheduled { background: #ffc107; }
.ds-timeline-dot.status-pending { background: #94a3b8; }
.ds-timeline-dot.status-shipped,
.ds-timeline-dot.status-in-transit,
.ds-timeline-dot.status-out-for-delivery { background: #2490ef; }

.ds-timeline-line {
	width: 2px;
	flex: 1;
	background: #e2e8f0;
	min-height: 20px;
	margin-top: 4px;
}

.ds-timeline-content { flex: 1; min-width: 0; }
.ds-timeline-status { font-weight: 600; font-size: 0.9rem; color: #1a1a2e; }
.ds-timeline-location { font-size: 0.8rem; color: #64748b; margin-top: 0.15rem; }
.ds-timeline-time { font-size: 0.75rem; color: #94a3b8; margin-top: 0.15rem; }
.ds-timeline-remarks { font-size: 0.8rem; color: #64748b; font-style: italic; margin-top: 0.2rem; }

@media (max-width: 480px) {
	.ds-step-label { font-size: 0.6rem; }
	.ds-step-dot { width: 16px; height: 16px; }
}
</style>`;
}
