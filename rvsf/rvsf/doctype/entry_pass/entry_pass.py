# Copyright (c) 2026, saheer and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EntryPass(Document):
	def validate(self):
		if not self.gate_pass_id:
			return
		gate_pass = self.gate_pass_id
		exist = frappe.db.exists("Entry Pass", {"gate_pass_id": gate_pass, "name": ["!=", self.name]})
		if exist:
			frappe.throw("An Entry Pass already exists for the selected Gate Pass.")
	def after_insert(self):
		if not self.gate_pass_id:
			return
		if frappe.db.exists("Gate Pass", self.gate_pass_id):
			frappe.db.set_value(
				"Gate Pass",
				self.gate_pass_id,
				{
					"is_entry_pass_issued": 1
				}
			)
	def after_delete(self):
		if not self.gate_pass_id:
			return
		if frappe.db.exists("Gate Pass", self.gate_pass_id):
			frappe.db.set_value(
				"Gate Pass",
				self.gate_pass_id,
				{
					"is_entry_pass_issued": 0
				}
			)