from __future__ import unicode_literals

import frappe
from frappe.utils import add_days, now_datetime, nowdate

from msme_logistics.logistics.doctype.delivery_stop.delivery_stop import DeliveryStop

# Existence of this Transporter is used as the "already seeded" marker,
# so the script is safe to re-run without creating duplicates.
DEMO_MARKER_TRANSPORTER = "FastTrack Logistics"


def execute():
	"""Insert demo data for the msme_logistics app.

	Creates Transporters, Customers, and Delivery Trips (with Delivery Stops)
	spread across the last ~10 days with a realistic mix of on-time, late,
	failed, and pending deliveries -- so the "SLA Compliance by Transporter"
	report/chart on the MSME workspace has real bars instead of "No Data".
	Also creates Trip Cost Reconciliation records so the "Cost Per Delivery
	by Transporter" chart and the "Avg Cost Per Stop" number card populate.

	Run via bench (do NOT pipe into bench console):

		bench --site <your-site-name> execute msme_logistics.patches.insert_demo_data.execute
	"""
	frappe.set_user("Administrator")

	# Only skip if BOTH the marker Transporter AND the Customers exist.
	# The old scripts created Transporters via raw SQL but never created
	# Customers, so checking only the Transporter would incorrectly skip
	# the new script's fuller data set.
	if frappe.db.exists("Transporter", DEMO_MARKER_TRANSPORTER) and frappe.db.exists("Customer", "Raj Electronics"):
		print(f"Demo data already present (Transporter '{DEMO_MARKER_TRANSPORTER}' and Customers exist). Skipping.")
		return

	warehouse = _get_warehouse()
	customer_group, territory = _get_customer_defaults()

	transporters = _create_transporters()
	customers = _create_customers(customer_group, territory)
	trips = _create_delivery_trips(transporters, customers, warehouse)
	_create_trip_cost_reconciliations(trips)

	frappe.db.commit()
	print("\n✅ Demo data created successfully.")
	print("   Refresh the MSME workspace to see the SLA Compliance chart populate.")


def _get_warehouse():
	warehouse = frappe.db.get_value("Warehouse", {"is_group": 0, "disabled": 0}, "name")
	if not warehouse:
		frappe.throw(
			"No usable Warehouse found. Please finish basic ERPNext setup "
			"(Company + at least one Warehouse) before running this script."
		)
	return warehouse


def _get_customer_defaults():
	customer_group = frappe.db.get_value("Customer Group", {"is_group": 0}, "name") or frappe.db.get_value(
		"Customer Group", {}, "name"
	)
	territory = frappe.db.get_value("Territory", {"is_group": 0}, "name") or frappe.db.get_value(
		"Territory", {}, "name"
	)
	if not customer_group or not territory:
		frappe.throw(
			"No Customer Group / Territory found. Please complete basic ERPNext "
			"setup (Selling module) before running this script."
		)
	return customer_group, territory


def _create_transporters():
	data = [
		{
			"transporter_name": "FastTrack Logistics",
			"status": "Active",
			"email": "info@fasttrack.in",
			"phone": "+91-9876543210",
			"vehicle_types": [("Tata Ace", 750, 12.0), ("Ashok Leyland", 2000, 18.5)],
			"service_areas": [("110001", "110099"), ("201301", "201310")],
		},
		{
			"transporter_name": "CityExpress Couriers",
			"status": "Active",
			"email": "dispatch@cityexpress.com",
			"phone": "+91-9876543211",
			"vehicle_types": [("Pickup Van", 500, 10.0)],
			"service_areas": [("110001", "110050")],
		},
		{
			"transporter_name": "SafeHands Transport",
			"status": "Active",
			"email": "ops@safehands.in",
			"phone": "+91-9876543212",
			"vehicle_types": [("Truck 6-Tyre", 5000, 25.0)],
			"service_areas": [("400001", "400099")],
		},
		{
			"transporter_name": "RapidMove Services",
			"status": "Inactive",
			"email": "contact@rapidmove.com",
			"phone": "+91-9876543213",
			"vehicle_types": [],
			"service_areas": [],
		},
	]

	names = []
	for t in data:
		if frappe.db.exists("Transporter", t["transporter_name"]):
			names.append(t["transporter_name"])
			continue

		doc = frappe.new_doc("Transporter")
		doc.transporter_name = t["transporter_name"]
		doc.status = t["status"]
		doc.email = t["email"]
		doc.phone = t["phone"]
		for vt, cap, rate in t["vehicle_types"]:
			doc.append("vehicle_types", {"vehicle_type": vt, "capacity_kg": cap, "rate_per_km": rate})
		for frm, to in t["service_areas"]:
			doc.append("service_areas", {"pincode_from": frm, "pincode_to": to})
		doc.flags.ignore_permissions = True
		doc.insert()
		names.append(doc.name)
		print(f"Created Transporter: {doc.name}")

	return names


