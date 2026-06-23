# Copyright (c) 2026, saheer and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CertificateOfDeposit(Document):
    def after_insert(self):
        if self.purchase_receipt and frappe.db.exists(
			"Purchase Receipt", self.purchase_receipt
		):
            frappe.db.set_value(
				"Purchase Receipt",
				self.purchase_receipt,
				"custom_certificate_of_deposit",
				self.name
			)
    def on_trash(self):
        if self.purchase_receipt and frappe.db.exists(
			"Purchase Receipt", self.purchase_receipt
		):
            frappe.db.set_value(
				"Purchase Receipt",
				self.purchase_receipt,
				"custom_certificate_of_deposit",
				None
			)