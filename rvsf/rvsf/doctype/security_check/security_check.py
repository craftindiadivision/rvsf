# Copyright (c) 2026, saheer and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import getdate,get_time,now_datetime


class SecurityCheck(Document):
    def validate(self):
        if self.vehicle_no:
            existing_security_check = frappe.db.exists(
                "Security Check",
                {
                    "vehicle_no": self.vehicle_no,
                    "name": ["!=", self.name],
                    "docstatus":1
                }
            )

            if existing_security_check:
                frappe.throw(
                    f"Security Check <b>{existing_security_check}</b> already exists for this vehicle."
                )
    def on_submit(self):
        if self.clear_for_yard_entry_ == 0:
            frappe.throw(
                "The vehicle is pending yard entry clearance. Please complete the clearance process before proceeding."
            )
    def on_update(self):
        if (
            self.has_value_changed("workflow_state")
            and self.workflow_state == "Yard Entry Approved"
            and not self.clear_for_yard_entry_
        ):
            self.db_set("clear_for_yard_entry_", 1, update_modified=False)


    
@frappe.whitelist()
def make_physical_verification(source_name, target_doc=None):
    existing_sc = frappe.db.exists(
        "Security Check",
        {"security_check": source_name}
    )

    if existing_sc:
        frappe.throw(
            f"Security Check <b>{existing_sc}</b> already exists for Gate Pass <b>{source_name}</b>"
        )
    def set_missing_values(source, target):
        target.security_check = source.name
        target.gate_pass_no = source.gate_pass
        if frappe.db.exists("Gate Pass", source.gate_pass):
            gate_pass_doc = frappe.get_doc("Gate Pass", source.gate_pass)
            if gate_pass_doc.is_entry_pass_issued == 1:
                entry_pass = frappe.get_doc("Entry Pass", {"gate_pass_id": source.gate_pass})
                in_time = entry_pass.entry_time
                target.time_in = get_time(in_time)
        if source.purchase_lead:
            pl = frappe.get_doc("Purchase Lead", source.purchase_lead)
            target.purchase_lead = pl.name
            target.owner_name = pl.owner_name
            target.pan_no = pl.pan_number
            target.contact_number = pl.mobile_number
            if pl.supplier_address:
                target.supplier_address = pl.supplier_address
            target.chassis_number = pl.chassis_no
            target.engine_number = pl.engine_no
            target.maker_name = pl.maker_name
            target.model_name = pl.model_name
            target.fuel_type = pl.fuel_type
            target.aadhar_no = pl.aadhar_no
            target.weight_at_entry_bridge_unladen_weight = pl.rc_weight
    doc = get_mapped_doc(
        "Security Check",
        source_name,
        {
            "Security Check": {
                "doctype": "Physical Verification",
                "field_map": {
                    "company": "company",
                    "purchase_order": "purchase_order",
                    "cost_center": "cost_center",
                    "vehicle_no": "vehicle",
                    "supplier": "supplier",
                    "purchase_order": "purchase_order",
                },
                "field_no_map": [
                    "naming_series",
                    "workflow_state",
                ]
            }
        },
        target_doc,
        set_missing_values
    )

    return doc

@frappe.whitelist()
def get_security_verification_checklist_template_details(template):
    if not template:
        return []

    template_doc = frappe.get_doc(
        "Security Verification Checklist Template",
        template
    )

    questions = []

    for row in template_doc.inspection_questions:
        questions.append({
            "inspection_question": row.inspection_question,
        })

    return questions

@frappe.whitelist()
def set_inspector(docname):
    doc = frappe.get_doc("Security Check", docname)

    if doc.workflow_state == "Inspected" and not doc.inspector_id:
        doc.db_set("inspector_id", frappe.session.user, update_modified=False)
        doc.db_set("inspector", frappe.get_value("User", frappe.session.user, "full_name"), update_modified=False)