# Copyright (c) 2026, saheer and contributors
# For license information, please see license.txt

from tempfile import template

import frappe
from frappe.model.document import Document
from frappe.utils import getdate,get_time,now_datetime
from frappe.model.mapper import get_mapped_doc
from datetime import timedelta


class GatePass(Document):
	def on_submit(self):
		if not self.start_time or not self.end_time:
			frappe.throw("Please select a time slot before submitting.")
		self.db_set("status", "Issued")
	def on_cancel(self):
		self.db_set("status", "Cancelled")
@frappe.whitelist()
def get_available_slots(template, scheduled_date):
    template_doc = frappe.get_doc(
        "Time Slot Template",
        template
    )
    slots = []
    holiday = template_doc.holiday_list
    if holiday:
        holiday_dates = frappe.get_all(
            "Holiday",
            filters = {"parent": holiday},
            fields = ["holiday_date"]
        )
        holiday_dates = [getdate(h["holiday_date"]) for h in holiday_dates]
        if getdate(scheduled_date) in holiday_dates:
            return slots
    weekday = getdate(scheduled_date).strftime("%A")
    for row in template_doc.slot_details:
        if row.day != weekday:
            continue
        if getdate(scheduled_date) == now_datetime().date():
            current_time = timedelta(
                hours=now_datetime().hour,
                minutes=now_datetime().minute,
                seconds=now_datetime().second
            )

            if row.start_time <= current_time:
                continue
        booking_count = frappe.db.count(
            "Gate Pass",
            {
                "scheduled_date": scheduled_date,
                "start_time": row.start_time,
                "end_time": row.end_time,
                "docstatus": ["!=", 2]
            }
        )
        available = booking_count < row.capacity            
        slots.append({
            "start_time": str(row.start_time),
            "end_time": str(row.end_time),
            "capacity": row.capacity,
            "booked": booking_count,
            "available": available,
        })
    return slots

@frappe.whitelist()
def issue_gate_pass(gate_pass, session_user):
    if not frappe.db.exists("Gate Pass", gate_pass):
        return {"status": "error"}
    gate_pass = frappe.get_doc("Gate Pass", gate_pass)
    if gate_pass.workflow_state == "Issued":
        gate_pass.db_set("status", "Issued")
        gate_pass.db_set("issued_by", session_user)
        gate_pass.db_set(
            "issued_by_name",
            frappe.get_value("User", session_user, "full_name")
        )
        return {
            "status": "success",
            "message": "Gate Pass Issued"
        }
    elif gate_pass.workflow_state == "Valid":
        gate_pass.db_set("status", "Valid")
        gate_pass.db_set("verified_by", session_user)
        gate_pass.db_set(
            "verified_by_name",
            frappe.get_value("User", session_user, "full_name")
        )
        return {
            "status": "success",
            "message": "Gate Pass Validated"
        }
    elif gate_pass.workflow_state == "Invalid":
        gate_pass.db_set("status", "Invalid")
        gate_pass.db_set("verified_by", session_user)
        gate_pass.db_set(
            "verified_by_name",
            frappe.get_value("User", session_user, "full_name")
        )
        return {
            "status": "success",
            "message": "Gate Pass Invalidated"
        }
@frappe.whitelist()
def make_entry_pass(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.gate_pass = source.name
    entry_pass_exists = frappe.db.exists("Entry Pass", {"gate_pass_id": source_name})
    if entry_pass_exists:
        frappe.throw("An Entry Pass already exists for the selected Gate Pass.")
    doc = get_mapped_doc(
        "Gate Pass",
        source_name,
        {
            "Gate Pass": {
                "doctype": "Entry Pass",
                "field_map": {
                    "gate_pass_id": "name",
                    "vehicle": "vehicle",
                    "company": "company",
                    "cost_center": "cost_center",
                },
                "field_no_map": [
                "naming_series"
                ]
                
            }
        },
        target_doc,
        set_missing_values
    )
    return doc

@frappe.whitelist()
def check_physical_verification(gate_pass):
    return frappe.db.exists(
        "Physical Verification",
        {
            "gate_pass_no": gate_pass
        }
    )
    
@frappe.whitelist()
def verify_documents(source_name, target_doc=None):
    existing_pv = frappe.db.exists(
        "Physical Verification",
        {"gate_pass_no": source_name}
    )

    if existing_pv:
        frappe.throw(
            f"Physical Verification <b>{existing_pv}</b> already exists for Gate Pass <b>{source_name}</b>"
        )
    def set_missing_values(source, target):
        target.gate_pass_no = source.name
        if source.is_entry_pass_issued == 1:
            entry_pass = frappe.get_doc("Entry Pass", {"gate_pass_id": source.name})
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

    doc = get_mapped_doc(
        "Gate Pass",
        source_name,
        {
            "Gate Pass": {
                "doctype": "Physical Verification",
                "field_map": {
                    "company": "company",
                    "purchase_order": "purchase_order",
                    "cost_center": "cost_center",
                    "vehicle": "vehicle",
                    "supplier": "supplier",
                },
                "field_no_map": [
                    "naming_series",
                    "workflow_state",
                    "verified_by",
                    "verified_by_name"
                ]
            }
        },
        target_doc,
        set_missing_values
    )

    return doc