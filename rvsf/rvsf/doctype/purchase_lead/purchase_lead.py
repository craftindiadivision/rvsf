# Copyright (c) 2026, saheer and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc	

class PurchaseLead(Document):
	pass

import frappe

@frappe.whitelist()
def make_supplier(source_name):

    doc = frappe.get_doc("Purchase Lead", source_name)

    # Create Supplier
    supplier = frappe.new_doc("Supplier")
    supplier.supplier_name = doc.owner_name
    supplier.supplier_type = "Individual"
    supplier.insert(ignore_permissions=True)

    # Create Address
    address = frappe.new_doc("Address")
    address.address_title = doc.owner_name
    address.address_type = "Billing"

    address.address_line1 = doc.address1
    address.address_line2 = (doc.address2 or "") + " " + (doc.address3 or "")
    address.city = doc.district
    address.state = doc.state
    address.pincode = doc.pin_code
    address.phone = doc.mobile_number
    address.email_id = doc.email_id
    address.is_your_company_address = 0
    address.append("links", {
        "link_doctype": "Supplier",
        "link_name": supplier.name
    })

    address.insert(ignore_permissions=True)
    return supplier.name

@frappe.whitelist()
def make_supplier_quotation(source_name):

    source_doc = frappe.get_doc("Purchase Lead", source_name)
    item_code = source_doc.vehicle_registration_no
    if frappe.db.exists("Supplier Quotation", {"custom_purchase_lead": source_doc.name}):
        frappe.throw("Supplier Quotation already exists for this Purchase Lead.")
    if not frappe.db.exists("Item", item_code):

        item = frappe.new_doc("Item")
        item.item_code = item_code
        item.item_name = source_doc.model_name
        item.item_group = "Vehicles"
        item.stock_uom = "Nos"
        item.custom_vehicle_category = source_doc.vehicle_category
        item.custom_maker_name = source_doc.maker_name
        item.custom_model_name = source_doc.model_name
        item.custom_monthyear_of_manufacture = source_doc.monthyear_of_manufacture
        item.custom_chassis_no = source_doc.chassis_no
        item.custom_engine_no = source_doc.engine_no
        item.custom_state_name = source_doc.state
        item.custom_rto_name = source_doc.rto_name
        item.custom_vehicle_registration_no = source_doc.vehicle_registration_no
        item.insert(ignore_permissions=True)
    supplier = frappe.db.get_value(
        "Supplier",
        {"supplier_name": source_doc.owner_name},
        "name"
    )
    def postprocess(source, target):

        target.supplier = supplier
        target.custom_purchase_lead = source.name
        supplier_address = frappe.db.get_value(
			"Address",
			{"address_title": source.owner_name},
			"name"
		)
        target.supplier_address = supplier_address
        target.append("items", {
            "item_code": source.vehicle_registration_no,
            "qty": 1,
            "uom": "Nos",
            "stock_uom": "Nos",
			"item_name": source.model_name
        })

    doc = get_mapped_doc(
        "Purchase Lead",
        source_name,
        {
            "Purchase Lead": {
                "doctype": "Supplier Quotation",
                "field_map": {
                    "name": "custom_lead"
                },
                "field_no_map": [
                "status"
                ]
            }
        },
        target_doc=None,
        postprocess=postprocess
    )

    return doc
    