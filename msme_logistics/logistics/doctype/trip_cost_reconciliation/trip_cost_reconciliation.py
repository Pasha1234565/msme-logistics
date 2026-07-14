from __future__ import unicode_literals

import frappe
from frappe.model.document import Document


class TripCostReconciliation(Document):
	def validate(self):
		self.calculate_costs()

	def calculate_costs(self):
		"""Compute total_stops and cost_per_stop based on linked Delivery Trip."""
		if self.delivery_trip:
			stop_count = frappe.db.count(
				"Delivery Stop",
				{"parenttype": "Delivery Trip", "parent": self.delivery_trip},
			)
			self.total_stops = stop_count

			total_cost = (self.fuel_cost or 0) + (self.transporter_payout or 0)
			self.cost_per_stop = round(total_cost / stop_count, 2) if stop_count > 0 else 0
