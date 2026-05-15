import frappe


@frappe.whitelist()
def update_supplier_quotation_status(supplier_quotation):
    doc = frappe.get_doc("Supplier Quotation", supplier_quotation)
    purchase_lead = frappe.get_doc("Purchase Lead", doc.custom_purchase_lead)
    if not purchase_lead:
        return
    if doc.workflow_state == "Accepted":
        purchase_lead.db_set("status", "Accepted")
    elif doc.workflow_state == "Rejected":
        purchase_lead.db_set("status", "Rejected")
    elif doc.workflow_state == "Revised":
        purchase_lead.db_set("status", "Revised")
    elif doc.workflow_state == "Sent":
        purchase_lead.db_set("status", "Quotation Sent")
    elif doc.workflow_state == "Cancelled":
        purchase_lead.db_set("status", "Open")