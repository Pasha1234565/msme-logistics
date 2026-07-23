from __future__ import unicode_literals

import frappe
from frappe.utils import today, add_days, now_datetime

from msme_logistics.logistics.doctype.delivery_stop.delivery_stop import DeliveryStop

# ── Constants ──────────────────────────────────────────────────────────────
DEMO_TRANSPORTERS = [
	"FastTrack Logistics",
	"CityExpress Couriers",
	"SafeHands Transport",
	"RapidMove Services",
]

DEMO_CUSTOMERS = [
	"Raj Electronics", "Priya Traders", "Delhi Mart", "NewGen Electronics",
	"Goyal Stationers", "TechHub Solutions", "GreenLeaf Organics", "QuickFix Services",
	"Metro Supplies", "Crystal Clear Waters", "FreshFarms Produce", "SmartOffice Solutions",
	"Bharat Industrials", "Coastal Exports", "WestEnd Retail", "NewAge Retail",
]


def execute():
	"""⚠️  DELETES all existing demo data, then re-creates it fresh.

	Safe to run repeatedly — previous demo Transporters, Customers, Delivery
	Trips, Stops, and Trip Cost Reconciliations are wiped first.
	"""
	step = 0
	total = 7
	try:
		_print_banner()
		now = now_datetime()
		today_date = today()

		# ── 1. Cleanup ──────────────────────────────────────────────────────
		step += 1
		_cleanup_all_demo_data()
		print(f"  ✅ [{step}/{total}] Cleanup complete")

		# ── 2. Customer Group & Territory ──────────────────────────────────
		step += 1
		customer_group = frappe.db.get_value("Customer Group", {"is_group": 0}, "name") or frappe.db.get_value(
			"Customer Group", {}, "name"
		)
		territory = frappe.db.get_value("Territory", {"is_group": 0}, "name") or frappe.db.get_value(
			"Territory", {}, "name"
		)
		if not customer_group or not territory:
			frappe.throw("No Customer Group / Territory found. Complete basic ERPNext Selling setup first.")
		print(f"  ✅ [{step}/{total}] Defaults ready")

		# ── 3. Transporters ─────────────────────────────────────────────────
		step += 1
		_create_transporters(now)
		print(f"  ✅ [{step}/{total}] Transporters created")

		# ── 4. Customers ────────────────────────────────────────────────────
		step += 1
		_create_customers(customer_group, territory, now)
		print(f"  ✅ [{step}/{total}] Customers created")

		# ── 5. Warehouse ────────────────────────────────────────────────────
		step += 1
		warehouse = frappe.db.get_value("Warehouse", {"is_group": 0, "disabled": 0}, "name")
		if not warehouse:
			frappe.throw("No usable Warehouse found. Complete basic ERPNext setup (Company + Warehouse) first.")
		print(f"  ✅ [{step}/{total}] Warehouse: {warehouse}")

		# ── 6. Delivery Trips with Stops ────────────────────────────────────
		step += 1
		trip_count = _create_delivery_trips(warehouse, now, today_date)
		print(f"  ✅ [{step}/{total}] {trip_count} Delivery Trips with tracking IDs created")

		# ── 7. Trip Cost Reconciliation ─────────────────────────────────────
		step += 1
		tcr_count = _create_trip_cost_reconciliations()
		print(f"  ✅ [{step}/{total}] {tcr_count} Trip Cost Reconciliations created")

		frappe.db.commit()
		_print_success()

	except Exception as e:
		frappe.db.rollback()
		print(f"\n❌ Demo data insertion FAILED at step {step}/{total}: {e}")
		print("   Transaction rolled back. Fix the issue and re-run.")


# ═══════════════════════════════════════════════════════════════════════════
#  CLEANUP
# ═══════════════════════════════════════════════════════════════════════════

