from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class DeliveryTrip(Document):
	def validate(self):
		self.validate_delivery_stops()
		self.validate_pod_on_completion()

	def on_submit(self):
		self.set_actual_dispatch_time()

	def validate_delivery_stops(self):
		"""Ensure unique sequence numbers and at least one stop."""
		if not self.get("delivery_stops") or len(self.delivery_stops) == 0:
			frappe.throw(
				frappe._("At least one delivery stop is required before submitting.")
			)

		sequences = []
		for stop in self.delivery_stops:
			if stop.sequence_no in sequences:
				frappe.throw(
					frappe._("Duplicate sequence number {0} in delivery stops.").format(
						frappe.bold(stop.sequence_no)
					)
				)
			sequences.append(stop.sequence_no)

	def validate_pod_on_completion(self):
		"""Block transition to Completed if any Delivered stop is missing POD image.

		This enforces the rule: no completed trip without proof of delivery.
		"""
		prev_doc = self.get_doc_before_save()
		if prev_doc and prev_doc.trip_status == self.trip_status:
			return

		if self.trip_status == "Completed" and self.get("delivery_stops"):
			missing_pod = [
				"#{0} ({1})".format(stop.sequence_no, stop.customer)
				for stop in self.delivery_stops
				if stop.status == "Delivered" and not stop.pod_image
			]
			if missing_pod:
				frappe.throw(
					frappe._(
						"Cannot complete trip: Proof of Delivery (POD) image is missing "
						"for the following delivered stops: {0}. "
						"Please upload POD images before completing the trip."
					).format(", ".join(str(s) for s in missing_pod)),
					title=frappe._("POD Missing"),
				)

	def set_actual_dispatch_time(self):
		"""Record actual dispatch time on submit."""
		self.db_set("actual_dispatch_time", now_datetime())

	def before_update_after_submit(self):
		"""Track arrival times when stops are updated."""
		self.update_stop_arrival_times()

	def update_stop_arrival_times(self):
		"""Auto-set actual_arrival_time when a stop status changes to Delivered."""
		for stop in self.get("delivery_stops"):
			if stop.status == "Delivered" and not stop.actual_arrival_time:
				stop.actual_arrival_time = now_datetime()

	def on_update(self):
		"""Trigger notification for failed deliveries.

		Compares current and previous child table rows to detect
		stops whose status changed to Failed.
		"""
		prev_doc = self.get_doc_before_save()
		if not prev_doc:
			return

		# Build lookup of previous stop statuses by sequence_no
		prev_status = {}
		if prev_doc.get("delivery_stops"):
			for stop in prev_doc.delivery_stops:
				prev_status[stop.sequence_no] = stop.status

		if self.get("delivery_stops"):
			for stop in self.delivery_stops:
				prev = prev_status.get(stop.sequence_no)
				if stop.status == "Failed" and prev != "Failed":
					self.notify_delivery_failed(stop)

	def notify_delivery_failed(self, stop):
		"""Create System Notification for failed delivery."""
		# Find a user with Dispatch Manager role
		dispatch_users = frappe.db.get_all(
			"User",
			filters=[
				["User", "enabled", "=", 1],
				["Has Role", "role", "=", "Dispatch Manager"],
			],
			limit=1,
			pluck="name",
		)
		target_user = dispatch_users[0] if dispatch_users else frappe.session.user

		notification = frappe.new_doc("Notification Log")
		notification.for_user = target_user
		notification.title = frappe._("Delivery Failed")
		notification.subject = frappe._(
			"Delivery failed at stop #{0}: {1} (Customer: {2}). "
			"Trip: {3}, Transporter: {4}"
		).format(
			stop.sequence_no,
			stop.address or "N/A",
			stop.customer,
			self.name,
			self.transporter,
		)
		notification.document_type = "Delivery Trip"
		notification.document_name = self.name
		notification.insert(ignore_permissions=True)
