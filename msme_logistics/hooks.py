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
doctype_class = {
	"Delivery Stop": "msme_logistics.logistics.doctype.delivery_stop.delivery_stop.DeliveryStop",
	"Delivery Trip": "msme_logistics.logistics.doctype.delivery_trip.delivery_trip.DeliveryTrip",
	"Delivery Status Log": "msme_logistics.logistics.doctype.delivery_status_log.delivery_status_log.DeliveryStatusLog",
	"Transporter": "msme_logistics.logistics.doctype.transporter.transporter.Transporter",
	"Trip Cost Reconciliation": "msme_logistics.logistics.doctype.trip_cost_reconciliation.trip_cost_reconciliation.TripCostReconciliation",
}

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
		"msme_logistics.logistics.tasks.daily_check_overdue_trips",
	],
	"weekly": [
		"msme_logistics.logistics.tasks.weekly_update_transporter_analytics",
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

# Run after every bench migrate to ensure child table columns exist
# and dashboard charts are created
# ------------------------------
after_migrate = [
	"msme_logistics.logistics.setup.after_migrate",
	"msme_logistics.patches.fix_child_table_parent_columns.execute",
	"msme_logistics.patches.create_dashboard_charts.execute",
]

# Run on first HTTP request to fix child table parent columns
# ------------------------------
# before_request is the most reliable hook because frappe.db is always connected
# during HTTP requests. The cache flag prevents re-running on every request.
before_request = ["msme_logistics.patches.fix_child_table_parent_columns.try_fix_once"]

# After Install
# ------------------------------
after_install = "msme_logistics.logistics.setup.after_install"
