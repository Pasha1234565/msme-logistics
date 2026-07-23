from __future__ import unicode_literals


def execute():
	"""Insert demo data by delegating to the canonical patch module."""
	from msme_logistics.patches.insert_demo_data.execute import execute as insert_demo_data

	insert_demo_data()
	print("Demo data patch completed")
