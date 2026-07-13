from __future__ import unicode_literals

import frappe
from frappe.model.document import Document


class Transporter(Document):
	def validate(self):
		self.validate_service_areas()
		self.validate_vehicle_types()

	def validate_service_areas(self):
		"""Ensure no overlapping pincode ranges in service areas."""
		if self.get("service_areas"):
			ranges = []
			for row in self.service_areas:
				pincode_from = row.pincode_from
				pincode_to = row.pincode_to or pincode_from

				if pincode_from and pincode_to:
					if int(pincode_from) > int(pincode_to):
						frappe.throw(
							frappe._("Pincode range is invalid: {0} to {1}. 'From' must be less than or equal to 'To'.").format(
								frappe.bold(pincode_from), frappe.bold(pincode_to)
							)
						)

					for existing_range in ranges:
						if not (int(pincode_to) < int(existing_range["from"]) or int(pincode_from) > int(existing_range["to"])):
							frappe.throw(
								frappe._("Service area range {0}-{1} overlaps with existing range {2}-{3}.").format(
									frappe.bold(pincode_from), frappe.bold(pincode_to),
									frappe.bold(existing_range["from"]), frappe.bold(existing_range["to"])
								)
							)

					ranges.append({"from": pincode_from, "to": pincode_to})

	def validate_vehicle_types(self):
		"""Ensure no duplicate vehicle types."""
		if self.get("vehicle_types"):
			types = []
			for row in self.vehicle_types:
				if row.vehicle_type in types:
					frappe.throw(
						frappe._("Vehicle type {0} is already defined. Please remove the duplicate.").format(
							frappe.bold(row.vehicle_type)
						)
					)
				types.append(row.vehicle_type)
