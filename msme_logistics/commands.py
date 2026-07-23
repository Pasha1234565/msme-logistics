from __future__ import unicode_literals

import frappe
from frappe.utils import today, add_days, add_years, now_datetime, get_datetime


def insert_demo_data():
	"""Insert comprehensive demo data using direct SQL.

	Creates transporters, delivery trips with stops, and cost reconciliation
	records that feed into the SLA Compliance and Cost Per Delivery charts.

	Run via bench console:
		import msme_logistics.commands
		msme_logistics.commands.insert_demo_data()
	"""
	# Check if demo data already exists
	existing = frappe.db.sql("SELECT name FROM `tabTransporter` LIMIT 1")
	if existing:
		print("✅ Demo data already exists, skipping")
		return

	print("Inserting comprehensive demo data...")
	_create_demo_transporters_sql()
	frappe.db.commit()

	_create_demo_trips_sql()
	frappe.db.commit()

	_create_demo_reconciliation_sql()
	frappe.db.commit()

	print("✅ Demo data inserted successfully!")
	print("   Refresh the MSME workspace to see charts with data.")


def _create_demo_transporters_sql():
	"""Insert demo transporters using raw SQL."""
	now = now_datetime()

	transporters = [
		{
			"name": "FastTrack Logistics",
			"transporter_name": "FastTrack Logistics",
			"status": "Active",
			"email": "info@fasttrack.in",
			"phone": "+91-9876543210",
		},
		{
			"name": "CityExpress Couriers",
			"transporter_name": "CityExpress Couriers",
			"status": "Active",
			"email": "dispatch@cityexpress.com",
			"phone": "+91-9876543211",
		},
		{
			"name": "SafeHands Transport",
			"transporter_name": "SafeHands Transport",
			"status": "Active",
			"email": "ops@safehands.in",
			"phone": "+91-9876543212",
		},
		{
			"name": "RapidMove Services",
			"transporter_name": "RapidMove Services",
			"status": "Inactive",
			"email": "contact@rapidmove.com",
			"phone": "+91-9876543213",
		},
	]

	for t in transporters:
		frappe.db.sql("""
			INSERT INTO `tabTransporter`
				(name, transporter_name, status, email, phone,
				 creation, modified, modified_by, owner, docstatus, idx)
			VALUES
				(%(name)s, %(transporter_name)s, %(status)s, %(email)s, %(phone)s,
				 %(now)s, %(now)s, 'Administrator', 'Administrator', 0, 0)
		""", {**t, "now": now})
		print(f"  ✅ Created Transporter: {t['name']}")

	frappe.db.commit()

	# Add vehicle types
	try:
		vehicles = [
			("FastTrack Logistics", "Tata Ace", 750, 12.00),
			("FastTrack Logistics", "Ashok Leyland", 2000, 18.50),
			("CityExpress Couriers", "Pickup Van", 500, 10.00),
			("SafeHands Transport", "Truck 6-Tyre", 5000, 25.00),
		]
		for idx, (transporter, vtype, cap, rate) in enumerate(vehicles, 1):
			frappe.db.sql("""
				INSERT INTO `tabTransporter Vehicle Type`
					(name, parent, parenttype, parentfield, idx,
					 vehicle_type, capacity_kg, rate_per_km,
					 creation, modified, modified_by, owner, docstatus)
				VALUES
					(%(name)s, %(parent)s, 'Transporter', 'vehicle_types', %(idx)s,
					 %(vtype)s, %(cap)s, %(rate)s,
					 %(now)s, %(now)s, 'Administrator', 'Administrator', 0)
			""", {
				"name": frappe.generate_hash("", 10),
				"parent": transporter,
				"idx": idx,
				"vtype": vtype,
				"cap": cap,
				"rate": rate,
				"now": now,
			})
		frappe.db.commit()
		print("  ✅ Added vehicle types")

		# Add service areas
		areas = [
			("FastTrack Logistics", "110001", "110099"),
			("FastTrack Logistics", "201301", "201310"),
			("CityExpress Couriers", "110001", "110050"),
			("SafeHands Transport", "400001", "400099"),
		]
		for idx, (transporter, frm, to) in enumerate(areas, 1):
			frappe.db.sql("""
				INSERT INTO `tabTransporter Service Area`
					(name, parent, parenttype, parentfield, idx,
					 pincode_from, pincode_to,
					 creation, modified, modified_by, owner, docstatus)
				VALUES
					(%(name)s, %(parent)s, 'Transporter', 'service_areas', %(idx)s,
					 %(frm)s, %(to)s,
					 %(now)s, %(now)s, 'Administrator', 'Administrator', 0)
			""", {
				"name": frappe.generate_hash("", 10),
				"parent": transporter,
				"idx": idx,
				"frm": frm,
				"to": to,
				"now": now,
			})
		frappe.db.commit()
		print("  ✅ Added service areas")
	except Exception as e:
		frappe.db.rollback()
		print(f"  ⚠️  Child table data skipped: {e}")