def _cleanup_all_demo_data():
	"""Remove all demo data records so we can start fresh."""
	deleted = {"Transporters": 0, "Customers": 0, "Trips": 0, "Stops": 0, "TCRs": 0}

	# Stop child tables (must delete before parent trips)
	for name in frappe.db.sql_list("SELECT name FROM `tabDelivery Trip` WHERE name LIKE 'DT-DEMO-%%'"):
		stop_count = frappe.db.sql("DELETE FROM `tabDelivery Stop` WHERE parent = %s", name)
		deleted["Stops"] += stop_count or 0
		deleted["Trips"] += 1
		frappe.db.sql("DELETE FROM `tabDelivery Trip` WHERE name = %s", name)

	# Trip Cost Reconciliations
	deleted["TCRs"] = frappe.db.sql(
		"DELETE FROM `tabTrip Cost Reconciliation` WHERE name LIKE 'TCR-DEMO-%%'"
	) or 0

	# Customers
	for c in DEMO_CUSTOMERS:
		if frappe.db.exists("Customer", c):
			frappe.db.sql("DELETE FROM `tabCustomer` WHERE name = %s", c)
			deleted["Customers"] += 1

	# Transporters (including child table rows)
	for t in DEMO_TRANSPORTERS:
		if frappe.db.exists("Transporter", t):
			frappe.db.sql("DELETE FROM `tabTransporter Vehicle Type` WHERE parent = %s", t)
			frappe.db.sql("DELETE FROM `tabTransporter Service Area` WHERE parent = %s", t)
			frappe.db.sql("DELETE FROM `tabTransporter` WHERE name = %s", t)
			deleted["Transporters"] += 1

	frappe.db.commit()

	summary = ", ".join(f"{k}={v}" for k, v in deleted.items() if v > 0)
	print(f"  🗑️  Deleted: {summary}" if summary else "  ℹ️  No old demo data to delete")


# ═══════════════════════════════════════════════════════════════════════════
#  TRANSPORTERS
# ═══════════════════════════════════════════════════════════════════════════

def _create_transporters(now):
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

	for d in data:
		frappe.db.sql("""
			INSERT INTO `tabTransporter`
				(name, transporter_name, status, email, phone,
				 creation, modified, modified_by, owner, docstatus, idx)
			VALUES
				(%s, %s, %s, %s, %s,
				 %s, %s, 'Administrator', 'Administrator', 0, 0)
		""", (d["transporter_name"], d["transporter_name"], d["status"], d["email"], d["phone"], now, now))

		for idx, (vt, cap, rate) in enumerate(d["vehicle_types"], 1):
			frappe.db.sql("""
				INSERT INTO `tabTransporter Vehicle Type`
					(name, parent, parenttype, parentfield, idx,
					 vehicle_type, capacity_kg, rate_per_km,
					 creation, modified, modified_by, owner, docstatus)
				VALUES (%s, %s, 'Transporter', 'vehicle_types', %s,
					%s, %s, %s, %s, %s, 'Administrator', 'Administrator', 0)
			""", (frappe.generate_hash("", 10), d["transporter_name"], idx, vt, cap, rate, now, now))

		for idx, (frm, to) in enumerate(d["service_areas"], 1):
			frappe.db.sql("""
				INSERT INTO `tabTransporter Service Area`
					(name, parent, parenttype, parentfield, idx,
					 pincode_from, pincode_to,
					 creation, modified, modified_by, owner, docstatus)
				VALUES (%s, %s, 'Transporter', 'service_areas', %s,
					%s, %s, %s, %s, 'Administrator', 'Administrator', 0)
			""", (frappe.generate_hash("", 10), d["transporter_name"], idx, frm, to, now, now))

		print(f"  ✅ Transporter: {d['transporter_name']}")

	frappe.db.commit()


# ═══════════════════════════════════════════════════════════════════════════
#  CUSTOMERS
# ═══════════════════════════════════════════════════════════════════════════

