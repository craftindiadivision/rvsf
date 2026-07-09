# Copyright (c) 2026, saheer and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class VehicleCategory(Document):
	@frappe.whitelist()
	def populate_months(self):
		if self.monthly_wise_scrap_valuation:
			return
		month_list = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]

		for idx, month in enumerate(month_list, start=1):
			self.append("monthly_wise_scrap_valuation", {
                "month": month,
                "idx": idx
            })

