from __future__ import unicode_literals

import json
import secrets
import string

import frappe
from frappe.utils import now_datetime, today, add_days


def after_install():
	"""Run after app installation. Creates workspace and demo data."""
	create_msme_workspace()
	run_tracking_fixes()
	insert_demo_data()


def after_migrate():
	"""Run after migration. Ensures workspace and tracking infrastructure exist."""
	create_msme_workspace()
	run_tracking_fixes()


def run_tracking_fixes():
	"""Ensure all tracking infrastructure is in place.

	Runs on every migrate. Handles:
	1. Adding missing child-table columns to Delivery Status Log
	2. Backfilling tracking IDs on existing stops that lack them
	3. Syncing the in_list_view field property
	"""
	# ── 1. Ensure Delivery Status Log has proper child-table columns ──
	table_name = "tabDelivery Status Log"
	required_columns = {
		"parent": "VARCHAR(140) NULL",
		"parenttype": "VARCHAR(140) NULL",
		"parentfield": "VARCHAR(140) NULL",
	}
	try:
		existing_cols = {
			row[0]
			for row in frappe.db.sql(
				"SHOW COLUMNS FROM `{0}`".format(table_name)
			)
		}
		for col, col_def in required_columns.items():
			if col not in existing_cols:
				frappe.db.sql(
					"ALTER TABLE `{0}` ADD COLUMN `{1}` {2}".format(table_name, col, col_def)
				)
		frappe.db.commit()
	except Exception:
		pass  # Table may not exist yet on fresh installs — fine

	# ── 2. Backfill tracking IDs on existing stops ──
	chars = string.ascii_uppercase + string.digits
	missing = frappe.db.sql(
		"""SELECT name FROM `tabDelivery Stop`
		 WHERE (tracking_id IS NULL OR tracking_id = '')
		 AND parent IS NOT NULL AND parent != ''
		 LIMIT 500""",
		as_dict=True,
	)

	if missing:
		for stop in missing:
			for _ in range(100):
				tid = "TRK-" + "".join(secrets.choice(chars) for _ in range(8))
				if not frappe.db.exists("Delivery Stop", {"tracking_id": tid}):
					break
			frappe.db.set_value("Delivery Stop", stop.name, "tracking_id", tid, update_modified=False)
		frappe.db.commit()
		print("✅ Backfilled {0} stops with tracking IDs".format(len(missing)))

	# ── 3. Sync in_list_view for tracking_id field ──
	frappe.db.set_value(
		"DocField",
		{"parent": "Delivery Stop", "fieldname": "tracking_id"},
		{"in_list_view": 1, "columns": 2},
	)
	frappe.db.commit()