def _create_demo_trips_sql():
	"""Insert demo Delivery Trips with stops that exercise SLA scenarios.

	SLA = Yes: actual_arrival_time's time ≤ delivery_window_end
	SLA = No:  actual_arrival_time's time > delivery_window_end
	"""
	now = now_datetime()
	today_date = today()

	transporters = [r[0] for r in frappe.db.sql(
		"SELECT name FROM `tabTransporter` WHERE status = 'Active' ORDER BY name"
	)]

	if len(transporters) < 3:
		print("  ⚠️  Not enough transporters for demo data")
		return

	# Get a default warehouse
	warehouse = frappe.db.get_value("Warehouse", {"is_group": 0, "disabled": 0}, "name")
	if not warehouse:
		warehouse = frappe.db.get_value("Warehouse", {}, "name")

	ft = transporters[0]   # FastTrack Logistics
	ce = transporters[1]   # CityExpress Couriers
	sh = transporters[2]   # SafeHands Transport

	# -------------------------------------------------------------------------
	# Define trips — each entry is a dict with trip fields + a `stops` list
	# -------------------------------------------------------------------------
	trips_data = [
		# ---- FastTrack Logistics: 2 completed trips + 1 in-transit ----
		{
			"name": "DT-DEMO-0001",
			"transporter": ft,
			"driver": "Rajesh Kumar",
			"vehicle": "DL-01-AB-1234",
			"status": "Completed",
			"trip_date": add_days(today_date, -5),
			"dispatch_date": add_days(today_date, -5),
			"dispatch_time": add_days(now, -5).replace(hour=8, minute=0, second=0),
			"stops": [
				# Stop 1 — arrived at 09:15, window 09:00-11:00 → ON TIME  ✓
				{"seq": 1, "cust": "Raj Electronics", "addr": "12, MG Road, Delhi - 110001",
				 "win_start": "09:00:00", "win_end": "11:00:00",
				 "status": "Delivered", "arrival": add_days(now, -5).replace(hour=9, minute=15)},
				# Stop 2 — arrived at 11:45, window 11:00-12:00 → ON TIME  ✓
				{"seq": 2, "cust": "Priya Traders", "addr": "45, Lajpat Nagar, Delhi - 110024",
				 "win_start": "11:00:00", "win_end": "12:00:00",
				 "status": "Delivered", "arrival": add_days(now, -5).replace(hour=11, minute=45)},
				# Stop 3 — arrived at 14:30, window 13:00-14:00 → LATE  ✗
				{"seq": 3, "cust": "Delhi Mart", "addr": "78, Connaught Place, Delhi - 110001",
				 "win_start": "13:00:00", "win_end": "14:00:00",
				 "status": "Delivered", "arrival": add_days(now, -5).replace(hour=14, minute=30)},
			],
		},
		{
			"name": "DT-DEMO-0002",
			"transporter": ft,
			"driver": "Rajesh Kumar",
			"vehicle": "DL-01-AB-1234",
			"status": "Completed",
			"trip_date": add_days(today_date, -3),
			"dispatch_date": add_days(today_date, -3),
			"dispatch_time": add_days(now, -3).replace(hour=8, minute=0, second=0),
			"stops": [
				{"seq": 1, "cust": "NewGen Electronics", "addr": "101, Sector 18, Noida - 201301",
				 "win_start": "09:30:00", "win_end": "10:30:00",
				 "status": "Delivered", "arrival": add_days(now, -3).replace(hour=10, minute=00)},
				{"seq": 2, "cust": "Goyal Stationers", "addr": "55, Sector 12, Noida - 201301",
				 "win_start": "11:00:00", "win_end": "12:00:00",
				 "status": "Delivered", "arrival": add_days(now, -3).replace(hour=11, minute=30)},
			],
		},
		{
			"name": "DT-DEMO-0003",
			"transporter": ft,
			"driver": "Suresh Singh",
			"vehicle": "DL-01-CD-5678",
			"status": "In Transit",
			"trip_date": add_days(today_date, -1),
			"dispatch_date": add_days(today_date, -1),
			"dispatch_time": add_days(now, -1).replace(hour=7, minute=0, second=0),
			"stops": [
				{"seq": 1, "cust": "TechHub Solutions", "addr": "202, Cyber City, Gurgaon - 122002",
				 "win_start": "08:00:00", "win_end": "10:00:00",
				 "status": "Delivered", "arrival": add_days(now, -1).replace(hour=9, minute=30)},
				{"seq": 2, "cust": "GreenLeaf Organics", "addr": "88, MG Road, Gurgaon - 122001",
				 "win_start": "10:30:00", "win_end": "12:00:00",
				 "status": "Delivered", "arrival": add_days(now, -1).replace(hour=13, minute=15)},  # LATE
				{"seq": 3, "cust": "QuickFix Services", "addr": "15, Industrial Area, Delhi - 110020",
				 "win_start": "14:00:00", "win_end": "16:00:00",
				 "status": "Pending", "arrival": None},
			],
		},

		# ---- CityExpress Couriers: 2 completed trips ----
		{
			"name": "DT-DEMO-0004",
			"transporter": ce,
			"driver": "Amit Sharma",
			"vehicle": "UP-14-EF-9012",
			"status": "Completed",
			"trip_date": add_days(today_date, -4),
			"dispatch_date": add_days(today_date, -4),
			"dispatch_time": add_days(now, -4).replace(hour=9, minute=0, second=0),
			"stops": [
				{"seq": 1, "cust": "Metro Supplies", "addr": "67, Karol Bagh, Delhi - 110005",
				 "win_start": "10:00:00", "win_end": "11:30:00",
				 "status": "Delivered", "arrival": add_days(now, -4).replace(hour=10, minute=45)},
				{"seq": 2, "cust": "Crystal Clear Waters", "addr": "34, Patel Nagar, Delhi - 110008",
				 "win_start": "12:00:00", "win_end": "13:00:00",
				 "status": "Failed", "arrival": None},
			],
		},
		{
			"name": "DT-DEMO-0005",
			"transporter": ce,
			"driver": "Vikram Yadav",
			"vehicle": "UP-14-GH-3456",
			"status": "Completed",
			"trip_date": add_days(today_date, -2),
			"dispatch_date": add_days(today_date, -2),
			"dispatch_time": add_days(now, -2).replace(hour=8, minute=30, second=0),
			"stops": [
				{"seq": 1, "cust": "FreshFarms Produce", "addr": "22, Model Town, Delhi - 110009",
				 "win_start": "09:00:00", "win_end": "10:00:00",
				 "status": "Delivered", "arrival": add_days(now, -2).replace(hour=9, minute=30)},
				{"seq": 2, "cust": "SmartOffice Solutions", "addr": "11, Rajendra Place, Delhi - 110008",
				 "win_start": "10:30:00", "win_end": "12:00:00",
				 "status": "Delivered", "arrival": add_days(now, -2).replace(hour=11, minute=15)},
			],
		},

		# ---- SafeHands Transport: 1 completed trip (all late) ----
		{
			"name": "DT-DEMO-0006",
			"transporter": sh,
			"driver": "Mohan Lal",
			"vehicle": "HR-26-XY-7890",
			"status": "Completed",
			"trip_date": add_days(today_date, -6),
			"dispatch_date": add_days(today_date, -6),
			"dispatch_time": add_days(now, -6).replace(hour=6, minute=0, second=0),
			"stops": [
				{"seq": 1, "cust": "Bharat Industrials", "addr": "88, MIDC, Andheri, Mumbai - 400093",
				 "win_start": "08:00:00", "win_end": "09:00:00",
				 "status": "Delivered", "arrival": add_days(now, -6).replace(hour=9, minute=45)},  # LATE
				{"seq": 2, "cust": "Coastal Exports", "addr": "12, Fort Area, Mumbai - 400001",
				 "win_start": "10:00:00", "win_end": "11:00:00",
				 "status": "Delivered", "arrival": add_days(now, -6).replace(hour=12, minute=10)},  # LATE
				{"seq": 3, "cust": "WestEnd Retail", "addr": "45, Linking Road, Mumbai - 400054",
				 "win_start": "12:00:00", "win_end": "13:00:00",
				 "status": "Delivered", "arrival": add_days(now, -6).replace(hour=14, minute=0)},  # LATE
			],
		},

		# ---- Planned trip (no SLA data yet) ----
		{
			"name": "DT-DEMO-0007",
			"transporter": ce,
			"driver": "Amit Sharma",
			"vehicle": "UP-14-EF-9012",
			"status": "Planned",
			"trip_date": today_date,
			"dispatch_date": today_date,
			"dispatch_time": None,
			"stops": [
				{"seq": 1, "cust": "NewAge Retail", "addr": "5, Sector 62, Noida - 201309",
				 "win_start": "10:00:00", "win_end": "12:00:00",
				 "status": "Pending", "arrival": None},
			],
		},
	]

	# -------------------------------------------------------------------------
	# Insert trips
	# -------------------------------------------------------------------------
	for t in trips_data:
		dispatch_time = t.get("dispatch_time")
		frappe.db.sql("""
			INSERT INTO `tabDelivery Trip`
				(name, naming_series, transporter, driver_name, vehicle_no,
				 origin_warehouse, trip_status, trip_date, planned_dispatch_date,
				 actual_dispatch_time, docstatus,
				 creation, modified, modified_by, owner, idx)
			VALUES
				(%(name)s, 'DT-DEMO-', %(transporter)s, %(driver)s, %(vehicle)s,
				 %(warehouse)s, %(status)s, %(trip_date)s, %(dispatch_date)s,
				 %(dispatch_time)s, 1,
				 %(now)s, %(now)s, 'Administrator', 'Administrator', 0)
		""", {
			"name": t["name"],
			"transporter": t["transporter"],
			"driver": t["driver"],
			"vehicle": t["vehicle"],
			"warehouse": warehouse or "",
			"status": t["status"],
			"trip_date": t["trip_date"],
			"dispatch_date": t["dispatch_date"],
			"dispatch_time": dispatch_time,
			"now": now,
		})
		print(f"  ✅ Created Delivery Trip: {t['name']} ({t['status']})")

		# Insert stops for this trip
		for stop in t["stops"]:
			arrival = stop.get("arrival")
			frappe.db.sql("""
				INSERT INTO `tabDelivery Stop`
					(name, parent, parenttype, parentfield, idx,
					 sequence_no, customer, address,
					 delivery_window_start, delivery_window_end,
					 status, actual_arrival_time,
					 creation, modified, modified_by, owner, docstatus)
				VALUES
					(%(name)s, %(parent)s, 'Delivery Trip', 'delivery_stops', %(idx)s,
					 %(seq)s, %(customer)s, %(address)s,
					 %(win_start)s, %(win_end)s,
					 %(status)s, %(arrival)s,
					 %(now)s, %(now)s, 'Administrator', 'Administrator', 0)
			""", {
				"name": frappe.generate_hash("", 10),
				"parent": t["name"],
				"idx": stop["seq"],
				"seq": stop["seq"],
				"customer": stop["cust"],
				"address": stop["addr"],
				"win_start": stop["win_start"],
				"win_end": stop["win_end"],
				"status": stop["status"],
				"arrival": arrival,
				"now": now,
			})

		frappe.db.commit()
		print(f"    -> {len(t['stops'])} delivery stops added")

	print("  ✅ All demo trips and stops created")


