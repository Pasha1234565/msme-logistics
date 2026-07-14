from __future__ import unicode_literals

import frappe
from frappe.utils import today, add_days


def daily_check_overdue_trips():
	"""Daily scheduler: send notifications for trips not dispatched past planned date."""
	overdue_trips = frappe.db.get_all(
		"Delivery Trip",
		filters={
			"trip_status": "Planned",
			"planned_dispatch_date": ["<", today()],
		},
		fields=["name", "transporter", "planned_dispatch_date"],
	)

	for dt in overdue_trips:
		days_overdue = frappe.utils.date_diff(today(), dt.planned_dispatch_date)

		notification = frappe.new_doc("Notification Log")
		notification.for_user = frappe.db.get_value(
			"User", {"user_type": "System User", "enabled": 1}, "name"
		)
		notification.title = frappe._("Trip Not Dispatched")
		notification.subject = frappe._(
			"Delivery Trip {0} (Transporter: {1}) was planned for dispatch on {2} "
			"but is still in 'Planned' status. Overdue by {3} day(s)."
		).format(dt.name, dt.transporter, dt.planned_dispatch_date, days_overdue)
		notification.document_type = "Delivery Trip"
		notification.document_name = dt.name
		notification.insert(ignore_permissions=True)

	frappe.db.commit()


def weekly_update_transporter_analytics():
	"""Weekly scheduler: update SLA compliance stats on Transporter doctype."""
	transporters = frappe.db.get_all("Transporter", filters={"status": "Active"}, pluck="name")

	for transporter_name in transporters:
		# Calculate SLA compliance: % of delivered stops within delivery window
		stats = frappe.db.sql("""
			SELECT
				COUNT(*) as total_delivered,
				SUM(
					CASE
						WHEN ds.delivery_window_end IS NOT NULL
							AND ds.actual_arrival_time IS NOT NULL
							AND TIME(ds.actual_arrival_time) <= ds.delivery_window_end
						THEN 1
						ELSE 0
					END
				) as on_time
			FROM `tabDelivery Stop` ds
			INNER JOIN `tabDelivery Trip` dt
				ON dt.name = ds.parent AND ds.parenttype = 'Delivery Trip'
			WHERE dt.transporter = %s
				AND ds.status = 'Delivered'
		""", transporter_name, as_dict=True)[0]

		total = stats.total_delivered or 0
		on_time = stats.on_time or 0
		sla_pct = round((on_time / total) * 100, 2) if total > 0 else 0

		# Update trip count
		trip_count = frappe.db.count("Delivery Trip", {"transporter": transporter_name})

		frappe.db.set_value("Transporter", transporter_name, {
			"total_trips": trip_count,
			"sla_compliance_pct": sla_pct,
		})

	frappe.db.commit()
