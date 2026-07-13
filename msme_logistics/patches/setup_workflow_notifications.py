from __future__ import unicode_literals

import frappe
from frappe.utils import now


def execute():
	"""Setup Workflow, Roles, and Notifications for Logistics app."""
	create_roles()
	create_workflow()
	create_notifications()


def create_roles():
	"""Create custom roles: Dispatch Manager, Driver."""
	for role_name in ("Dispatch Manager", "Driver"):
		if not frappe.db.exists("Role", role_name):
			role = frappe.new_doc("Role")
			role.role_name = role_name
			role.desk_access = 1
			role.is_custom = 1
			role.insert(ignore_permissions=True)
			print(f"Created Role: {role_name}")


def create_workflow():
	"""Create Delivery Trip workflow.

	States: Planned → Dispatched → In Transit → Completed → Reconciled
	"""
	if frappe.db.exists("Workflow", "Delivery Trip Workflow"):
		print("Workflow 'Delivery Trip Workflow' already exists")
		return

	workflow = frappe.new_doc("Workflow")
	workflow.workflow_name = "Delivery Trip Workflow"
	workflow.document_type = "Delivery Trip"
	workflow.is_active = 1
	workflow.send_email_alert = 0

	# Workflow States
	states = [
		{
			"state": "Planned",
			"allow_edit": "All",
			"update_field": "trip_status",
			"update_value": "Planned",
		},
		{
			"state": "Dispatched",
			"allow_edit": "Dispatch Manager",
			"update_field": "trip_status",
			"update_value": "Dispatched",
		},
		{
			"state": "In Transit",
			"allow_edit": "Dispatch Manager",
			"update_field": "trip_status",
			"update_value": "In Transit",
		},
		{
			"state": "Completed",
			"allow_edit": "Dispatch Manager",
			"update_field": "trip_status",
			"update_value": "Completed",
		},
		{
			"state": "Reconciled",
			"allow_edit": "Dispatch Manager",
			"update_field": "trip_status",
			"update_value": "Reconciled",
		},
	]

	for state_data in states:
		workflow.append("states", state_data)

	# Workflow Transitions
	transitions = [
		{
			"state": "Planned",
			"action": "Dispatch Trip",
			"next_state": "Dispatched",
			"allowed": "Dispatch Manager",
		},
		{
			"state": "Dispatched",
			"action": "Mark In Transit",
			"next_state": "In Transit",
			"allowed": "Dispatch Manager",
		},
		{
			"state": "In Transit",
			"action": "Complete Trip",
			"next_state": "Completed",
			"allowed": "Dispatch Manager",
		},
		{
			"state": "Completed",
			"action": "Reconcile Trip",
			"next_state": "Reconciled",
			"allowed": "Dispatch Manager",
		},
	]

	for transition_data in transitions:
		workflow.append("transitions", transition_data)

	workflow.insert(ignore_permissions=True)
	print("Created Workflow: Delivery Trip Workflow")


def create_notifications():
	"""Create Notification records for the Logistics app."""
	notifications = [
		{
			"name": "Delivery Failed Alert",
			"subject": "Delivery Failed: {{ doc.name }} - Stop {{ doc.sequence_no }}",
			"document_type": "Delivery Stop",
			"event": "Save",
			"condition": 'doc.status == "Failed"',
			"channel": ["System Notification"],
			"recipients": [
				{
					"receiver_by_document_field": "owner",
				}
			],
			"send_system_notification": 1,
			"send_email": 0,
			"enabled": 1,
		},
		{
			"name": "Trip Not Dispatched Alert",
			"subject": "Trip {{ doc.name }} is overdue for dispatch (planned: {{ doc.planned_dispatch_date }})",
			"document_type": "Delivery Trip",
			"event": "Days After",
			"days_before": 0,
			"days_after": 1,
			"condition": 'doc.trip_status == "Planned"',
			"channel": ["System Notification"],
			"recipients": [
				{
					"receiver_by_document_field": "owner",
				}
			],
			"send_system_notification": 1,
			"send_email": 0,
			"enabled": 1,
		},
	]

	for notif_data in notifications:
		name = notif_data.pop("name")
		if frappe.db.exists("Notification", name):
			print(f"Notification '{name}' already exists")
			continue

		notif = frappe.new_doc("Notification")
		notif.update(notif_data)
		notif.name = name
		notif.insert(ignore_permissions=True)
		print(f"Created Notification: {name}")
