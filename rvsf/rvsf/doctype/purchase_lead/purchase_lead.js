// Copyright (c) 2026, saheer and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Lead", {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.owner_name) {

            // Show Supplier button only if Supplier does not exist
                if (!frm.doc.supplier) {
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
                if (frm.doc.supplier && frm.doc.application_type === "Quotation Wise") {
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
                else if (frm.doc.application_type === "Direct Customer" && frm.doc.supplier) {
                    if (!frm.doc.is_vehicle_weighment_is_completed) {
                        frappe.db.exists("Gate Pass", {
                            purchase_lead: frm.doc.name
                        }).then((gate_pass_exists) => {

                            if (!gate_pass_exists) {
                                frm.add_custom_button(__("Gate Pass"), () => {
                                    frappe.model.open_mapped_doc({
                                        method: "rvsf.rvsf.doctype.purchase_lead.purchase_lead.make_gate_pass",
                                        frm: frm
                                    });
                                }, __("Create"));
                            }
                        });
                    }  
                    else if (frm.doc.is_vehicle_weighment_is_completed && frm.doc.application_type === "Direct Customer") { 
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
                }
        }
        set_district_query(frm);
    },
    state(frm) {
		frm.set_value("district", null);
		set_district_query(frm);
	},
    vehicle_registration_no: function(frm) {
        if (frm.doc.vehicle_registration_no) {
            frm.set_value(
                "vehicle_registration_no",
                frm.doc.vehicle_registration_no.toUpperCase().trim()
            );
        }
    }
});

function set_district_query(frm) {
	frm.set_query("district", function () {
		return {
			filters: {
				state: frm.doc.state
			}
		};
	});
}