def _create_demo_reconciliation_sql():
	"""Insert Trip Cost Reconciliation records for all completed trips.

	This feeds the 'Cost Per Delivery by Transporter' report/chart.
	"""
	now = now_datetime()

	completed_trips = frappe.db.sql(
		"""SELECT name, transporter FROM `tabDelivery Trip`
		   WHERE trip_status = 'Completed'""", as_dict=True
	)

	if not completed_trips:
		print("  ⚠️  No completed trips found — skipping reconciliation data")
		return

	for idx, trip in enumerate(completed_trips, 1):
		# Count delivered stops for this trip
		stop_count = frappe.db.count("Delivery Stop", {
			"parenttype": "Delivery Trip",
			"parent": trip.name,
		})

		# Vary costs by transporter for interesting chart data
		if "FastTrack" in trip.transporter:
			fuel = 1500.00
			payout = 3000.00
		elif "CityExpress" in trip.transporter:
			fuel = 1200.00
			payout = 2500.00
		else:
			fuel = 2200.00
			payout = 4800.00

		cost_per_stop = round((fuel + payout) / stop_count, 2) if stop_count > 0 else 0

		recon_name = f"TCR-DEMO-{idx:04d}"
		frappe.db.sql("""
			INSERT INTO `tabTrip Cost Reconciliation`
				(name, naming_series, delivery_trip, reconciliation_date,
				 fuel_cost, transporter_payout, total_stops, cost_per_stop,
				 creation, modified, modified_by, owner, docstatus, idx)
			VALUES
				(%(name)s, 'TCR-DEMO-', %(trip)s, %(date)s,
				 %(fuel)s, %(payout)s, %(stops)s, %(cps)s,
				 %(now)s, %(now)s, 'Administrator', 'Administrator', 0, 0)
		""", {
			"name": recon_name,
			"trip": trip.name,
			"date": today(),
			"fuel": fuel,
			"payout": payout,
			"stops": stop_count,
			"cps": cost_per_stop,
			"now": now,
		})
		print(f"  ✅ Created TCR: {recon_name} ({trip.transporter}, ₹{cost_per_stop}/stop)")
