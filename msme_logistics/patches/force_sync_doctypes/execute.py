from __future__ import unicode_literals

import os
import json
import frappe
from frappe.model.sync import sync_for


def execute():
	"""Force-sync all DocTypes, Workspace, and Reports from JSON files.

	Uses Frappe's built-in sync_for() which properly creates DocType records
	along with their database tables, fields, and schema. This handles the
	case where Frappe's automatic model sync during `bench migrate` does not
	create DocType records from the JSON files in the doctype/ directory.
	"""
	app_name = "msme_logistics"

	print("  🔄 Syncing DocTypes from JSON files...")
	try:
		sync_for(app_name, force=True)
		frappe.db.commit()
		print("  ✅ DocTypes synced successfully")
	except Exception as e:
		frappe.db.rollback()
		print(f"  ❌ Error syncing DocTypes: {e}")
		raise

	# Also ensure workspace is created from JSON file
	print("  🔄 Syncing Workspace from JSON files...")
	try:
		app_path = frappe.get_app_path(app_name)
		_sync_workspace(app_path)
		frappe.db.commit()
	except Exception as e:
		frappe.db.rollback()
		print(f"  ⚠️  Workspace sync warning: {e}")

	print("  ✅ Force-sync completed successfully")


def _sync_workspace(app_path):
	"""Create Workspace from JSON file if it doesn't exist."""
	workspace_path = os.path.join(app_path, "workspace")
	if not os.path.exists(workspace_path):
		print("  ⚠️  workspace directory not found")
		return

	for root, dirs, files in os.walk(workspace_path):
		for f in files:
			if not f.endswith(".json"):
				continue

			filepath = os.path.join(root, f)
			with open(filepath, "rb") as fp:
				try:
					data = json.load(fp)
				except json.JSONDecodeError:
					print(f"  ⚠️  Invalid JSON: {filepath}")
					continue

			if data.get("doctype") != "Workspace":
				continue

			name = data["name"]
			if frappe.db.exists("Workspace", name):
				print(f"  ℹ️  Workspace '{name}' already exists")
				continue

			try:
				doc = frappe.get_doc(data)
				doc.flags.ignore_permissions = True
				doc.flags.ignore_links = True
				doc.flags.ignore_validate = True
				doc.insert()
				frappe.db.commit()
				print(f"  ✅ Created Workspace: {name}")
			except Exception as e:
				frappe.db.rollback()
				print(f"  ❌ Failed to create Workspace '{name}': {e}")
