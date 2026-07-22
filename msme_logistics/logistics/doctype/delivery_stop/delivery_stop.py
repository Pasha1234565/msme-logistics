from __future__ import unicode_literals

import secrets
import string

import frappe
from frappe.model.document import Document


class DeliveryStop(Document):
	def before_insert(self):
		"""Auto-generate a unique customer-facing tracking ID."""
		if not self.tracking_id:
			self.tracking_id = self._generate_tracking_id()

	def _generate_tracking_id(self):
		"""Generate a unique tracking ID in format TRK-XXXXXXXX."""
		chars = string.ascii_uppercase + string.digits
		for _ in range(100):  # collision-retry loop
			tid = "TRK-" + "".join(secrets.choice(chars) for _ in range(8))
			if not frappe.db.exists("Delivery Stop", {"tracking_id": tid}):
				return tid
		# Fallback: extremely unlikely to reach here
		frappe.throw(frappe._("Could not generate a unique tracking ID. Please try again."))