def create_msme_workspace():
	"""Create MSME workspace if it doesn't exist."""
	workspace_name = "MSME"

	try:
		if frappe.db.exists("Workspace", workspace_name):
			workspace = frappe.get_doc("Workspace", workspace_name)
			workspace.flags.ignore_permissions = True
			workspace.flags.ignore_links = True
			# Clear existing shortcuts/charts/cards to rebuild
			workspace.shortcuts = []
			workspace.number_cards = []
			workspace.charts = []
			workspace.content = json.dumps([])
			workspace.links = []
		else:
			workspace = frappe.new_doc("Workspace")
			workspace.name = workspace_name
			workspace.title = workspace_name
			workspace.workspace_name = workspace_name
			workspace.module = "Logistics"
			workspace.is_standard = 1
			workspace.public = 1
			workspace.icon = "truck"
			workspace.label = workspace_name

		# Build content layout
		content = [
			{"type": "header", "data": {"text": "Shortcuts"}},
			{"type": "shortcut", "data": {"shortcut_name": "New Delivery Trip", "type": "DocType", "link_to": "Delivery Trip", "doc_view": "New", "icon": "share", "onboard": 1}},
			{"type": "shortcut", "data": {"shortcut_name": "Delivery Status", "type": "Page", "link_to": "delivery-status", "icon": "map-marker", "onboard": 1}},
			{"type": "shortcut", "data": {"shortcut_name": "Transporter List", "type": "DocType", "link_to": "Transporter", "doc_view": "List", "icon": "user", "onboard": 1}},
			{"type": "shortcut", "data": {"shortcut_name": "Trip Cost Recon", "type": "DocType", "link_to": "Trip Cost Reconciliation", "doc_view": "List", "icon": "currency", "onboard": 1}},
			{"type": "shortcut", "data": {"shortcut_name": "Failed Deliveries", "type": "Report", "link_to": "Failed Delivery Rate by Area", "icon": "warning", "onboard": 1}},
			{"type": "header", "data": {"text": "Key Metrics"}},
			{"type": "number_card", "data": {"number_card_name": "Trips In Transit Today", "label": "Trips In Transit Today"}},
			{"type": "number_card", "data": {"number_card_name": "Deliveries Completed Today", "label": "Deliveries Completed Today"}},
			{"type": "number_card", "data": {"number_card_name": "Avg Cost Per Stop", "label": "Avg Cost Per Stop"}},
			{"type": "header", "data": {"text": "Analytics"}},
			{"type": "chart", "data": {"chart_name": "SLA Compliance", "label": "SLA Compliance by Transporter", "chart_type": "Report", "report_name": "SLA Compliance by Transporter", "width": "Half"}},
			{"type": "chart", "data": {"chart_name": "Cost Per Delivery Trend", "label": "Cost Per Delivery Trend", "chart_type": "Report", "report_name": "Cost Per Delivery by Transporter", "width": "Half"}},
			{"type": "card", "data": {"card_name": "Transactions", "col": 4, "items": [
				{"type": "DocType", "link_to": "Delivery Trip", "label": "Delivery Trip", "description": "Create and manage delivery trips", "onboard": 1},
				{"type": "DocType", "link_to": "Trip Cost Reconciliation", "label": "Trip Cost Reconciliation", "description": "Reconcile trip costs per delivery", "onboard": 1}
			]}},
			{"type": "card", "data": {"card_name": "Master Data", "col": 4, "items": [
				{"type": "DocType", "link_to": "Transporter", "label": "Transporter", "description": "Manage transporters, vehicle types, and service areas", "onboard": 1}
			]}},
			{"type": "card", "data": {"card_name": "Reports", "col": 4, "items": [
				{"type": "Report", "link_to": "SLA Compliance by Transporter", "label": "SLA Compliance", "description": "On-time delivery compliance by transporter", "is_query_report": 1, "onboard": 1},
				{"type": "Report", "link_to": "Cost Per Delivery by Transporter", "label": "Cost Per Delivery", "description": "Cost per delivery analysis by transporter", "is_query_report": 1, "onboard": 1},
				{"type": "Report", "link_to": "Failed Delivery Rate by Area", "label": "Failed Delivery Rate", "description": "Failed/rescheduled deliveries by area/pincode", "is_query_report": 1, "onboard": 1}
			]}},
		]
		workspace.content = json.dumps(content)

		# Add shortcuts
		for s in [
			{"label": "New Delivery Trip", "type": "DocType", "link_to": "Delivery Trip", "doc_view": "New", "icon": "share", "kanban_board": "", "dependencies": "", "onboard": 1},
			{"label": "Delivery Status", "type": "Page", "link_to": "delivery-status", "icon": "map-marker", "kanban_board": "", "dependencies": "", "onboard": 1},
			{"label": "Transporter List", "type": "DocType", "link_to": "Transporter", "doc_view": "List", "icon": "user", "kanban_board": "", "dependencies": "", "onboard": 1},
			{"label": "Trip Cost Recon", "type": "DocType", "link_to": "Trip Cost Reconciliation", "doc_view": "List", "icon": "currency", "kanban_board": "", "dependencies": "", "onboard": 1},
			{"label": "Failed Deliveries", "type": "Report", "link_to": "Failed Delivery Rate by Area", "doc_view": "", "icon": "warning", "kanban_board": "", "dependencies": "", "onboard": 1},
		]:
			workspace.append("shortcuts", s)

		# Add number cards
		for c in [
			{"number_card_name": "Trips In Transit Today", "label": "Trips In Transit Today", "type": "Document Type", "document_type": "Delivery Trip", "function": "Count", "filter_operator": "=", "filter_field": "trip_status", "filter_value": "In Transit", "color": "#2490ef", "show_trend": 1},
			{"number_card_name": "Deliveries Completed Today", "label": "Deliveries Completed Today", "type": "Document Type", "document_type": "Delivery Stop", "function": "Count", "filter_operator": "=", "filter_field": "status", "filter_value": "Delivered", "color": "#28a745", "show_trend": 1},
			{"number_card_name": "Avg Cost Per Stop", "label": "Avg Cost Per Stop", "type": "Document Type", "document_type": "Trip Cost Reconciliation", "function": "Average", "aggregate_function_based_on": "cost_per_stop", "color": "#28a745"},
		]:
			workspace.append("number_cards", c)

		# Add charts
		for c in [
			{"chart_name": "SLA Compliance", "label": "SLA Compliance by Transporter", "chart_type": "Report", "report_name": "SLA Compliance by Transporter", "is_public": 1, "width": "Half"},
			{"chart_name": "Cost Per Delivery Trend", "label": "Cost Per Delivery Trend", "chart_type": "Report", "report_name": "Cost Per Delivery by Transporter", "is_public": 1, "width": "Half"},
		]:
			workspace.append("charts", c)

		workspace.flags.ignore_permissions = True
		workspace.flags.ignore_links = True
		workspace.save()
		frappe.db.commit()
		print(f"✅ Created workspace: {workspace_name}")
	except Exception as e:
		frappe.db.rollback()
		print(f"⚠️ Could not create workspace: {e}")


