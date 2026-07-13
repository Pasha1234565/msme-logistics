from __future__ import unicode_literals

import frappe
from frappe.utils import today, add_days, now_datetime


def insert_demo_data():
	"""Insert demo data using direct SQL to bypass DocType controller issues.

	Run via bench console:
		import msme_logistics.commands
		msme_logistics.commands.insert_demo_data()
	"""
	# Check if demo data already exists
	existing = frappe.db.sql("SELECT name FROM `tabTransporter` LIMIT 1")
	if existing:
		print("✅ Demo data already exists, skipping")
		return

	print("Inserting demo data...")
	_create_demo_transporters_sql()
	frappe.db.commit()

	_create_demo_trips_sql()
	frappe.db.commit()

	_create_demo_reconciliation_sql()
	frappe.db.commit()

	print("✅ Demo data inserted successfully!")


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

	# Add vehicle types and service areas
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
	"""Insert demo Delivery Trips using raw SQL."""
	now = now_datetime()
	today_date = today()

	transporters = [r[0] for r in frappe.db.sql(
		"SELECT name FROM `tabTransporter` WHERE status = 'Active' ORDER BY name"
	)]

	if len(transporters) < 2:
		print("  ⚠️  Not enough transporters")
		return

	# Try to get a default warehouse
	warehouse = frappe.db.get_value("Warehouse", {"is_group": 0, "disabled": 0}, "name")

	trips = [
		{
			"name": "DT-DEMO-0001",
			"transporter": transporters[0],
			"driver_name": "Rajesh Kumar",
			"vehicle_no": "DL-01-AB-1234",
			"origin_warehouse": warehouse,
			"trip_status": "In Transit",
			"trip_date": add_days(today_date, -1),
			"planned_dispatch_date": add_days(today_date, -2),
			"actual_dispatch_time": now,
		},
		{
			"name": "DT-DEMO-0002",
			"transporter": transporters[0],
			"driver_name": "Suresh Singh",
			"vehicle_no": "DL-01-CD-5678",
			"origin_warehouse": warehouse,
			"trip_status": "Completed",
			"trip_date": add_days(today_date, -3),
			"planned_dispatch_date": add_days(today_date, -3),
			"actual_dispatch_time": add_days(now, -3),
		},
		{
			"name": "DT-DEMO-0003",
			"transporter": transporters[1],
			"driver_name": "Amit Sharma",
			"vehicle_no": "UP-14-EF-9012",
			"origin_warehouse": warehouse,
			"trip_status": "Planned",
			"trip_date": today_date,
			"planned_dispatch_date": today_date,
		},
	]

	for t in trips:
		dispatch_time = t.get("actual_dispatch_time")
		frappe.db.sql("""
			INSERT INTO `tabDelivery Trip`
				(name, naming_series, transporter, driver_name, vehicle_no,
				 origin_warehouse, trip_status, trip_date, planned_dispatch_date,
				 actual_dispatch_time, docstatus,
				 creation, modified, modified_by, owner, idx)
			VALUES
				(%(name)s, 'DT-DEMO-', %(transporter)s, %(driver_name)s, %(vehicle_no)s,
				 %(warehouse)s, %(status)s, %(trip_date)s, %(planned)s,
				 %(dispatch)s, 1,
				 %(now)s, %(now)s, 'Administrator', 'Administrator', 0)
		""", {
			"name": t["name"],
			"transporter": t["transporter"],
			"driver_name": t["driver_name"],
			"vehicle_no": t["vehicle_no"],
			"warehouse": t["origin_warehouse"] or "",
			"status": t["trip_status"],
			"trip_date": t["trip_date"],
			"planned": t["planned_dispatch_date"],
			"dispatch": dispatch_time,
			"now": now,
		})
		print(f"  ✅ Created Delivery Trip: {t['name']}")

	frappe.db.commit()

	# Add delivery stops
	try:
		customers = frappe.db.sql(
			"SELECT name FROM `tabCustomer` LIMIT 5"
		)
		if customers:
			stops_data = [
				("DT-DEMO-0001", 1, customers[0][0], "123, Main Street, Delhi - 110001",
				 "09:00:00", "11:00:00", "Delivered", now),
				("DT-DEMO-0001", 2, customers[1][0] if len(customers) > 1 else "Customer",
				 "456, Park Avenue, Delhi - 110002",
				 "11:30:00", "13:00:00", "Delivered", now),
				("DT-DEMO-0001", 3, customers[2][0] if len(customers) > 2 else "Customer",
				 "789, MG Road, Noida - 201301",
				 "14:00:00", "16:00:00", "Pending", None),
				("DT-DEMO-0002", 1, customers[0][0] if len(customers) > 0 else "Customer",
				 "123, Main Street, Delhi - 110001",
				 "09:00:00", "10:00:00", "Delivered", add_days(now, -3)),
				("DT-DEMO-0002", 2, customers[3][0] if len(customers) > 3 else "Customer",
				 "321, Sector 12, Noida - 201301",
				 "10:30:00", "12:00:00", "Failed", None),
				("DT-DEMO-0003", 1, customers[4][0] if len(customers) > 4 else "Customer",
				 "555, Civil Lines, Delhi - 110054",
				 "10:00:00", "12:00:00", "Pending", None),
			]

			for trip, seq, customer, address, win_start, win_end, status, arrival in stops_data:
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
					"parent": trip,
					"idx": seq,
					"seq": seq,
					"customer": customer,
					"address": address,
					"win_start": win_start,
					"win_end": win_end,
					"status": status,
					"arrival": arrival,
					"now": now,
				})
			frappe.db.commit()
			print("  ✅ Added delivery stops")
	except Exception as e:
		frappe.db.rollback()
		print(f"  ⚠️  Stops skipped: {e}")


def _create_demo_reconciliation_sql():
	"""Insert demo Trip Cost Reconciliation records."""
	now = now_datetime()

	completed_trips = frappe.db.sql(
		"SELECT name FROM `tabDelivery Trip` WHERE trip_status = 'Completed'"
	)
	if not completed_trips:
		print("  ⚠️  No completed trips found")
		return

	for idx, (trip_name,) in enumerate(completed_trips, 1):
		# Count stops
		stop_count = frappe.db.count("Delivery Stop", {
			"parenttype": "Delivery Trip",
			"parent": trip_name,
		})

		fuel = 1500.00 if idx == 1 else 2000.00
		payout = 3000.00 if idx == 1 else 4500.00
		cost_per_stop = round((fuel + payout) / stop_count, 2) if stop_count > 0 else 0

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
			"name": f"TCR-DEMO-{idx:04d}",
			"trip": trip_name,
			"date": today(),
			"fuel": fuel,
			"payout": payout,
			"stops": stop_count,
			"cps": cost_per_stop,
			"now": now,
		})
		print(f"  ✅ Created Trip Cost Reconciliation: TCR-DEMO-{idx:04d}")
