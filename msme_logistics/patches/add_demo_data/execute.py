from __future__ import unicode_literals

import frappe


def execute():
	"""Insert demo data by delegating to commands.py."""
	from msme_logistics.commands import insert_demo_data

	insert_demo_data()
	print("Demo data patch completed")
