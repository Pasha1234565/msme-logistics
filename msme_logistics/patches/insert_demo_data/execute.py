from __future__ import unicode_literals

import frappe
from frappe.utils import today, add_days, now_datetime


def execute():
	"""Insert comprehensive demo data for SLA Compliance & Cost Per Delivery charts."""
	now = now_datetime()
	today_date = today()

	# ── Skip if data already exists ──────────────────────────────────────
	if frappe.db.exists("Delivery Trip", "DT-DEMO-0001"):
		print("✅ Demo data already exists, skipping")
		return

	print("Inserting comprehensive demo data...")

	# ── 1. Transporters ──────────────────────────────────────────────────
	transporters = [
		("FastTrack Logistics", "Active",   "info@fasttrack.in",     "+91-9876543210"),
		("CityExpress Couriers", "Active",  "dispatch@cityexpress.com", "+91-9876543211"),
		("SafeHands Transport", "Active",   "ops@safehands.in",      "+91-9876543212"),
		("RapidMove Services", "Inactive",  "contact@rapidmove.com", "+91-9876543213"),
	]
	for name, status, email, phone in transporters:
		frappe.db.sql("""
			INSERT INTO `tabTransporter`
				(name, transporter_name, status, email, phone,
				 creation, modified, modified_by, owner, docstatus, idx)
			VALUES
				(%s, %s, %s, %s, %s, %s, %s, 'Administrator', 'Administrator', 0, 0)
		""", (name, name, status, email, phone, now, now))

		# Vehicle types
		vtypes = {
			"FastTrack Logistics": [("Tata Ace", 750, 12.00), ("Ashok Leyland", 2000, 18.50)],
			"CityExpress Couriers": [("Pickup Van", 500, 10.00)],
			"SafeHands Transport": [("Truck 6-Tyre", 5000, 25.00)],
		}
		for idx, (vt, cap, rate) in enumerate(vtypes.get(name, []), 1):
			frappe.db.sql("""
				INSERT INTO `tabTransporter Vehicle Type`
					(name, parent, parenttype, parentfield, idx,
					 vehicle_type, capacity_kg, rate_per_km,
					 creation, modified, modified_by, owner, docstatus)
				VALUES (%s, %s, 'Transporter', 'vehicle_types', %s,
					%s, %s, %s, %s, %s, 'Administrator', 'Administrator', 0)
			""", (frappe.generate_hash("", 10), name, idx, vt, cap, rate, now, now))

		# Service areas
		areas = {
			"FastTrack Logistics": [("110001", "110099"), ("201301", "201310")],
			"CityExpress Couriers": [("110001", "110050")],
			"SafeHands Transport": [("400001", "400099")],
		}
		for idx, (frm, to) in enumerate(areas.get(name, []), 1):
			frappe.db.sql("""
				INSERT INTO `tabTransporter Service Area`
					(name, parent, parenttype, parentfield, idx,
					 pincode_from, pincode_to,
					 creation, modified, modified_by, owner, docstatus)
				VALUES (%s, %s, 'Transporter', 'service_areas', %s,
					%s, %s, %s, %s, 'Administrator', 'Administrator', 0)
			""", (frappe.generate_hash("", 10), name, idx, frm, to, now, now))

	frappe.db.commit()
	print("  ✅ Created 4 Transporters with vehicle types & service areas")

	# ── 2. Warehouse ─────────────────────────────────────────────────────
	warehouse = frappe.db.get_value("Warehouse", {"is_group": 0, "disabled": 0}, "name")

	# ── 3. Delivery Trips with Stops ─────────────────────────────────────
	ft = "FastTrack Logistics"
	ce = "CityExpress Couriers"
	sh = "SafeHands Transport"

	# Helper to build arrival datetime
	def arrival(days_ago, hour, minute):
		return add_days(now, -days_ago).replace(hour=hour, minute=minute, second=0, microsecond=0)

	trips = [
		# FastTrack: 2 completed + 1 in-transit
		{
			"name": "DT-DEMO-0001", "transporter": ft, "driver": "Rajesh Kumar",
			"vehicle": "DL-01-AB-1234", "status": "Completed",
			"trip_date": add_days(today_date, -5), "dispatch": add_days(today_date, -5),
			"dispatch_time": arrival(5, 8, 0),
			"stops": [
				(1, "Raj Electronics",      "12, MG Road, Delhi - 110001",       "09:00:00", "11:00:00", "Delivered", arrival(5, 9, 15)),
				(2, "Priya Traders",        "45, Lajpat Nagar, Delhi - 110024",  "11:00:00", "12:00:00", "Delivered", arrival(5, 11, 45)),
				(3, "Delhi Mart",           "78, Connaught Place, Delhi - 110001","13:00:00", "14:00:00", "Delivered", arrival(5, 14, 30)),
			],
		},
		{
			"name": "DT-DEMO-0002", "transporter": ft, "driver": "Rajesh Kumar",
			"vehicle": "DL-01-AB-1234", "status": "Completed",
			"trip_date": add_days(today_date, -3), "dispatch": add_days(today_date, -3),
			"dispatch_time": arrival(3, 8, 0),
			"stops": [
				(1, "NewGen Electronics",  "101, Sector 18, Noida - 201301",  "09:30:00", "10:30:00", "Delivered", arrival(3, 10, 0)),
				(2, "Goyal Stationers",    "55, Sector 12, Noida - 201301",   "11:00:00", "12:00:00", "Delivered", arrival(3, 11, 30)),
			],
		},
		{
			"name": "DT-DEMO-0003", "transporter": ft, "driver": "Suresh Singh",
			"vehicle": "DL-01-CD-5678", "status": "In Transit",
			"trip_date": add_days(today_date, -1), "dispatch": add_days(today_date, -1),
			"dispatch_time": arrival(1, 7, 0),
			"stops": [
				(1, "TechHub Solutions",  "202, Cyber City, Gurgaon - 122002","08:00:00", "10:00:00", "Delivered", arrival(1, 9, 30)),
				(2, "GreenLeaf Organics", "88, MG Road, Gurgaon - 122001",   "10:30:00", "12:00:00", "Delivered", arrival(1, 13, 15)),
				(3, "QuickFix Services",  "15, Industrial Area, Delhi - 110020","14:00:00","16:00:00", "Pending",   None),
			],
		},
		# CityExpress: 2 completed
		{
			"name": "DT-DEMO-0004", "transporter": ce, "driver": "Amit Sharma",
			"vehicle": "UP-14-EF-9012", "status": "Completed",
			"trip_date": add_days(today_date, -4), "dispatch": add_days(today_date, -4),
			"dispatch_time": arrival(4, 9, 0),
			"stops": [
				(1, "Metro Supplies",      "67, Karol Bagh, Delhi - 110005",  "10:00:00", "11:30:00", "Delivered", arrival(4, 10, 45)),
				(2, "Crystal Clear Waters","34, Patel Nagar, Delhi - 110008", "12:00:00", "13:00:00", "Failed",    None),
			],
		},
		{
			"name": "DT-DEMO-0005", "transporter": ce, "driver": "Vikram Yadav",
			"vehicle": "UP-14-GH-3456", "status": "Completed",
			"trip_date": add_days(today_date, -2), "dispatch": add_days(today_date, -2),
			"dispatch_time": arrival(2, 8, 30),
			"stops": [
				(1, "FreshFarms Produce",  "22, Model Town, Delhi - 110009",  "09:00:00", "10:00:00", "Delivered", arrival(2, 9, 30)),
				(2, "SmartOffice Solutions","11, Rajendra Place, Delhi - 110008","10:30:00","12:00:00","Delivered", arrival(2, 11, 15)),
			],
		},
		# SafeHands: 1 completed (all late)
		{
			"name": "DT-DEMO-0006", "transporter": sh, "driver": "Mohan Lal",
			"vehicle": "HR-26-XY-7890", "status": "Completed",
			"trip_date": add_days(today_date, -6), "dispatch": add_days(today_date, -6),
			"dispatch_time": arrival(6, 6, 0),
			"stops": [
				(1, "Bharat Industrials", "88, MIDC, Andheri, Mumbai - 400093","08:00:00","09:00:00","Delivered", arrival(6, 9, 45)),
				(2, "Coastal Exports",    "12, Fort Area, Mumbai - 400001",   "10:00:00","11:00:00","Delivered", arrival(6, 12, 10)),
				(3, "WestEnd Retail",     "45, Linking Road, Mumbai - 400054","12:00:00","13:00:00","Delivered", arrival(6, 14, 0)),
			],
		},
		# Planned trip
		{
			"name": "DT-DEMO-0007", "transporter": ce, "driver": "Amit Sharma",
			"vehicle": "UP-14-EF-9012", "status": "Planned",
			"trip_date": today_date, "dispatch": today_date,
			"dispatch_time": None,
			"stops": [
				(1, "NewAge Retail", "5, Sector 62, Noida - 201309", "10:00:00","12:00:00","Pending", None),
			],
		},
	]

	for t in trips:
		frappe.db.sql("""
			INSERT INTO `tabDelivery Trip`
				(name, naming_series, transporter, driver_name, vehicle_no,
				 origin_warehouse, trip_status, trip_date, planned_dispatch_date,
				 actual_dispatch_time, docstatus,
				 creation, modified, modified_by, owner, idx)
			VALUES
				(%s, 'DT-DEMO-', %s, %s, %s,
				 %s, %s, %s, %s, %s, 1,
				 %s, %s, 'Administrator', 'Administrator', 0)
		""", (t["name"], t["transporter"], t["driver"], t["vehicle"],
			warehouse or "", t["status"], t["trip_date"], t["dispatch"],
			t["dispatch_time"], now, now))

		for seq, cust, addr, ws, we, status, arrival in t["stops"]:
			frappe.db.sql("""
				INSERT INTO `tabDelivery Stop`
					(name, parent, parenttype, parentfield, idx,
					 sequence_no, customer, address,
					 delivery_window_start, delivery_window_end,
					 status, actual_arrival_time,
					 creation, modified, modified_by, owner, docstatus)
				VALUES
					(%s, %s, 'Delivery Trip', 'delivery_stops', %s,
					 %s, %s, %s, %s, %s,
					 %s, %s,
					 %s, %s, 'Administrator', 'Administrator', 0)
			""", (frappe.generate_hash("", 10), t["name"], seq, seq, cust, addr,
				ws, we, status, arrival, now, now))

	frappe.db.commit()
	print("  ✅ Created 7 Delivery Trips with delivery stops")

	# ── 4. Trip Cost Reconciliation (for Cost Per Delivery chart) ──────
	completed = frappe.db.sql(
		"SELECT name, transporter FROM `tabDelivery Trip` WHERE trip_status = 'Completed'",
		as_dict=True,
	)
	cost_map = {"FastTrack Logistics": (1500, 3000), "SafeHands Transport": (2200, 4800)}
	for idx, trip in enumerate(completed, 1):
		fuel, payout = cost_map.get(trip.transporter, (1200, 2500))
		stops = frappe.db.count("Delivery Stop", {"parenttype": "Delivery Trip", "parent": trip.name})
		cps = round((fuel + payout) / stops, 2) if stops else 0
		frappe.db.sql("""
			INSERT INTO `tabTrip Cost Reconciliation`
				(name, naming_series, delivery_trip, reconciliation_date,
				 fuel_cost, transporter_payout, total_stops, cost_per_stop,
				 creation, modified, modified_by, owner, docstatus, idx)
			VALUES
				(%s, 'TCR-DEMO-', %s, %s,
				 %s, %s, %s, %s,
				 %s, %s, 'Administrator', 'Administrator', 0, 0)
		""", (f"TCR-DEMO-{idx:04d}", trip.name, today(), fuel, payout, stops, cps, now, now))

	frappe.db.commit()
	print(f"  ✅ Created {len(completed)} Trip Cost Reconciliation records")

	print("✅ Comprehensive demo data inserted successfully!")
	print("   Refresh the MSME workspace to see charts with data.")
