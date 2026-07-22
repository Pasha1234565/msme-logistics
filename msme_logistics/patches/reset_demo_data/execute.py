from __future__ import unicode_literals

import secrets
import string

import frappe
from frappe.utils import now_datetime, today, add_days


def execute():
	"""Fresh reset of all demo data with proper stops, actual_arrival_time, and TCR records."""
	print("=" * 60)
	print("🔄 Resetting all demo data...")
	print("=" * 60)

	# ── Step 1: Delete ALL existing data in reverse dependency order ──
	_delete_all_data()

	# ── Step 2: Create Transporters ──
	print("\n📦 Creating Transporters...")
	transporters = _create_transporters()

	# ── Step 3: Create Delivery Trips with stops ──
	print("\n🚛 Creating Delivery Trips with stops...")
	warehouse = _get_warehouse()
	trips = _create_trips(transporters, warehouse)

	# ── Step 4: Create Trip Cost Reconciliation for completed trips ──
	print("\n💰 Creating Trip Cost Reconciliations...")
	_create_reconciliations(trips)

	print("\n" + "=" * 60)
	print("✅ Demo data reset complete! Refresh the workspace to see charts.")
	print("=" * 60)


def _delete_all_data():
	"""Delete all records in reverse dependency order."""
	doctypes = [
		"Delivery Status Log",
		"Delivery Stop",
		"Delivery Trip Delivery Note",
		"Trip Cost Reconciliation",
		"Delivery Trip",
		"Customer",
		"Transporter",
	]
	for doctype in doctypes:
		names = frappe.get_all(doctype, pluck="name")
		if names:
			for name in names:
				try:
					frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
				except Exception:
					pass
			frappe.db.commit()
			print(f"  ✅ Deleted {len(names)} {doctype}")


def _create_transporters():
	"""Create 3 demo transporters."""
	data = [
		{"transporter_name": "FastTrack Logistics", "email": "info@fasttrack.in", "phone": "+91-9876543210"},
		{"transporter_name": "CityExpress Couriers", "email": "dispatch@cityexpress.com", "phone": "+91-9876543211"},
		{"transporter_name": "SafeHands Transport", "email": "ops@safehands.in", "phone": "+91-9876543212"},
	]
	names = []
	for t in data:
		try:
			doc = frappe.get_doc({
				"doctype": "Transporter",
				"transporter_name": t["transporter_name"],
				"status": "Active",
				"email": t["email"],
				"phone": t["phone"],
				"vehicle_types": [
					{"vehicle_type": "Tata Ace", "capacity_kg": 750, "rate_per_km": 12.00},
					{"vehicle_type": "Ashok Leyland", "capacity_kg": 2000, "rate_per_km": 18.50},
				],
				"service_areas": [
					{"pincode_from": "110001", "pincode_to": "110099"},
				],
				"default_transit_days": 3,
			})
			doc.flags.ignore_permissions = True
			doc.flags.ignore_links = True
			doc.insert()
			names.append(doc.name)
			print(f"  ✅ {t['transporter_name']}")
		except Exception as e:
			print(f"  ⚠️ {t['transporter_name']}: {e}")
	frappe.db.commit()
	return names


def _get_warehouse():
	"""Get first non-group warehouse."""
	warehouses = frappe.get_all("Warehouse", {"is_group": 0, "disabled": 0}, pluck="name", limit=1)
	return warehouses[0] if warehouses else "Stores - B"