def _create_customers(customer_group, territory, now):
	for c in DEMO_CUSTOMERS:
		frappe.db.sql("""
			INSERT INTO `tabCustomer`
				(name, customer_name, customer_type, customer_group, territory,
				 creation, modified, modified_by, owner, docstatus, idx)
			VALUES
				(%s, %s, 'Company', %s, %s,
				 %s, %s, 'Administrator', 'Administrator', 0, 0)
		""", (c, c, customer_group, territory, now, now))
		print(f"  ✅ Customer: {c}")

	frappe.db.commit()


# ═══════════════════════════════════════════════════════════════════════════
#  DELIVERY TRIPS + STOPS
# ═══════════════════════════════════════════════════════════════════════════

def _create_delivery_trips(warehouse, now, today_date):
	ft = "FastTrack Logistics"
	ce = "CityExpress Couriers"
	sh = "SafeHands Transport"
	rm = "RapidMove Services"

	def arrival(days_ago, hour, minute):
		return add_days(now, -days_ago).replace(hour=hour, minute=minute, second=0, microsecond=0)

	def day(days_ago):
		return add_days(today_date, -days_ago)

	trips_config = [
		{
			"name": "DT-DEMO-0001", "transporter": ft, "driver": "Rajesh Kumar",
			"vehicle": "DL-01-AB-1234", "distance": 42.5, "days_ago": 5,
			"status": "Completed",
			"stops": [
				(1, "Raj Electronics",      "12, MG Road, Delhi - 110001",       "09:00:00", "11:00:00", "Delivered", arrival(5, 9, 15)),
				(2, "Priya Traders",        "45, Lajpat Nagar, Delhi - 110024",  "11:00:00", "12:00:00", "Delivered", arrival(5, 11, 45)),
				(3, "Delhi Mart",           "78, Connaught Place, Delhi - 110001","13:00:00", "14:00:00", "Delivered", arrival(5, 14, 30)),
			],
		},
		{
			"name": "DT-DEMO-0002", "transporter": ft, "driver": "Rajesh Kumar",
			"vehicle": "DL-01-AB-1234", "distance": 28.0, "days_ago": 3,
			"status": "Completed",
			"stops": [
				(1, "NewGen Electronics",  "101, Sector 18, Noida - 201301",  "09:30:00", "10:30:00", "Delivered", arrival(3, 10, 0)),
				(2, "Goyal Stationers",    "55, Sector 12, Noida - 201301",   "11:00:00", "12:00:00", "Delivered", arrival(3, 11, 30)),
			],
		},
		{
			"name": "DT-DEMO-0003", "transporter": ft, "driver": "Suresh Singh",
			"vehicle": "DL-01-CD-5678", "distance": 35.2, "days_ago": 1,
			"status": "In Transit",
			"stops": [
				(1, "TechHub Solutions",  "202, Cyber City, Gurgaon - 122002","08:00:00", "10:00:00", "Delivered", arrival(1, 9, 30)),
				(2, "GreenLeaf Organics", "88, MG Road, Gurgaon - 122001",   "10:30:00", "12:00:00", "Delivered", arrival(1, 13, 15)),
				(3, "QuickFix Services",  "15, Industrial Area, Delhi - 110020","14:00:00","16:00:00", "Pending",   None),
			],
		},
		{
			"name": "DT-DEMO-0004", "transporter": ce, "driver": "Amit Sharma",
			"vehicle": "UP-14-EF-9012", "distance": 19.5, "days_ago": 4,
			"status": "Completed",
			"stops": [
				(1, "Metro Supplies",      "67, Karol Bagh, Delhi - 110005",  "10:00:00", "11:30:00", "Delivered", arrival(4, 10, 45)),
				(2, "Crystal Clear Waters","34, Patel Nagar, Delhi - 110008", "12:00:00", "13:00:00", "Failed",    None),
			],
		},
		{
			"name": "DT-DEMO-0005", "transporter": ce, "driver": "Vikram Yadav",
			"vehicle": "UP-14-GH-3456", "distance": 22.1, "days_ago": 2,
			"status": "Completed",
			"stops": [
				(1, "FreshFarms Produce",  "22, Model Town, Delhi - 110009",  "09:00:00", "10:00:00", "Delivered", arrival(2, 9, 30)),
				(2, "SmartOffice Solutions","11, Rajendra Place, Delhi - 110008","10:30:00","12:00:00","Delivered", arrival(2, 11, 15)),
			],
		},
		{
			"name": "DT-DEMO-0006", "transporter": ce, "driver": "Amit Sharma",
			"vehicle": "UP-14-EF-9012", "distance": 12.0, "days_ago": 0,
			"status": "Planned",
			"stops": [
				(1, "NewAge Retail", "5, Sector 62, Noida - 201309", "10:00:00","12:00:00","Pending", None),
			],
		},
		{
			"name": "DT-DEMO-0007", "transporter": sh, "driver": "Mohan Lal",
			"vehicle": "HR-26-XY-7890", "distance": 51.0, "days_ago": 6,
			"status": "Completed",
			"stops": [
				(1, "Bharat Industrials", "88, MIDC, Andheri, Mumbai - 400093","08:00:00","09:00:00","Delivered", arrival(6, 9, 45)),
				(2, "Coastal Exports",    "12, Fort Area, Mumbai - 400001",   "10:00:00","11:00:00","Delivered", arrival(6, 12, 10)),
				(3, "WestEnd Retail",     "45, Linking Road, Mumbai - 400054","12:00:00","13:00:00","Delivered", arrival(6, 14, 0)),
			],
		},
		{
			"name": "DT-DEMO-0008", "transporter": sh, "driver": "Mohan Lal",
			"vehicle": "HR-26-XY-7890", "distance": 33.4, "days_ago": 8,
			"status": "Reconciled",
			"stops": [
				(1, "Bharat Industrials", "88, MIDC, Andheri, Mumbai - 400093","08:00:00","09:00:00","Delivered", arrival(8, 8, 40)),
				(2, "Coastal Exports",    "12, Fort Area, Mumbai - 400001",   "10:00:00","11:00:00","Delivered", arrival(8, 10, 50)),
			],
		},
		{
			"name": "DT-DEMO-0009", "transporter": rm, "driver": "Naresh Gupta",
			"vehicle": "MH-04-KL-2468", "distance": 15.0, "days_ago": 1,
			"status": "Dispatched",
			"stops": [
				(1, "Crystal Clear Waters", "34, Patel Nagar, Delhi - 110008", "09:00:00","11:00:00","Pending", None),
			],
		},
	]

	for t in trips_config:
		frappe.db.sql("""
			INSERT INTO `tabDelivery Trip`
				(name, naming_series, transporter, driver_name, vehicle_no,
				 origin_warehouse, total_distance_km,
				 trip_status, trip_date, planned_dispatch_date,
				 actual_dispatch_time, completed_time, docstatus,
				 creation, modified, modified_by, owner, idx)
			VALUES
				(%s, 'DT-DEMO-', %s, %s, %s,
				 %s, %s,
				 %s, %s, %s,
				 %s, %s, 1,
				 %s, %s, 'Administrator', 'Administrator', 0)
		""", (
			t["name"], t["transporter"], t["driver"], t["vehicle"],
			warehouse, t["distance"],
			t["status"], day(t["days_ago"]), day(t["days_ago"]),
			arrival(t["days_ago"], 8, 0) if t["status"] != "Planned" else None,
			arrival(t["days_ago"], 16, 0) if t["status"] == "Completed" else None,
			now, now,
		))

		for seq, cust, addr, ws, we, stop_status, arrival_time in t["stops"]:
			tracking_id = DeliveryStop.generate_tracking_id()
			frappe.db.sql("""
				INSERT INTO `tabDelivery Stop`
					(name, parent, parenttype, parentfield, idx,
					 sequence_no, customer, address,
					 delivery_window_start, delivery_window_end,
					 status, actual_arrival_time,
					 tracking_id,
					 creation, modified, modified_by, owner, docstatus)
				VALUES
					(%s, %s, 'Delivery Trip', 'delivery_stops', %s,
					 %s, %s, %s, %s, %s,
					 %s, %s,
					 %s,
					 %s, %s, 'Administrator', 'Administrator', 0)
			""", (
				frappe.generate_hash("", 10), t["name"], seq,
				seq, cust, addr, ws, we,
				stop_status, arrival_time,
				tracking_id,
				now, now,
			))

		frappe.db.commit()
		print(f"  ✅ Trip: {t['name']} ({t['transporter']}, {t['status']})")

	return len(trips_config)


