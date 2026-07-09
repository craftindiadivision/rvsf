# Copyright (c) 2026, saheer and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class PhysicalVerification(Document):
	pass

@frappe.whitelist()
def update_workflow_details(physical_verification, session_user):
    if not frappe.db.exists("Physical Verification", physical_verification):
        return {"status": "error"}

    doc = frappe.get_doc("Physical Verification", physical_verification)

    if doc.workflow_state == "Inspected":
        doc.db_set("inspected_by", session_user)
        doc.db_set("inspected_by_name", frappe.get_value("User", session_user, "full_name"))

        return {
            "status": "success",
            "message": "Vehicle Inspected"
        }

    elif doc.workflow_state == "Verified":
        doc.db_set("verified_by", session_user)
        doc.db_set("verified_by_name", frappe.get_value("User", session_user, "full_name"))

        return {
            "status": "success",
            "message": "Vehicle Verified"
        }
    elif doc.workflow_state == "Authorised":
        doc.db_set("authorized_by", session_user)
        doc.db_set("authorized_by_name", frappe.get_value("User", session_user, "full_name"))
        return {
            "status": "success",
            "message": "Vehicle Authorized"
        }

    return {"status": "error"}

@frappe.whitelist()
def make_work_order(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.vehicle = source.vehicle
        target.supplier = source.supplier

    doclist = get_mapped_doc(
        "Physical Verification",
        source_name,
        {
            "Physical Verification": {
                "doctype": "Execution Order",
                "field_map": {
                    "name": "physical_verification_check_list",
                    "purchase_order": "purchase_order",
                    "purchase_lead": "purchase_lead",
                    "cost_center": "cost_center",
                    "company": "company",
                    "vehicle": "vehicle",
                    "supplier": "supplier"
                },
                "field_no_map": {
                    "naming_series"
                }
            }
        },
        target_doc,
        set_missing_values
    )

    return doclist

@frappe.whitelist()
def get_vehicle_assessment_template(template):
    if not frappe.db.exists("Vehicle Condition Assessment Template", template):
        return
    doc = frappe.get_doc("Vehicle Condition Assessment Template", template)

    data = []

    for row in doc.vehicle_condition_assessment_items:
        data.append({
            "item_code": row.item_code
        })

    return data