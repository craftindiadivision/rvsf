// Copyright (c) 2026, saheer and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Lead", {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.owner_name) {

            // Show Supplier button only if Supplier does not exist
            frappe.db.exists("Supplier", {
                supplier_name: frm.doc.owner_name
            }).then((supplier_exists) => {

                if (!supplier_exists) {
                    frm.add_custom_button(__("Supplier"), () => {
                        frappe.call({
                            method: "rvsf.rvsf.doctype.purchase_lead.purchase_lead.make_supplier",
                            args: {
                                source_name: frm.doc.name
                            },
                            freeze: true,
                            freeze_message: __("Creating Supplier..."),
                            callback: function(r) {
                                if (r.message) {
                                    frappe.show_alert({
                                        message: __("Supplier Created Successfully"),
                                        indicator: "green"
                                    }, 5);

                                    frm.reload_doc();
                                }
                            }
                        });
                    }, __("Create"));
                }

                // Show Supplier Quotation button only if Supplier exists
                // and no Supplier Quotation exists for this Purchase Lead
                if (supplier_exists) {
                    frappe.db.exists("Supplier Quotation", {
                        custom_purchase_lead: frm.doc.name
                    }).then((quotation_exists) => {

                        if (!quotation_exists) {
                            frm.add_custom_button(__("Supplier Quotation"), () => {
                                frappe.model.open_mapped_doc({
                                    method: "rvsf.rvsf.doctype.purchase_lead.purchase_lead.make_supplier_quotation",
                                    frm: frm
                                });
                            }, __("Create"));
                        }
                    });
                }
            });
        }
    }
});