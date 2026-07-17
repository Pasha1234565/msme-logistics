from __future__ import unicode_literals
import frappe


def execute():
	"""Create Module Def for Logistics if it doesn't exist."""
	if not frappe.db.exists("Module Def", "Logistics"):
		module_def = frappe.get_doc(
			{
				"doctype": "Module Def",
				"module_name": "Logistics",
				"app_name": "msme_logistics",
			}
		)
		module_def.insert()
		frappe.db.commit()
		print("Created 'Logistics' Module Def")
	else:
		print("'Logistics' Module Def already exists")
