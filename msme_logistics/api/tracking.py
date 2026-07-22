from __future__ import unicode_literals

import math

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import add_days


# ─────────────────────────────────────────────
# Phase 2 — ETA logic (internal / whitelisted)
# ─────────────────────────────────────────────


@frappe.whitelist()
def get_estimated_delivery(stop_name):
	"""Return the estimated delivery date for a Delivery Stop.

	Priority:
	1. Manually set `estimated_delivery_date` on the stop itself
	2. Derived from the parent trip's `trip_date` + transporter's
	   `default_transit_days`, prorated by the stop's sequence position

	Args:
		stop_name: The `name` of the Delivery Stop row

	Returns:
		dict with "estimated_delivery_date" (str or None) and "source"
		("manual" | "derived" | "unavailable")
	"""
	if not stop_name:
		frappe.throw(_("Delivery Stop name is required"))

	# Fetch stop fields — only what we need
	stop = frappe.db.get_value(
		"Delivery Stop",
		stop_name,
		["name", "estimated_delivery_date", "sequence_no", "parent", "parenttype"],
		as_dict=True,
	)
	if not stop:
		frappe.throw(_("Delivery Stop {0} not found").format(stop_name), frappe.DoesNotExistError)

	# Priority 1: manually set date
	if stop.estimated_delivery_date:
		return {
			"estimated_delivery_date": str(stop.estimated_delivery_date),
			"source": "manual",
		}

	# Priority 2: derive from trip + transporter
	if stop.parent and stop.parenttype == "Delivery Trip":
		return _derive_eta(stop)

	return {"estimated_delivery_date": None, "source": "unavailable"}


def _derive_eta(stop):
	"""Derive ETA from parent trip and transporter master data."""
	trip = frappe.db.get_value(
		"Delivery Trip",
		stop.parent,
		["trip_date", "transporter"],
		as_dict=True,
	)
	if not trip or not trip.trip_date:
		return {"estimated_delivery_date": None, "source": "unavailable"}

	# Get transporter's default transit days
	transit_days = frappe.db.get_value(
		"Transporter", trip.transporter, "default_transit_days"
	) or 1.0

	# Count total stops in the trip
	total_stops = frappe.db.count(
		"Delivery Stop",
		{"parent": stop.parent, "parenttype": "Delivery Trip"},
	)

	if total_stops < 1:
		return {"estimated_delivery_date": None, "source": "unavailable"}

	# Prorate: later stops get a larger fraction of transit_days
	fraction = stop.sequence_no / total_stops
	days_to_add = math.ceil(transit_days * fraction)

	eta = add_days(trip.trip_date, days_to_add)
	return {"estimated_delivery_date": str(eta), "source": "derived"}


# ─────────────────────────────────────────────
# Phase 3 — Guest-facing order tracking API
# ─────────────────────────────────────────────


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=30, seconds=60)
def track_order(tracking_id):
	"""Public endpoint for customers to track an order by its tracking ID.

	Args:
		tracking_id: The 12-character tracking ID (TRK-XXXXXXXX)

	Returns:
		dict with status, current_location, estimated_delivery_date, timeline

	Security:
	- Exact match only (no wildcard / partial search)
	- Only returns whitelisted fields (no PII)
	- Rate-limited per IP
	- Failed lookups are logged for abuse detection
	"""
	tracking_id = (tracking_id or "").strip().upper()

	if not tracking_id:
		frappe.throw(_("Please enter a tracking ID"))

	# Exact-match lookup only — no partial / LIKE search
	stop = frappe.db.get_value(
		"Delivery Stop",
		{"tracking_id": tracking_id},
		["name", "status", "current_location_label", "estimated_delivery_date"],
		as_dict=True,
	)
	if not stop:
		# Log failed lookup (tracking_id only — no PII)
		frappe.log_error(
			title=_("Order Tracking — Invalid Tracking ID"),
			message=_("A lookup was attempted for non-existent tracking ID: {0}").format(
				tracking_id
			),
		)
		frappe.throw(
			_("No order found for this tracking ID. Please check and try again."),
			frappe.DoesNotExistError,
		)

	# Fetch timeline from Delivery Status Log
	timeline = frappe.get_all(
		"Delivery Status Log",
		filters={"parent": stop.name},
		fields=["status", "location_label", "timestamp", "remarks"],
		order_by="timestamp desc",
	)

	# Get estimated delivery (may be manual or derived)
	eta = get_estimated_delivery(stop.name)

	return {
		"tracking_id": tracking_id,
		"status": stop.status,
		"current_location": stop.current_location_label,
		"estimated_delivery_date": eta.get("estimated_delivery_date"),
		"eta_source": eta.get("source"),
		"timeline": timeline,
	}
