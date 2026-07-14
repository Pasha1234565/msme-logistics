from __future__ import unicode_literals

import frappe


def execute():
	"""Create MSME workspace directly in the database.

	This bypasses Frappe's workspace JSON sync mechanism to ensure
	a dedicated workspace is created without affecting other apps.
	"""
	workspace_name = "MSME"

	if frappe.db.exists("Workspace", workspace_name):
		print(f"  ℹ️  Workspace '{workspace_name}' already exists")
		return

	workspace = frappe.new_doc("Workspace")
	workspace.name = workspace_name
	workspace.workspace_name = workspace_name
	workspace.label = workspace_name
	workspace.module = "Logistics"
	workspace.is_standard = 1
	workspace.public = 1
	workspace.icon = "truck"

	# Build content layout
	workspace.content = build_workspace_content()

	# Add shortcuts
	add_shortcuts(workspace)

	# Add number cards
	add_number_cards(workspace)

	# Add charts
	add_charts(workspace)

	try:
		workspace.flags.ignore_permissions = True
		workspace.flags.ignore_links = True
		workspace.insert()
		frappe.db.commit()
		print(f"  ✅ Created workspace: {workspace_name}")
	except Exception as e:
		frappe.db.rollback()
		print(f"  ❌ Failed to create workspace: {e}")
		raise


def build_workspace_content():
	"""Build workspace layout JSON content."""
	content = [
		{"type": "header", "data": {"text": "Shortcuts"}},
		{"type": "shortcut", "data": {"shortcut_name": "New Delivery Trip", "type": "DocType", "link_to": "Delivery Trip", "doc_view": "New", "icon": "share", "onboard": 1}},
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
	import json
	return json.dumps(content)


def add_shortcuts(workspace):
	"""Add shortcuts to the workspace."""
	shortcuts = [
		{"label": "New Delivery Trip", "type": "DocType", "link_to": "Delivery Trip", "doc_view": "New", "icon": "share", "kanban_board": "", "dependencies": "", "onboard": 1},
		{"label": "Transporter List", "type": "DocType", "link_to": "Transporter", "doc_view": "List", "icon": "user", "kanban_board": "", "dependencies": "", "onboard": 1},
		{"label": "Trip Cost Recon", "type": "DocType", "link_to": "Trip Cost Reconciliation", "doc_view": "List", "icon": "currency", "kanban_board": "", "dependencies": "", "onboard": 1},
		{"label": "Failed Deliveries", "type": "Report", "link_to": "Failed Delivery Rate by Area", "doc_view": "", "icon": "warning", "kanban_board": "", "dependencies": "", "onboard": 1},
	]
	for s in shortcuts:
		workspace.append("shortcuts", s)


def add_number_cards(workspace):
	"""Add number cards to the workspace."""
	cards = [
		{
			"number_card_name": "Trips In Transit Today",
			"label": "Trips In Transit Today",
			"type": "Document Type",
			"document_type": "Delivery Trip",
			"function": "Count",
			"filter_operator": "=",
			"filter_field": "trip_status",
			"filter_value": "In Transit",
			"color": "#2490ef",
			"show_trend": 1,
		},
		{
			"number_card_name": "Failed Deliveries This Week",
			"label": "Failed Deliveries This Week",
			"type": "Document Type",
			"document_type": "Delivery Stop",
			"function": "Count",
			"filter_operator": "=",
			"filter_field": "status",
			"filter_value": "Failed",
			"color": "#ff6b6b",
			"show_trend": 1,
		},
		{
			"number_card_name": "Avg Cost Per Stop",
			"label": "Avg Cost Per Stop",
			"type": "Document Type",
			"document_type": "Trip Cost Reconciliation",
			"function": "Average",
			"aggregate_function_based_on": "cost_per_stop",
			"color": "#28a745",
		},
	]
	for c in cards:
		workspace.append("number_cards", c)


def add_charts(workspace):
	"""Add charts to the workspace."""
	charts = [
		{
			"chart_name": "SLA Compliance",
			"label": "SLA Compliance by Transporter",
			"chart_type": "Report",
			"report_name": "SLA Compliance by Transporter",
			"is_public": 1,
			"width": "Half",
		},
		{
			"chart_name": "Cost Per Delivery Trend",
			"label": "Cost Per Delivery Trend",
			"chart_type": "Report",
			"report_name": "Cost Per Delivery by Transporter",
			"is_public": 1,
			"width": "Half",
		},
	]
	for c in charts:
		workspace.append("charts", c)