def _create_customers(customer_group, territory):
	names = [
		"Raj Electronics", "Priya Traders", "Delhi Mart", "NewGen Electronics",
		"Goyal Stationers", "TechHub Solutions", "GreenLeaf Organics", "QuickFix Services",
		"Metro Supplies", "Crystal Clear Waters", "FreshFarms Produce", "SmartOffice Solutions",
		"Bharat Industrials", "Coastal Exports", "WestEnd Retail", "NewAge Retail",
	]
	for n in names:
		if frappe.db.exists("Customer", n):
			continue
		doc = frappe.new_doc("Customer")
		doc.customer_name = n
		doc.customer_type = "Company"
		doc.customer_group = customer_group
		doc.territory = territory
		doc.flags.ignore_permissions = True
		doc.insert()
	return names


def _create_delivery_trips(transporters, customers, warehouse):
	ft, ce, sh, rm = transporters[0], transporters[1], transporters[2], transporters[3]

	def arrival(days_ago, hour, minute):
		return add_days(now_datetime(), -days_ago).replace(hour=hour, minute=minute, second=0, microsecond=0)

	def day(days_ago):
		return add_days(nowdate(), -days_ago)

	# Each trip dict:
	#   transporter, driver, vehicle, total_distance_km, days_ago (trip/dispatch date),
	#   target_status (final trip_status shown to the user),
	#   stops: (seq, customer, address, window_start, window_end, status, actual_arrival_datetime_or_None)
	#
	# NOTE: Stops are built using `frappe.get_doc()` with child rows inline in
	# the dict (NOT doc.append()). This matches the pattern used by the
	# order_tracking_test.py which reliably generates tracking IDs via the
	# DeliveryStop.before_insert hook.
	trip_configs = [
		{
			"transporter": ft, "driver": "Rajesh Kumar", "vehicle": "DL-01-AB-1234",
			"total_distance_km": 42.5, "days_ago": 5, "target_status": "Completed",
			"stops": [
				(1, customers[0], "12, MG Road, Delhi - 110001", "09:00:00", "11:00:00", "Delivered", arrival(5, 9, 15)),
				(2, customers[1], "45, Lajpat Nagar, Delhi - 110024", "11:00:00", "12:00:00", "Delivered", arrival(5, 11, 45)),
				(3, customers[2], "78, Connaught Place, Delhi - 110001", "13:00:00", "14:00:00", "Delivered", arrival(5, 15, 30)),
			],
		},
		{
			"transporter": ft, "driver": "Rajesh Kumar", "vehicle": "DL-01-AB-1234",
			"total_distance_km": 28.0, "days_ago": 3, "target_status": "Completed",
			"stops": [
				(1, customers[3], "101, Sector 18, Noida - 201301", "09:30:00", "10:30:00", "Delivered", arrival(3, 10, 0)),
				(2, customers[4], "55, Sector 12, Noida - 201301", "11:00:00", "12:00:00", "Delivered", arrival(3, 11, 30)),
			],
		},
		{
			"transporter": ft, "driver": "Suresh Singh", "vehicle": "DL-01-CD-5678",
			"total_distance_km": 35.2, "days_ago": 1, "target_status": "In Transit",
			"stops": [
				(1, customers[5], "202, Cyber City, Gurgaon - 122002", "08:00:00", "10:00:00", "Delivered", arrival(1, 9, 30)),
				(2, customers[6], "88, MG Road, Gurgaon - 122001", "10:30:00", "12:00:00", "Delivered", arrival(1, 11, 45)),
				(3, customers[7], "15, Industrial Area, Delhi - 110020", "14:00:00", "16:00:00", "Pending", None),
			],
		},
		{
			"transporter": ce, "driver": "Amit Sharma", "vehicle": "UP-14-EF-9012",
			"total_distance_km": 19.5, "days_ago": 4, "target_status": "Completed",
			"stops": [
				(1, customers[8], "67, Karol Bagh, Delhi - 110005", "10:00:00", "11:30:00", "Delivered", arrival(4, 13, 45)),
				(2, customers[9], "34, Patel Nagar, Delhi - 110008", "12:00:00", "13:00:00", "Failed", None),
			],
		},
		{
			"transporter": ce, "driver": "Vikram Yadav", "vehicle": "UP-14-GH-3456",
			"total_distance_km": 22.1, "days_ago": 2, "target_status": "Completed",
			"stops": [
				(1, customers[10], "22, Model Town, Delhi - 110009", "09:00:00", "10:00:00", "Delivered", arrival(2, 9, 30)),
				(2, customers[11], "11, Rajendra Place, Delhi - 110008", "10:30:00", "12:00:00", "Delivered", arrival(2, 11, 15)),
			],
		},
		{
			"transporter": ce, "driver": "Amit Sharma", "vehicle": "UP-14-EF-9012",
			"total_distance_km": 12.0, "days_ago": 0, "target_status": "Planned",
			"stops": [
				(1, customers[15], "5, Sector 62, Noida - 201309", "10:00:00", "12:00:00", "Pending", None),
			],
		},
		{
			"transporter": sh, "driver": "Mohan Lal", "vehicle": "HR-26-XY-7890",
			"total_distance_km": 51.0, "days_ago": 6, "target_status": "Completed",
			"stops": [
				(1, customers[12], "88, MIDC, Andheri, Mumbai - 400093", "08:00:00", "09:00:00", "Delivered", arrival(6, 9, 45)),
				(2, customers[13], "12, Fort Area, Mumbai - 400001", "10:00:00", "11:00:00", "Delivered", arrival(6, 12, 10)),
				(3, customers[14], "45, Linking Road, Mumbai - 400054", "12:00:00", "13:00:00", "Delivered", arrival(6, 14, 0)),
			],
		},
		{
			"transporter": sh, "driver": "Mohan Lal", "vehicle": "HR-26-XY-7890",
			"total_distance_km": 33.4, "days_ago": 8, "target_status": "Reconciled",
			"stops": [
				(1, customers[12], "88, MIDC, Andheri, Mumbai - 400093", "08:00:00", "09:00:00", "Delivered", arrival(8, 8, 40)),
				(2, customers[13], "12, Fort Area, Mumbai - 400001", "10:00:00", "11:00:00", "Delivered", arrival(8, 10, 50)),
			],
		},
		{
			"transporter": rm, "driver": "Naresh Gupta", "vehicle": "MH-04-KL-2468",
			"total_distance_km": 15.0, "days_ago": 1, "target_status": "Dispatched",
			"stops": [
				(1, customers[9], "34, Patel Nagar, Delhi - 110008", "09:00:00", "11:00:00", "Pending", None),
			],
		},
	]

	created = []
	for cfg in trip_configs:
		final_status = cfg["target_status"]

		# Build stops list with inline tracking IDs (belt + suspenders:
		# both the explicit tracking_id below AND the DeliveryStop.before_insert
		# hook will fire, so IDs are guaranteed).
		stops_data = []
		for seq, customer, address, ws, we, stop_status, arrival_dt in cfg["stops"]:
			stops_data.append({
				"sequence_no": seq,
				"customer": customer,
				"address": address,
				"delivery_window_start": ws,
				"delivery_window_end": we,
				"status": stop_status,
				"actual_arrival_time": arrival_dt,
				"tracking_id": DeliveryStop.generate_tracking_id(),
			})

		doc = frappe.get_doc({
			"doctype": "Delivery Trip",
			"transporter": cfg["transporter"],
			"driver_name": cfg["driver"],
			"vehicle_no": cfg["vehicle"],
			"origin_warehouse": warehouse,
			"total_distance_km": cfg["total_distance_km"],
			"trip_date": day(cfg["days_ago"]),
			"planned_dispatch_date": day(cfg["days_ago"]),
			"trip_status": "Planned",
			"delivery_stops": stops_data,
		})

		doc.flags.ignore_permissions = True
		doc.flags.ignore_links = True
		doc.insert()

		# ── Bypass doc.submit() — the active workflow blocks submission ──
		if final_status != "Planned":
			frappe.db.sql("""
				UPDATE `tabDelivery Trip`
				SET docstatus = 1,
					trip_status = %s,
					completed_time = %s
				WHERE name = %s
			""", (
				final_status,
				arrival(cfg["days_ago"], 16, 0) if final_status == "Completed" else None,
				doc.name,
			))
		else:
			frappe.db.sql("""
				UPDATE `tabDelivery Trip`
				SET trip_status = %s
				WHERE name = %s
			""", (final_status, doc.name))

		created.append(doc.name)
		print(f"Created Delivery Trip: {doc.name} ({cfg['transporter']}, {final_status})")

		# Commit after each trip so partial data survives errors on later trips.
		frappe.db.commit()

	return created


def _create_trip_cost_reconciliations(trip_names):
	cost_map = {
		"FastTrack Logistics": (1500, 3000),
		"SafeHands Transport": (2200, 4800),
	}
	count = 0
	for name in trip_names:
		trip = frappe.db.get_value("Delivery Trip", name, ["transporter", "trip_status"], as_dict=True)
		if trip.trip_status not in ("Completed", "Reconciled"):
			continue
		if frappe.db.exists("Trip Cost Reconciliation", {"delivery_trip": name}):
			continue

		fuel, payout = cost_map.get(trip.transporter, (1200, 2500))
		total_stops = frappe.db.count("Delivery Stop", {"parenttype": "Delivery Trip", "parent": name})
		cost_per_stop = round((fuel + payout) / total_stops, 2) if total_stops else 0

		doc = frappe.new_doc("Trip Cost Reconciliation")
		doc.delivery_trip = name
		doc.reconciliation_date = nowdate()
		doc.fuel_cost = fuel
		doc.transporter_payout = payout
		doc.total_stops = total_stops
		doc.cost_per_stop = cost_per_stop
		doc.flags.ignore_permissions = True
		doc.insert()
		count += 1

	print(f"Created {count} Trip Cost Reconciliation record(s)")
