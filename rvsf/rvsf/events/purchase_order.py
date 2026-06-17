import frappe
from frappe.model.mapper import get_mapped_doc

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