def _generate_tracking_id():
	"""Generate a unique tracking ID in format TRK-XXXXXXXX."""
	chars = string.ascii_uppercase + string.digits
	for _ in range(100):
		tid = "TRK-" + "".join(secrets.choice(chars) for _ in range(8))
		if not frappe.db.exists("Delivery Stop", {"tracking_id": tid}):
			return tid
	return "TRK-" + "".join(secrets.choice(chars) for _ in range(8))


def delete_demo_data():
	"""Delete existing demo data (trips, reconciliations, stops, status logs, transporters).

	Run from bench console:
	  bench execute msme_logistics.logistics.setup.delete_demo_data
	"""
	print("🗑️  Deleting existing demo data...")
	for doctype in ["Delivery Status Log", "Delivery Stop", "Delivery Trip Delivery Note", "Delivery Trip", "Trip Cost Reconciliation", "Transporter"]:
		names = frappe.get_all(doctype, pluck="name")
		if names:
			for name in names:
				try:
					frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
				except Exception:
					pass
			print(f"  ✅ Deleted {len(names)} {doctype} records")
		frappe.db.commit()
	print("✅ Demo data deleted. Run `bench execute msme_logistics.logistics.setup.insert_demo_data` to create fresh data.")


def insert_demo_data():
	"""Insert demo transporters, trips, and reconciliations with tracking IDs."""
	if frappe.db.get_all("Transporter", limit=1):
		print("ℹ️ Demo data already exists, skipping")
		return

	now = now_datetime()
	today_date = today()

	# Create Transporters
	transporters_data = [
		{"transporter_name": "FastTrack Logistics", "email": "info@fasttrack.in", "phone": "+91-9876543210"},
		{"transporter_name": "CityExpress Couriers", "email": "dispatch@cityexpress.com", "phone": "+91-9876543211"},
		{"transporter_name": "SafeHands Transport", "email": "ops@safehands.in", "phone": "+91-9876543212"},
	]

	for t in transporters_data:
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
				]
			})
			doc.flags.ignore_permissions = True
			doc.flags.ignore_links = True
			doc.flags.ignore_validate = True
			doc.insert()
			print(f"✅ Created Transporter: {t['transporter_name']}")
		except Exception as e:
			print(f"⚠️ Skipped Transporter {t['transporter_name']}: {e}")

	frappe.db.commit()

	# Create Delivery Trips
	transporter_names = frappe.get_all("Transporter", pluck="name")
	if len(transporter_names) < 2:
		return

	warehouse = frappe.get_all("Warehouse", {"is_group": 0, "disabled": 0}, pluck="name")
	warehouse = warehouse[0] if warehouse else ""
	_ts = lambda: _generate_tracking_id()
	_arrival = add_days(now_datetime(), -3).strftime("%Y-%m-%d %H:%M:%S")

	trips_config = [
		{
			"transporter": transporter_names[0], "driver_name": "Rajesh Kumar",
			"vehicle_no": "DL-01-AB-1234", "trip_status": "In Transit",
			"trip_date": add_days(today_date, -1), "planned_dispatch_date": add_days(today_date, -2),
		},
		{
			"transporter": transporter_names[1], "driver_name": "Suresh Singh",
			"vehicle_no": "DL-01-CD-5678", "trip_status": "Completed",
			"trip_date": add_days(today_date, -3), "planned_dispatch_date": add_days(today_date, -3),
		},
	]

	for t in trips_config:
		try:
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
					{"sequence_no": 1, "customer": "Customer", "address": "123 Main St, Delhi",
					 "status": "Shipped", "delivery_window_start": "09:00:00",
					 "delivery_window_end": "11:00:00", "tracking_id": _ts()},
					{"sequence_no": 2, "customer": "Customer", "address": "456 Park Ave, Delhi",
					 "status": "In Transit", "delivery_window_start": "11:30:00",
					 "delivery_window_end": "13:00:00", "tracking_id": _ts()},
					{"sequence_no": 3, "customer": "Customer", "address": "789 Lake Rd, Delhi",
					 "status": "Out for Delivery", "delivery_window_start": "14:00:00",
					 "delivery_window_end": "16:00:00", "tracking_id": _ts()},
					{"sequence_no": 4, "customer": "Customer", "address": "321 Hill St, Delhi",
					 "status": "Delivered", "delivery_window_start": "16:30:00",
					 "delivery_window_end": "18:00:00",
					 "actual_arrival_time": _arrival, "tracking_id": _ts()},
				],
			})
			doc.flags.ignore_permissions = True
			doc.flags.ignore_links = True
			doc.flags.ignore_validate = True
			doc.insert()
			print(f"✅ Created Delivery Trip: {doc.name} ({t['trip_status']})")
		except Exception as e:
			print(f"⚠️ Skipped trip: {e}")

	frappe.db.commit()

	# ── Create Trip Cost Reconciliation records for completed trips ──
	completed_trips = frappe.db.sql(
		"""SELECT name, transporter FROM `tabDelivery Trip`
		 WHERE trip_status = 'Completed' LIMIT 5""",
		as_dict=True,
	)
	for t in completed_trips:
		stop_count = frappe.db.count("Delivery Stop", {"parent": t.name, "parenttype": "Delivery Trip"})
		cost_per_stop = round(150.0 + (stop_count * 25.0), 2)
		try:
			recon = frappe.get_doc({
				"doctype": "Trip Cost Reconciliation",
				"delivery_trip": t.name,
				"reconciliation_date": today(),
				"fuel_cost": 800,
				"transporter_payout": 1200,
				"total_stops": stop_count,
				"cost_per_stop": cost_per_stop,
			})
			recon.flags.ignore_permissions = True
			recon.flags.ignore_links = True
			recon.insert()
			print(f"✅ Created Trip Cost Reconciliation for {t.name}")
		except Exception as e:
			print(f"⚠️ Skipped reconciliation for {t.name}: {e}")

	frappe.db.commit()
	print("✅ Demo data inserted successfully!")
