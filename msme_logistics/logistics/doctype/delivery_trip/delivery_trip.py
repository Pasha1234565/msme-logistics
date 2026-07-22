from __future__ import unicode_literals

#import std lib

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, get_url

from msme_logistics.logistics.doctype.delivery_stop.delivery_stop import _generate_tracking_id


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

	def _get_dispatch_user(self):
		"""Return the first enabled Dispatch Manager user, or fallback to current user."""
		users = frappe.db.get_all(
			"User",
			filters=[
				["User", "enabled", "=", 1],
				["Has Role", "role", "=", "Dispatch Manager"],
			],
			limit=1,
			pluck="name",
		)
		return users[0] if users else frappe.session.user

	def on_update(self):
		"""Trigger notifications and log status changes on delivery stops.

		On first save (new trip):
		- Generate tracking IDs for any stop missing one
		- Notify Dispatch Manager with tracking links for all new stops

		On subsequent saves:
		- Detect newly added stops → generate tracking ID → notify tracking links
		- Detect status changes → log to Delivery Status Log
		- Notify on failed deliveries
		"""
		prev_doc = self.get_doc_before_save()

		# Resolve dispatch user once to avoid repeated queries
		target_user = self._get_dispatch_user()

		if not prev_doc:
			# First save — all stops are new
			if self.get("delivery_stops"):
				for stop in self.delivery_stops:
					self._ensure_tracking_id(stop)
					if stop.tracking_id:
						self._notify_tracking_id(stop, target_user)
			return

		# Build lookup of previous stop statuses by sequence_no
		prev_status = {}
		if prev_doc.get("delivery_stops"):
			for stop in prev_doc.delivery_stops:
				prev_status[stop.sequence_no] = stop.status

		if self.get("delivery_stops"):
			for stop in self.delivery_stops:
				self._ensure_tracking_id(stop)
				prev = prev_status.get(stop.sequence_no)
				if prev is None:
					# New stop added — notify tracking ID
					if stop.tracking_id:
						self._notify_tracking_id(stop, target_user)
				elif prev != stop.status:
					# Log the status change
					self._log_status_change(stop)
					# Notify on failed deliveries
					if stop.status == "Failed":
						self.notify_delivery_failed(stop)

	def _ensure_tracking_id(self, stop):
		"""Generate a tracking ID for this stop if it doesn't have one.

		Child-table before_insert does not fire reliably during parent doc save
		in Frappe v15, so this method provides a fallback that always runs
		in the parent's on_update (which always fires).
		"""
		if not stop.tracking_id:
			tid = _generate_tracking_id()
			stop.tracking_id = tid
			# Persist directly so it's available even if stop obj isn't re-fetched
			frappe.db.set_value(
				"Delivery Stop", stop.name, "tracking_id", tid,
				update_modified=False
			)

	def _log_status_change(self, stop):
		"""Append a timestamped entry to Delivery Status Log for this stop."""
		log = frappe.new_doc("Delivery Status Log")
		log.parent = stop.name
		log.parenttype = "Delivery Stop"
		log.parentfield = "delivery_status_logs"
		log.status = stop.status
		log.location_label = stop.get("current_location_label", "")
		log.timestamp = now_datetime()
		log.flags.ignore_permissions = True
		log.insert()

	def _notify_tracking_id(self, stop, target_user):
		"""Create System Notification with tracking ID link for dispatch staff."""
		site_url = get_url()
		tracking_link = "{0}/track?id={1}".format(site_url, stop.tracking_id)

		notification = frappe.new_doc("Notification Log")
		notification.for_user = target_user
		notification.title = frappe._("New Tracking ID Generated")
		notification.subject = frappe._(
			"Tracking ID {0} generated for Stop #{1} (Customer: {2}). "
			"Share with customer: {3}"
		).format(
			stop.tracking_id,
			stop.sequence_no,
			stop.customer,
			tracking_link,
		)
		notification.document_type = "Delivery Trip"
		notification.document_name = self.name
		notification.insert(ignore_permissions=True)

	def notify_delivery_failed(self, stop):
		"""Create System Notification for failed delivery."""
		target_user = self._get_dispatch_user()

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
