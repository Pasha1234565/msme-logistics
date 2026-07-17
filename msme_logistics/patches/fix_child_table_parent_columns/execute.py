from __future__ import unicode_literals

import frappe


def execute():
	"""Add parent/parenttype/parentfield columns to all Logistics child tables.

	Frappe's schema sync sometimes fails to create these columns for child
	tables, causing (1054, "Unknown column 'parent' in WHERE") errors when
	child table records are queried or filtered by parent.

	This patch is designed to NEVER crash — every ALTER TABLE is wrapped in
	try/except and columns that already exist are silently skipped.
	"""
	from . import fix_all_child_tables

	fix_all_child_tables()
