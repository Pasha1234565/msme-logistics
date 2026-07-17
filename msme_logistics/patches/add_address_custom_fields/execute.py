from __future__ import unicode_literals

import frappe


def execute():
	"""Add missing ERPNext custom fields to the Address doctype.

	ERPNext's Address controller (erpnext/accounts/custom/address.py)
	references custom fields like `is_your_company_address` that are
	supposed to be created by ERPNext's fixture/custom field sync.
	If that sync doesn't happen (e.g. on a fresh install), these
	fields are missing and causing AttributeError when saving any
	document that creates an address (e.g. Customer with inline address).

	This patch ensures the missing fields exist.
	"""
	create_custom_field(
		doctype="Address",
		fieldname="is_your_company_address",
		label="Is Your Company Address",
		fieldtype="Check",
		default=0,
		insert_after="is_shipping_address",
		print_hide=1,
	)

	print("✅ Added missing ERPNext custom fields to Address doctype")


def create_custom_field(
	doctype, fieldname, label, fieldtype, default=None, insert_after=None, **kwargs
):
	"""Create a Custom Field if it doesn't already exist."""
	if frappe.db.exists("Custom Field", f"{doctype}-{fieldname}"):
		print(f"  ℹ️  Custom Field '{doctype}-{fieldname}' already exists")
		return

	custom_field = frappe.get_doc(
		{
			"doctype": "Custom Field",
			"dt": doctype,
			"fieldname": fieldname,
			"label": label,
			"fieldtype": fieldtype,
			"default": default,
			"insert_after": insert_after,
			**kwargs,
		}
	)
	custom_field.flags.ignore_permissions = True
	custom_field.flags.ignore_validate = True
	custom_field.insert()
	frappe.db.commit()
	print(f"  ✅ Created Custom Field '{doctype}-{fieldname}'")
