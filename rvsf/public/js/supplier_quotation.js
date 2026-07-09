frappe.ui.form.on("Supplier Quotation", {
    onload_post_render(frm) {
        if (frm.doc.custom_purchase_lead) {
            delete frm.custom_make_buttons["Quotation"];
            frm.remove_custom_button(__("Quotation"), __("Create"));
        }
    },
    after_workflow_action(frm) {
        if (frm.doc.workflow_state === "Rejected") {
            console.log("rejected")
            let d = new frappe.ui.Dialog({
                title: "Reason for Rejection",
                fields: [
                    {
                        label: "Reason",
                        fieldname: "reason",
                        fieldtype: "Small Text",
                        reqd: 1
                    }
                ],
                primary_action_label: "Submit",
                primary_action(values) {
                    frm.set_value(
                        "custom_reason_for_rejection",
                        values.reason
                    );
                    d.hide();
                    frappe.show_alert({
                        message: __("Rejection reason added"),
                        indicator: "green"
                    }, 5);
                }
            });
            d.show();
        }
        frappe.call({
            method: "rvsf.rvsf.events.supplier_quotation.update_supplier_quotation_status",
            args: {
                supplier_quotation:frm.doc.name
            }
        })
    }
})