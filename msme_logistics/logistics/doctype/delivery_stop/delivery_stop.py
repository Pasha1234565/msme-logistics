from __future__ import unicode_literals

import frappe
from frappe.model.document import Document


class DeliveryStop(Document):
	def before_insert(self):
		"""Auto-generate a unique customer-facing tracking ID (fallback)."""
		if not self.tracking_id:
			self.tracking_id = _generate_tracking_id()


def _generate_tracking_id():
	"""Generate a unique tracking ID in format TRK-XXXXXXXX using frappe built-ins."""
	for _ in range(100):
		tid = "TRK-" + frappe.generate_hash(length=8).upper()
		if not frappe.db.exists("Delivery Stop", {"tracking_id": tid}):
			return tid
	return "TRK-" + frappe.generate_hash(length=8).upper()
