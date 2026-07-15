import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt,getdate


def on_submit(doc, method):
    if doc.grand_total > doc.custom_scrap_amount:
        frappe.throw("Purchase Cost cannot be greater than Scrap Amount.")
def validate_purchase_receipt(doc, method):
    if not doc.custom_purchase_lead:
        return
        
    purchase_order = next(
        (row.purchase_order for row in doc.items if row.purchase_order),
        None
    )
    if purchase_order:
        validate_purchase_order_for_receipt(purchase_order)
    if doc.custom_purchase_lead and flt(doc.custom_gross_weight) <= 0:
        frappe.throw("Gross Weight must be greater than 0.")
    if doc.custom_gross_weight > 0 :
        vehicle_category = frappe.db.get_value(
            "Purchase Lead",
            doc.custom_purchase_lead,
            "vehicle_category"
        )
        posting_date = getdate(doc.posting_date)
        month = posting_date.strftime("%B")
        scrap_rate = frappe.db.get_value(
            "Monthly Wise Scrap Valuation",
            {"parent": vehicle_category, "month": month},
            "per_kg_rate"
        )
        if not flt(scrap_rate):
            frappe.throw(
                ("Scrap Rate is not configured for Vehicle Category <b>{0}</b> for the month <b>{1}</b>. Please configure the Monthly Wise Scrap Valuation before proceeding.")
                .format(vehicle_category, month)
            )
        doc.custom_scrap_cost_per_kg = scrap_rate 
        scrap_amount = scrap_rate * doc.custom_gross_weight
        doc.custom_scrap_amount = scrap_amount

@frappe.whitelist()
def check_purchase_order_for_receipt(purchase_order):
    try:
        validate_purchase_order_for_receipt(purchase_order)
        return {
            "valid": True
        }
    except Exception as e:
        return {
            "valid": False,
            "message": str(e)
        }

def validate_purchase_order_for_receipt(purchase_order_from_item):
    po_doc = frappe.get_doc("Purchase Order", purchase_order_from_item)

    if not po_doc and purchase_order.custom_purchase_lead:
        return

    purchase_order = purchase_order_from_item
    gate_pass = frappe.db.get_value(
        "Gate Pass",
        {"purchase_order": purchase_order},
        "name"
    )

    if not gate_pass:
        frappe.throw("Cannot create Purchase Receipt. Gate Pass has not been created.")
        

    # 2. Physical Verification
    physical_verification = frappe.db.get_value(
        "Physical Verification",
        {"gate_pass_no": gate_pass},
        "name"
    )

    if not physical_verification:
        frappe.throw("Cannot create Purchase Receipt. Physical Verification has not been completed.")

    # 3. Execution Order
    execution_order = frappe.db.get_value(
        "Execution Order",
        {"physical_verification_check_list": physical_verification},
        "name"
    )

    if not execution_order:
        frappe.throw("Cannot create Purchase Receipt. Execution Order has not been created.")
        

    job_cards = frappe.get_all(
    "Execution Job Card",
    filters={
        "execution_order": execution_order,
        "is_recovery_operation": 0,
        "docstatus":1
    },
    fields=["name", "operation", "status"]
    )

    if not job_cards:
        frappe.throw("No non-recovery job cards found for the Execution Order.")

    incomplete_operations = [
        jc.operation
        for jc in job_cards
        if jc.status != "Completed"
    ]

    if incomplete_operations:
        frappe.throw(
            (
                "The following operations must be completed before creating Purchase Receipt: {0}"
            ).format(", ".join(incomplete_operations))
        )
    return True

@frappe.whitelist()
def can_create_cod(purchase_receipt):
    # COD already created
    if frappe.db.exists(
        "Certificate Of Deposit",
        {"purchase_receipt": purchase_receipt}
    ):
        return False

    purchase_invoice = frappe.db.get_value(
        "Purchase Invoice Item",
        {"purchase_receipt": purchase_receipt},
        "parent"
    )

    if not purchase_invoice:
        return False

    if frappe.db.get_value(
        "Purchase Invoice",
        purchase_invoice,
        "status"
    ) == "Paid":
        return True

    payment_request = frappe.db.exists(
        "Payment Request",
        {
            "reference_doctype": "Purchase Invoice",
            "reference_name": purchase_invoice,
            "docstatus": 1
        }
    )

    return bool(payment_request)
@frappe.whitelist()
def make_cod(source_name, target_doc=None):

    def set_missing_values(source, target):
        target.purchase_receipt = source.name

    doc = get_mapped_doc(
        "Purchase Receipt",
        source_name,
        {
            "Purchase Receipt": {
                "doctype": "Certificate Of Deposit",
                "field_map": {
                    "custom_purchase_lead": "purchase_lead"
                },
                "field_no_map": {
                    "naming_series"
                }
                
            }
        },
        target_doc,
        set_missing_values
    )

    return doc

@frappe.whitelist()
def get_weight_details(purchase_lead):

    rc_weight = 0
    gross_weight = 0

    if purchase_lead:
        rc_weight = frappe.db.get_value(
            "Purchase Lead",
            purchase_lead,
            "rc_weight"
        ) or 0
        execution_order = frappe.db.get_value(
            "Execution Order",
            {"purchase_lead": purchase_lead},
            "name"
        )

        if execution_order:
            job_cards = frappe.get_all(
                "Execution Job Card",
                filters={"execution_order": execution_order},
                fields=["weight"],
                order_by="creation desc"
            )

            for jc in job_cards:
                if flt(jc.weight) > 0:
                    gross_weight = jc.weight
                    break

    return {
        "custom_rc_weight": rc_weight,
        "custom_gross_weight": gross_weight
    }
    
@frappe.whitelist()
def get_purchase_receipt_weight_details(purchase_lead, posting_date):

    rc_weight = 0
    gross_weight = 0
    scrap_rate = 0
    scrap_amount = 0

    if not purchase_lead:
        return {}

    # RC Weight
    purchase_lead_doc = frappe.db.get_value(
        "Purchase Lead",
        purchase_lead,
        ["rc_weight", "vehicle_category"],
        as_dict=True
    )

    if purchase_lead_doc:
        rc_weight = purchase_lead_doc.rc_weight or 0
        vehicle_category = purchase_lead_doc.vehicle_category

        # Gross Weight
        execution_order = frappe.db.get_value(
            "Execution Order",
            {"purchase_lead": purchase_lead},
            "name"
        )

        if execution_order:
            job_cards = frappe.get_all(
                "Execution Job Card",
                filters={"execution_order": execution_order},
                fields=["weight"],
                order_by="creation desc"
            )

            for jc in job_cards:
                if flt(jc.weight) > 0:
                    gross_weight = flt(jc.weight)
                    break

        # Scrap Calculation
        if gross_weight > 0 and vehicle_category and posting_date:
            month = getdate(posting_date).strftime("%B")

            scrap_rate = flt(
                frappe.db.get_value(
                    "Monthly Wise Scrap Valuation",
                    {
                        "parent": vehicle_category,
                        "month": month
                    },
                    "per_kg_rate"
                )
            )

            scrap_amount = gross_weight * flt(scrap_rate)

    return {
        "custom_rc_weight": rc_weight,
        "custom_gross_weight": gross_weight,
        "custom_scrap_cost_per_kg": scrap_rate,
        "custom_scrap_amount": scrap_amount
    }