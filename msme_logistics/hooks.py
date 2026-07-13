from __future__ import unicode_literals

app_name = "msme_logistics"
app_title = "Logistics"
app_publisher = "Your Company"
app_description = "MSME B2B Last-Mile Logistics Management Application"
app_icon = "octicon octicon-truck"
app_color = "blue"
app_email = "info@example.com"
app_license = "MIT"

# Fixtures
# ------------------------------
fixtures = [
	{"dt": "Workspace", "filters": [["module", "=", "Logistics"]]},
	{"dt": "DocType", "filters": [["module", "=", "Logistics"]]},
	{"dt": "Report", "filters": [["module", "=", "Logistics"]]},
	{"dt": "Workflow", "filters": [["document_type", "=", "Delivery Trip"]]},
	{"dt": "Workflow State", "filters": [["name", "in", ["Planned", "Dispatched", "In Transit", "Completed", "Reconciled"]]]},
	{"dt": "Workflow Action", "filters": [["workflow_name", "=", "Delivery Trip Workflow"]]},
	{"dt": "Role", "filters": [["name", "in", ["Dispatch Manager", "Driver"]]]},
	{"dt": "Notification", "filters": [["document_type", "in", ["Delivery Stop", "Delivery Trip"]]]},
]

# DocType Class
# ------------------------------
doctype_class = {}

# Document Events
# ------------------------------
doc_events = {
	# Note: Delivery trip validation logic is handled in the controller class.
	# Document-level hooks can be added here for cross-doctype operations.
}

# Scheduled Tasks
# ------------------------------
scheduler_events = {
	"daily": [
		"msme_logistics.tasks.daily_check_overdue_trips",
	],
	"weekly": [
		"msme_logistics.tasks.weekly_update_transporter_analytics",
	],
}

# Permissions
# ------------------------------
# permission_query_conditions = {}

# Website
# ------------------------------

# Jinja
# ------------------------------
# jinja = {}

# Boot
# ------------------------------
# boot_session = boot_session
