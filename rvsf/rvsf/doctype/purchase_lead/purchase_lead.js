// Copyright (c) 2026, saheer and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Lead", {
    refresh(frm) {
    if( !frm.is_new() && frm.doc.owner_name){
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
                        // frappe.set_route("Form", "Supplier", r.message);
                        frm.reload_doc();
                    }
                }
            });

        }, __("Create"));

        frappe.db.exists("Supplier", {
            supplier_name: frm.doc.owner_name
        }).then((exists) => {

            if (exists) {

                frm.add_custom_button(__("Supplier Quotation"), () => {

                    frappe.model.open_mapped_doc({
                        method: "rvsf.rvsf.doctype.purchase_lead.purchase_lead.make_supplier_quotation",
                        frm: frm
                    });

                }, __("Create"));
            }
        });

    }
    }

});