def _create_trips(transporters, warehouse):
	"""Create 2 demo trips with 4 stops each, with actual_arrival_time on Delivered."""
	today_date = today()
	now = now_datetime()

	trips_data = [
		{
			"transporter": transporters[0],
			"driver_name": "Rajesh Kumar",
			"vehicle_no": "DL-01-AB-1234",
			"trip_status": "In Transit",
			"trip_date": add_days(today_date, -1),
			"planned_dispatch_date": add_days(today_date, -2),
		},
		{
			"transporter": transporters[1],
			"driver_name": "Suresh Singh",
			"vehicle_no": "DL-01-CD-5678",
			"trip_status": "Completed",
			"trip_date": add_days(today_date, -3),
			"planned_dispatch_date": add_days(today_date, -3),
		},
	]

	trip_names = []
	for t in trips_data:
		try:
			_ts = lambda: _generate_tracking_id()
			# Each trip has 4 stops covering all statuses
			_arrival = add_days(now, -3).strftime("%Y-%m-%d %H:%M:%S")

			doc = frappe.get_doc({
				"doctype": "Delivery Trip",
				"transporter": t["transporter"],
				"driver_name": t["driver_name"],
				"vehicle_no": t["vehicle_no"],
				"origin_warehouse": warehouse,
				"trip_status": t["trip_status"],
				"trip_date": t["trip_date"],
				"planned_dispatch_date": t["planned_dispatch_date"],
				"delivery_stops": [
					{
						"sequence_no": 1,
						"customer": "Customer",
						"address": "123 Main St, Delhi",
						"status": "Shipped",
						"delivery_window_start": "09:00:00",
						"delivery_window_end": "11:00:00",
						"tracking_id": _ts(),
					},
					{
						"sequence_no": 2,
						"customer": "Customer",
						"address": "456 Park Ave, Delhi",
						"status": "In Transit",
						"delivery_window_start": "11:30:00",
						"delivery_window_end": "13:00:00",
						"tracking_id": _ts(),
					},
					{
						"sequence_no": 3,
						"customer": "Customer",
						"address": "789 Lake Rd, Delhi",
						"status": "Out for Delivery",
						"delivery_window_start": "14:00:00",
						"delivery_window_end": "16:00:00",
						"tracking_id": _ts(),
					},
					{
						"sequence_no": 4,
						"customer": "Customer",
						"address": "321 Hill St, Delhi",
						"status": "Delivered",
						"delivery_window_start": "16:30:00",
						"delivery_window_end": "18:00:00",
						"actual_arrival_time": _arrival,
						"tracking_id": _ts(),
					},
				],
			})
			doc.flags.ignore_permissions = True
			doc.flags.ignore_links = True
			doc.flags.ignore_validate = True
			doc.insert()
			trip_names.append(doc.name)
			print(f"  ✅ {doc.name} ({t['trip_status']}) — 4 stops created")
		except Exception as e:
			print(f"  ⚠️ Trip {t['trip_status']} failed: {e}")
			import traceback
			traceback.print_exc()

	frappe.db.commit()
	return trip_names


def _create_reconciliations(trip_names):
	"""Create Trip Cost Reconciliation for each completed trip."""
	for name in trip_names:
		trip_status = frappe.db.get_value("Delivery Trip", name, "trip_status")
		if trip_status != "Completed":
			continue
		try:
			doc = frappe.get_doc({
				"doctype": "Trip Cost Reconciliation",
				"delivery_trip": name,
				"reconciliation_date": today(),
				"fuel_cost": 800,
				"transporter_payout": 1200,
			})
			doc.flags.ignore_permissions = True
			doc.flags.ignore_links = True
			doc.insert()
			print(f"  ✅ TCR for {name} — stops={stop_count}, cost_per_stop={doc.cost_per_stop}")
		except Exception as e:
			print(f"  ⚠️ TCR for {name}: {e}")

	frappe.db.commit()


def _generate_tracking_id():
	"""Generate a unique tracking ID in format TRK-XXXXXXXX."""
	chars = string.ascii_uppercase + string.digits
	for _ in range(100):
		tid = "TRK-" + "".join(secrets.choice(chars) for _ in range(8))
		if not frappe.db.exists("Delivery Stop", {"tracking_id": tid}):
			return tid
	return "TRK-" + "".join(secrets.choice(chars) for _ in range(8))
