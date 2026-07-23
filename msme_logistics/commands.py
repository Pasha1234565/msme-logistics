from __future__ import unicode_literals


def insert_demo_data():
	"""Insert comprehensive demo data via the patch module.

	Creates transporters, customers, delivery trips with stops, and cost
	reconciliation records that feed into the SLA Compliance and Cost Per
	Delivery charts.

	Run via bench console:
		import msme_logistics.commands
		msme_logistics.commands.insert_demo_data()

	Or via bench execute:
		bench --site <your-site-name> execute msme_logistics.patches.insert_demo_data.execute
	"""
	from msme_logistics.patches.insert_demo_data.execute import execute

	execute()
