from __future__ import unicode_literals

import json
import frappe
from frappe.utils import now_datetime, today, add_days


def after_install():
	"""Run after app installation. Creates workspace and demo data."""
	create_msme_workspace()
	insert_demo_data()


def after_migrate():
	"""Run after migration. Ensures workspace exists."""
	create_msme_workspace()


def create_msme_workspace():
	"""Create MSME workspace if it doesn't exist."""
	workspace_name = "MSME"

	if frappe.db.exists("Workspace", workspace_name):
		return

	try:
		workspace = frappe.new_doc("Workspace")
		workspace.name = workspace_name
		workspace.title = workspace_name
		workspace.workspace_name = workspace_name
		workspace.label = workspace_name
		workspace.module = "Logistics"
		workspace.is_standard = 1
		workspace.public = 1
		workspace.icon = "truck"

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
			{"type": "number_card", "data": {"number_card_name": "Failed Deliveries This Week", "label": "Failed Deliveries This Week"}},
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
			{"number_card_name": "Failed Deliveries This Week", "label": "Failed Deliveries This Week", "type": "Document Type", "document_type": "Delivery Stop", "function": "Count", "filter_operator": "=", "filter_field": "status", "filter_value": "Failed", "color": "#ff6b6b", "show_trend": 1},
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
		workspace.insert()
		frappe.db.commit()
		print(f"✅ Created workspace: {workspace_name}")
	except Exception as e:
		frappe.db.rollback()
		print(f"⚠️ Could not create workspace: {e}")


def insert_demo_data():
	"""Insert demo transporters, trips, and reconciliations."""
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

	trips_data = [
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

	for t in trips_data:
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
					{"sequence_no": 1, "customer": "Customer", "address": "123 Main St, Delhi", "status": "Delivered", "delivery_window_start": "09:00:00", "delivery_window_end": "11:00:00"},
					{"sequence_no": 2, "customer": "Customer", "address": "456 Park Ave, Delhi", "status": "Pending", "delivery_window_start": "11:30:00", "delivery_window_end": "13:00:00"},
				]
			})
			doc.flags.ignore_permissions = True
			doc.flags.ignore_links = True
			doc.flags.ignore_validate = True
			doc.insert()
			print(f"✅ Created Delivery Trip: {doc.name}")
		except Exception as e:
			print(f"⚠️ Skipped trip: {e}")

	frappe.db.commit()
	print("✅ Demo data inserted successfully!")
