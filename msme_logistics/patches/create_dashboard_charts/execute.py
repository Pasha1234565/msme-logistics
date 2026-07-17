from __future__ import unicode_literals

import frappe
from frappe.utils import now


def execute():
	"""Create Dashboard Chart records and link them to the MSME workspace via direct SQL.

	This script directly manipulates the database tables to:
	1. Create/update Dashboard Chart records (tabDashboard Chart)
	2. Create/update the workspace's charts child table (tabWorkspace Chart)

	This bypasses the fixture system entirely (which can fail with various
	validation errors) and uses the same reliable direct-SQL approach that
	the reference textile_tracking app uses for wastage charts.
	"""
	create_chart(
		chart_name="SLA Compliance",
		chart_type="Report",
		visual_type="Bar",
		report_name="SLA Compliance by Transporter",
		workspace_name="MSME",
	)

	# NOTE: Cost Per Delivery Trend is NOT created as a Dashboard Chart
	# because Dashboard Chart's `get` API doesn't handle Report-type charts
	# properly (falls through to get_chart_config which is for aggregate charts).
	# The workspace renders this report's chart directly via report_name.
	# We clean up any stale chart record that might exist:
	frappe.db.sql(
		"DELETE FROM `tabDashboard Chart` WHERE `name` = 'Cost Per Delivery Trend'"
	)
	frappe.db.sql(
		"""DELETE FROM `tabWorkspace Chart`
		   WHERE `parent` = 'MSME' AND `parentfield` = 'charts'
		   AND `chart_name` = 'Cost Per Delivery Trend'"""
	)

	# Also update the workspace content field to use report_name directly
	# (existing workspaces have a stale chart_name reference)
	frappe.db.sql(
		"""UPDATE `tabWorkspace`
		   SET `content` = REPLACE(`content`,
		       '{"chart_name":"Cost Per Delivery Trend","col":6}',
		       '{"report_name":"Cost Per Delivery by Transporter","chart_type":"Report","col":6}')
		   WHERE `name` = 'MSME'"""
	)
	frappe.db.commit()

	print("🎯 Dashboard charts setup complete! Refresh the workspace to see them.")


def create_chart(chart_name, chart_type, visual_type, report_name, workspace_name):
	"""Create or update a Dashboard Chart and link it to a workspace."""
	# STEP 1: Create/fix the Dashboard Chart record
	try:
		# Delete old Dashboard Chart record if it exists (to reset any bad data)
		frappe.db.sql(
			"DELETE FROM `tabDashboard Chart` WHERE `name` = %(name)s",
			{"name": chart_name},
		)
		frappe.db.commit()

		# Insert fresh Dashboard Chart record
		frappe.db.sql(
			"""
			INSERT INTO `tabDashboard Chart`
			(`name`, `chart_name`, `chart_type`, `type`,
			 `report_name`, `use_report_chart`, `module`, `is_public`, `is_standard`,
			 `filters_json`, `timeseries`,
			 `timespan`, `time_interval`,
			 `creation`, `modified`, `modified_by`, `owner`, `docstatus`)
			VALUES
			(%(name)s, %(chart_name)s, %(chart_type)s, %(type)s,
			 %(report_name)s, %(use_report_chart)s, %(module)s, %(is_public)s, %(is_standard)s,
			 %(filters_json)s, %(timeseries)s,
			 %(timespan)s, %(time_interval)s,
			 %(creation)s, %(modified)s, %(owner)s, %(owner)s, 0)
		""",
			{
				"name": chart_name,
				"chart_name": chart_name,
				"chart_type": chart_type,
				"type": visual_type,
				"use_report_chart": 1,
				"report_name": report_name,
				"module": "Logistics",
				"is_public": 1,
				"is_standard": 0,
				"filters_json": "{}",
				"timeseries": 0,
				"timespan": "Last Month",
				"time_interval": "Monthly",
				"creation": now(),
				"modified": now(),
				"owner": "Administrator",
			},
		)
		frappe.db.commit()
		print(f"✅ Dashboard Chart '{chart_name}' created/updated")
	except Exception as e:
		print(f"⚠️ Dashboard Chart error for '{chart_name}': {e}")

	# STEP 2: Directly update the workspace's charts child table
	chart_link_name = f"ws-chart-{chart_name.lower().replace(' ', '-')}"
	try:
		# Delete old chart link records for this workspace
		frappe.db.sql(
			"""
			DELETE FROM `tabWorkspace Chart`
			WHERE `parent` = %(workspace)s AND `parentfield` = 'charts'
			AND `chart_name` = %(chart_name)s
		""",
			{"workspace": workspace_name, "chart_name": chart_name},
		)
		frappe.db.commit()

		# Insert fresh chart link record
		frappe.db.sql(
			"""
			INSERT INTO `tabWorkspace Chart`
			(`name`, `parent`, `parenttype`, `parentfield`,
			 `chart_name`, `label`, `idx`,
			 `creation`, `modified`, `modified_by`, `owner`, `docstatus`)
			VALUES
			(%(name)s, %(parent)s, 'Workspace', 'charts',
			 %(chart_name)s, %(label)s, %(idx)s,
			 %(creation)s, %(modified)s, %(owner)s, %(owner)s, 0)
		""",
			{
				"name": chart_link_name,
				"parent": workspace_name,
				"chart_name": chart_name,
				"label": chart_name,
				"idx": 1,
				"creation": now(),
				"modified": now(),
				"owner": "Administrator",
			},
		)
		frappe.db.commit()
		print(
			f"✅ Workspace '{workspace_name}' now has chart link to '{chart_name}'"
		)
	except Exception as e:
		print(f"⚠️ Workspace chart link error for '{chart_name}': {e}")
