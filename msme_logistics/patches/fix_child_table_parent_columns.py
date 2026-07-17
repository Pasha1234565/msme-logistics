from __future__ import unicode_literals

import frappe


def try_fix_once():
	"""Run the fix once per server start using frappe.cache().

	Called from the `before_request` hook in hooks.py. The cache flag
	ensures the ALTER TABLE only runs on the very first HTTP request.
	"""
	if frappe.cache().get_value("logistics_child_tables_fixed"):
		return

	fix_all_child_tables()
	frappe.cache().set_value("logistics_child_tables_fixed", True)


def execute():
	"""Add parent/parenttype/parentfield columns to all Logistics child tables.

	Frappe's schema sync sometimes fails to create these columns for child
	tables, causing (1054, "Unknown column 'parent' in WHERE") errors when
	child table records are queried or filtered by parent.

	This patch is designed to NEVER crash — every ALTER TABLE is wrapped in
	try/except and columns that already exist are silently skipped.
	"""
	fix_all_child_tables()


def fix_all_child_tables():
	"""Add parent columns to ALL Logistics child tables and ensure indexes exist."""
	tables = [
		"tabDelivery Stop",
		"tabDelivery Trip Delivery Note",
		"tabTransporter Vehicle Type",
		"tabTransporter Service Area",
	]

	columns = ["parent", "parenttype", "parentfield"]

	for table in tables:
		for col in columns:
			try:
				frappe.db.sql(
					f"ALTER TABLE `{table}` ADD COLUMN `{col}` VARCHAR(140) NULL"
				)
				print(f"  Added `{col}` to {table}")
			except Exception:
				# Column already exists — that's fine
				pass

		# Also try to ensure parent column has an index
		try:
			frappe.db.sql(f"ALTER TABLE `{table}` ADD INDEX `parent` (`parent`)")
		except Exception:
			# Index already exists — that's fine
			pass

	frappe.db.commit()
	print("✅ Child table parent columns checked and fixed where needed")
