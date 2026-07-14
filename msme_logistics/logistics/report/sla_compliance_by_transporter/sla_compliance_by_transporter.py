from __future__ import unicode_literals

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart(data)

	return columns, data, None, chart


def get_columns():
	return [
		{"label": _("Transporter"), "fieldname": "transporter", "fieldtype": "Link", "options": "Transporter", "width": 180},
		{"label": _("Trip"), "fieldname": "trip", "fieldtype": "Link", "options": "Delivery Trip", "width": 150},
		{"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 150},
		{"label": _("Delivery Window"), "fieldname": "delivery_window", "fieldtype": "Data", "width": 150},
		{"label": _("Actual Arrival"), "fieldname": "actual_arrival_time", "fieldtype": "Datetime", "width": 160},
		{"label": _("Within SLA"), "fieldname": "within_sla", "fieldtype": "Data", "width": 100},
		{"label": _("Delay (mins)"), "fieldname": "delay_mins", "fieldtype": "Int", "width": 100},
	]


def get_data(filters):
	conditions = []
	params = {}

	if filters.get("transporter"):
		conditions.append("dt.transporter = %(transporter)s")
		params["transporter"] = filters["transporter"]

	if filters.get("from_date"):
		conditions.append("dt.trip_date >= %(from_date)s")
		params["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("dt.trip_date <= %(to_date)s")
		params["to_date"] = filters["to_date"]

	where_clause = " AND ".join(conditions) if conditions else "1=1"

	data = frappe.db.sql(f"""
		SELECT
			dt.transporter,
			dt.name as trip,
			ds.customer,
			CONCAT(
				COALESCE(TIME_FORMAT(ds.delivery_window_start, '%%H:%%i'), 'N/A'),
				' - ',
				COALESCE(TIME_FORMAT(ds.delivery_window_end, '%%H:%%i'), 'N/A')
			) as delivery_window,
			ds.actual_arrival_time,
			CASE
				WHEN ds.status = 'Delivered' AND ds.actual_arrival_time IS NOT NULL
					AND ds.delivery_window_start IS NOT NULL
					AND TIME(ds.actual_arrival_time) <= ds.delivery_window_end
				THEN 'Yes'
				WHEN ds.status = 'Delivered' AND ds.actual_arrival_time IS NOT NULL
					AND ds.delivery_window_start IS NOT NULL
				THEN 'No'
				ELSE 'N/A'
			END as within_sla,
			CASE
				WHEN ds.status = 'Delivered' AND ds.actual_arrival_time IS NOT NULL
					AND ds.delivery_window_end IS NOT NULL
					AND TIME(ds.actual_arrival_time) > ds.delivery_window_end
				THEN TIMESTAMPDIFF(MINUTE,
					CONCAT(CURDATE(), ' ', ds.delivery_window_end),
					CONCAT(CURDATE(), ' ', TIME(ds.actual_arrival_time))
				)
				ELSE 0
			END as delay_mins
		FROM `tabDelivery Stop` ds
		INNER JOIN `tabDelivery Trip` dt ON dt.name = ds.parent AND ds.parenttype = 'Delivery Trip'
		WHERE {where_clause}
		ORDER BY dt.transporter, dt.name, ds.sequence_no
	""", params, as_dict=True)

	return data


def get_chart(data):
	if not data:
		return None

	transporter_sla = {}
	for row in data:
		if row.transporter not in transporter_sla:
			transporter_sla[row.transporter] = {"on_time": 0, "total": 0}
		if row.within_sla == "Yes":
			transporter_sla[row.transporter]["on_time"] += 1
		if row.within_sla in ("Yes", "No"):
			transporter_sla[row.transporter]["total"] += 1

	labels = list(transporter_sla.keys())
	on_time_pcts = []
	for t in labels:
		stats = transporter_sla[t]
		pct = round((stats["on_time"] / stats["total"]) * 100, 1) if stats["total"] > 0 else 0
		on_time_pcts.append(pct)

	return {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": _("SLA Compliance %"),
					"values": on_time_pcts,
				}
			],
		},
		"type": "bar",
		"colors": ["#2490ef"],
		"bar_options": {"stacked": 0},
	}
