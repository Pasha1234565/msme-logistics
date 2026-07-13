from __future__ import unicode_literals

import frappe
from frappe import _


@frappe.whitelist()
def optimize_route(trip_name):
	"""Call external routing API (Google Directions / OSRM) to optimize delivery stop sequence.

	Args:
		trip_name: Name of the Delivery Trip to optimize

	Returns:
		dict with status and updated sequence info, or error message

	Note:
		This is a stub. Actual implementation requires an external routing API.
		- For Google Directions API: https://developers.google.com/maps/documentation/directions
		- For OSRM (self-hosted): https://project-osrm.org/

		The external API should:
		1. Accept the origin warehouse address + all delivery stop addresses
		2. Return optimized waypoint order
		3. Update sequence_no on each Delivery Stop
	"""
	trip = frappe.get_doc("Delivery Trip", trip_name)

	if not trip.get("delivery_stops"):
		frappe.throw(_("No delivery stops found for trip {0}").format(trip_name))

	if len(trip.delivery_stops) < 3:
		frappe.msgprint(
			_("Trip {0} has fewer than 3 stops. Route optimization skipped.").format(trip_name)
		)
		return {"status": "skipped", "reason": "Too few stops"}

	# Get origin warehouse address
	origin_address = frappe.db.get_value(
		"Warehouse", trip.origin_warehouse, "address_line_1"
	) or frappe.db.get_value("Warehouse", trip.origin_warehouse, "warehouse_name")

	# Collect stop addresses
	stops = []
	for stop in trip.delivery_stops:
		customer_address = stop.address
		if not customer_address:
			# Fallback to Customer's primary address
			customer_address = frappe.db.get_value(
				"Dynamic Link",
				{"link_doctype": "Customer", "link_name": stop.customer, "parenttype": "Address"},
				"parent",
			)
		stops.append({
			"name": stop.name,
			"idx": stop.idx or stop.sequence_no,
			"customer": stop.customer,
			"address": customer_address,
		})

	# --- EXTERNAL API CALL STUB ---
	# Replace this block with actual API call:
	#
	# import requests
	# api_key = frappe.conf.get("google_maps_api_key")
	# waypoints = [s["address"] for s in stops]
	# url = "https://maps.googleapis.com/maps/api/directions/json"
	# params = {
	#     "origin": origin_address,
	#     "destination": stops[-1]["address"],  # Last stop as final destination
	#     "waypoints": "optimize:true|" + "|".join(waypoints[:-1]),
	#     "key": api_key,
	# }
	# response = requests.get(url, params=params).json()
	# if response["status"] == "OK":
	#     optimized_order = response["routes"][0]["waypoint_order"]
	#     for new_seq, old_idx in enumerate(optimized_order, 1):
	#         stop_name = stops[old_idx]["name"]
	#         frappe.db.set_value("Delivery Stop", stop_name, "sequence_no", new_seq)
	#     frappe.db.commit()
	#     return {"status": "success", "optimized_order": optimized_order}
	# else:
	#     return {"status": "error", "message": response["status"]}
	# --- END STUB ---

	frappe.msgprint(
		_("Route optimization for {0} requires an external routing API integration. "
		  "See the api.py stub for integration instructions.").format(trip_name)
	)

	return {
		"status": "stub",
		"message": "External routing API not configured. Update api.py to integrate Google Directions or OSRM.",
		"origin": origin_address,
		"stops_count": len(stops),
	}
