import frappe
from frappe.model.mapper import get_mapped_doc

def on_submit(doc, method):
    if not doc.custom_purchase_lead:
        return

    gate_pass_exists = frappe.db.exists("Gate Pass", {"purchase_order": doc.name})
    if gate_pass_exists:
        return
    elif not gate_pass_exists:
        purchase_lead = frappe.get_doc("Purchase Lead", doc.custom_purchase_lead)
        if purchase_lead.application_type == "Direct Customer":
            gate_pass = frappe.db.get_value(
                "Gate Pass",
                {
                    "purchase_lead": purchase_lead.name,
                    "docstatus": 1
                },
                "name"
            )
            if gate_pass:   
                gate_pass_doc = frappe.get_doc("Gate Pass", gate_pass) 
                gate_pass_doc.db_set("purchase_order", doc.name)
            execution_order = frappe.db.get_value(
                "Execution Order",
                {
                    "purchase_lead": purchase_lead.name,
                    "docstatus": 1
                },
                "name"
            )
            if execution_order:
                frappe.get_doc("Execution Order", execution_order).db_set(
                    "purchase_order",
                    doc.name
                )

def on_cancel(doc, method):
    if not doc.custom_purchase_lead:
        return

    purchase_lead = frappe.get_doc("Purchase Lead", doc.custom_purchase_lead)

    if purchase_lead.application_type != "Direct Customer":
        return

    gate_pass = frappe.db.get_value(
        "Gate Pass",
        {
            "purchase_lead": purchase_lead.name,
            "purchase_order": doc.name,
            "docstatus": 1
        },
        "name"
    )

    if gate_pass:
        frappe.db.set_value(
            "Gate Pass",
            gate_pass,
            "purchase_order",
            None,
            update_modified=False
        )

    execution_order = frappe.db.get_value(
        "Execution Order",
        {
            "purchase_lead": purchase_lead.name,
            "purchase_order": doc.name,
            "docstatus": 1
        },
        "name"
    )

    if execution_order:
        frappe.db.set_value(
            "Execution Order",
            execution_order,
            "purchase_order",
            None,
            update_modified=False
        )
@frappe.whitelist()
def make_gate_pass(source_name, target_doc=None):
    def set_missing_values(source, target):
        item_code = source.items[0].item_code if source.items else None
        target.vehicle = item_code
        # supplier_quotation = source.items[0].supplier_quotation if source.items else None
        # target.supplier_quotation = supplier_quotation
        target.purchase_order = source.name
    gate_pass_exists = frappe.db.exists("Gate Pass", {"purchase_order": source_name})
    if gate_pass_exists:
        frappe.throw("A Gate Pass already exists for the selected Purchase Order.")
    doc = get_mapped_doc(
        "Purchase Order",
        source_name,
        {
            "Purchase Order": {
                "doctype": "Gate Pass",
                "field_map": {
                    "name": "purchase_order",
                    "company": "company",
                    "supplier": "supplier",
                    "posting_date": "posting_date",
                    "custom_purchase_lead": "purchase_lead",
                    "cost_center": "cost_center"
                },
                "field_no_map": [
                "naming_series","status"
                ]
                
            }
        },
        target_doc,
        set_missing_values
    )
    return doc