# ═══════════════════════════════════════════════════════════════════════════
#  TRIP COST RECONCILIATION
# ═══════════════════════════════════════════════════════════════════════════

def _create_trip_cost_reconciliations():
	completed = frappe.db.sql(
		"SELECT name, transporter, trip_status FROM `tabDelivery Trip` "
		"WHERE name LIKE 'DT-DEMO-%%' AND trip_status IN ('Completed', 'Reconciled')",
		as_dict=True,
	)

	if not completed:
		print("  ℹ️  No completed/reconciled demo trips — skipping TCR creation")
		return 0

	cost_map = {"FastTrack Logistics": (1500, 3000), "SafeHands Transport": (2200, 4800)}
	count = 0

	for trip in completed:
		fuel, payout = cost_map.get(trip.transporter, (1200, 2500))
		total_stops = frappe.db.count("Delivery Stop", {"parenttype": "Delivery Trip", "parent": trip.name})
		cost_per_stop = round((fuel + payout) / total_stops, 2) if total_stops else 0

		name = f"TCR-DEMO-{count + 1:04d}"
		frappe.db.sql("""
			INSERT INTO `tabTrip Cost Reconciliation`
				(name, naming_series, delivery_trip, reconciliation_date,
				 fuel_cost, transporter_payout, total_stops, cost_per_stop,
				 creation, modified, modified_by, owner, docstatus, idx)
			VALUES
				(%s, 'TCR-DEMO-', %s, %s,
				 %s, %s, %s, %s,
				 %s, %s, 'Administrator', 'Administrator', 0, 0)
		""", (name, trip.name, today(), fuel, payout, total_stops, cost_per_stop, now_datetime(), now_datetime()))
		count += 1

	frappe.db.commit()
	print(f"  ✅ Created {count} Trip Cost Reconciliation record(s)")
	return count


# ═══════════════════════════════════════════════════════════════════════════
#  UI HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _print_banner():
	print()
	print("=" * 60)
	print("  MSME LOGISTICS — DEMO DATA INSERTION")
	print("=" * 60)
	print("  This will DELETE all existing demo data and re-create it.")
	print()


def _print_success():
	print()
	print("=" * 60)
	print("████████████████████████████████████████████████████████████████")
	print("██                                                          ██")
	print("██           ✅  DEMO DATA INSERTED SUCCESSFULLY            ██")
	print("██                                                          ██")
	print("████████████████████████████████████████████████████████████████")
	print("=" * 60)
	print()
	print("  What was created:")
	print("    • 4 Transporters with vehicle types & service areas")
	print("    • 16 Customers")
	print("    • 9 Delivery Trips with tracking IDs on each stop")
	print("    • Trip Cost Reconciliation records")
	print()
	print("  Next steps:")
	print("    1. Refresh the MSME workspace")
	print("    2. Check SLA Compliance by Transporter chart")
	print("    3. Check Cost Per Delivery by Transporter chart")
	print("    4. Visit /track?id=<tracking_id> for customer tracking")
	print()
	print("=" * 60)
