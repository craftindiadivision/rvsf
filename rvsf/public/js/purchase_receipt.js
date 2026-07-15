frappe.ui.form.on("Purchase Receipt", {
     onload(frm) {

        if (
            frm.doc.docstatus === 0 &&
            frm.doc.custom_purchase_lead &&
            !frm.doc.custom_gross_weight
        ) {
            frm.events.get_purchase_receipt_weight_details(frm);
        }
    },

    get_purchase_receipt_weight_details(frm) {

        frappe.call({
            method: "rvsf.rvsf.events.purchase_receipt.get_purchase_receipt_weight_details",
            args: {
                purchase_lead: frm.doc.custom_purchase_lead,
                posting_date: frm.doc.posting_date
            },
            callback: function(r) {

                if (!r.message) return;

                frm.set_value("custom_rc_weight", r.message.custom_rc_weight);
                frm.set_value("custom_gross_weight", r.message.custom_gross_weight);
                frm.set_value("custom_scrap_cost_per_kg", r.message.custom_scrap_cost_per_kg);
                frm.set_value("custom_scrap_amount", r.message.custom_scrap_amount);
            }
        });

    },
    refresh(frm) {

        // Validation for new Purchase Receipt
        if (frm.is_new()) {
            const purchase_order = frm.doc.items?.[0]?.purchase_order;

            if (purchase_order) {
                frappe.call({
                    method: "rvsf.rvsf.events.purchase_receipt.check_purchase_order_for_receipt",
                    args: {
                        purchase_order
                    },
                    callback(r) {
                        if (!r.message.valid) {
                            frappe.msgprint(r.message.message);
                        }
                    }
                });
            }
        }

        // Create COD button for submitted Purchase Receipt
        if (frm.doc.docstatus === 1) {

            frappe.call({
                method: "rvsf.rvsf.events.purchase_receipt.can_create_cod",
                args: {
                    purchase_receipt: frm.doc.name
                },
                callback(r) {
                    if (r.message) {
                        frm.add_custom_button(__("Create COD"), () => {
                            frappe.model.open_mapped_doc({
                                method: "rvsf.rvsf.events.purchase_receipt.make_cod",
                                frm: frm
                            });
                        });
                    }
                }
            });
        }
    },
    custom_get_weight_details(frm) {
        if (frm.doc.docstatus !== 1) {
            frappe.call({
                method: "rvsf.rvsf.events.purchase_receipt.get_weight_details",
                args: {
                    purchase_lead: frm.doc.custom_purchase_lead,
                },
                callback: function(r) {
                    if (r.message) {
                        console.log(r.message.custom_rc_weight);

                        frm.set_value(
                            "custom_rc_weight",
                            r.message.custom_rc_weight || 0
                        );

                        frm.set_value(
                            "custom_gross_weight",
                            r.message.custom_gross_weight || 0
                        );
                    }
                }
            });
        }
    }
});