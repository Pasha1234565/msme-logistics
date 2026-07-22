from __future__ import unicode_literals

import frappe

no_cache = 1


def get_context(context):
	"""Provide context for the /track web page.

	Prefills the tracking ID from the ?id= query parameter so that
	customers clicking a link like `/track?id=TRK-XXXXXXXX` see results
	immediately without re-typing.
	"""
	context.title = "Track Your Order"
	context.tracking_id = (frappe.form_dict.get("id") or "").strip().upper()
