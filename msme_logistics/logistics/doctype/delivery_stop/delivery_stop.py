from __future__ import unicode_literals

import frappe
from frappe.model.document import Document


def _generate_tracking_id():
	"""Generate a unique tracking ID in format TRK-XXXXXXXX (module-level for reuse)."""
	for _ in range(100):  # collision-retry loop
		tid = "TRK-" + frappe.generate_hash(length=8).upper()
		if not frappe.db.exists("Delivery Stop", {"tracking_id": tid}):
			return tid
	# Fallback: extremely unlikely to reach here
	frappe.throw(frappe._("Could not generate a unique tracking ID. Please try again."))


class DeliveryStop(Document):
	def before_insert(self):
		"""Auto-generate a unique customer-facing tracking ID."""
		if not self.tracking_id:
			self.tracking_id = _generate_tracking_id()
