# Copyright (c) 2026, saheer and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import now_datetime

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

@frappe.whitelist()
def scan_entry_pass(entry_pass):
    if not entry_pass:
        frappe.throw(_("Entry Pass is required."))

    if not frappe.db.exists("Entry Pass", entry_pass):
        frappe.throw(_("Invalid Entry Pass: {0}").format(entry_pass))

    doc = frappe.get_doc("Entry Pass", entry_pass)

    # Prevent duplicate exit
    if doc.exit_time:
        frappe.throw(
            _("Vehicle has already exited on {0}.").format(doc.exit_time)
        )

    # Update exit details
    doc.exit_time = now_datetime()

    # Optional: if you have these fields
    if hasattr(doc, "exit_approved_by"):
        doc.exit_approved_by = frappe.session.user

    if hasattr(doc, "exit_approved_by_name"):
        doc.exit_approved_by_name = frappe.db.get_value(
            "User",
            frappe.session.user,
            "full_name"
        )

    # Optional status field
    if hasattr(doc, "status"):
        doc.status = "Exited"

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "entry_pass": doc.name,
        "vehicle": doc.vehicle,
        "customer": doc.visitor_name,
        "exit_time": doc.exit_time,
        "message": _("Vehicle exit recorded successfully.")
    }