frappe.ui.form.on("Purchase Order", {
    refresh(frm) {
        if (frm.doc.docstatus === 1){
        frappe.db.exists("Gate Pass", {
            purchase_order: frm.doc.name
            }).then(exists => {
                if (!exists) {
                    frm.add_custom_button(__("Create Gate Pass"), function () {
                        frappe.model.open_mapped_doc({
                            method: "rvsf.rvsf.events.purchase_order.make_gate_pass",
                            frm: frm
                        });
                    });
                }

            });
        }
        frappe.db.get_value(
            "Purchase Lead",
            frm.doc.custom_purchase_lead,
            "application_type"
        ).then(r => {
            if (r.message.application_type === "Direct Customer") {
                frm.ignore_doctypes_on_cancel_all = [
                    "Gate Pass",
                    "Execution Order",
                    "Execution Job Card"
                ];
            }
        });
    }
})

// Reason for using ignore_doctypes_on_cancel_all:

// For the Direct Customer workflow, the Gate Pass is created independently before the Purchase Order.
//  The Purchase Order is only linked later for commercial tracking and is not the owner of the Gate Pass.
//   Therefore, during Purchase Order cancellation,
//    ignore_doctypes_on_cancel_all is used to suppress the 
//    linked-document cancellation dialog, following the same design pattern used by ERPNext's Quality Inspection.