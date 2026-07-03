// Copyright (c) 2026, saheer and contributors
// For license information, please see license.txt

frappe.ui.form.on("Physical Verification", {
	refresh(frm) {
        frm.trigger("supplier_address");
        frappe.db.exists("Execution Order", {
            physical_verification_check_list: frm.doc.name
        }).then(exists => {
            if (!exists && frm.doc.authorized_by) {
                frm.add_custom_button(__("Create Execution Order"), function () {
                    frappe.model.open_mapped_doc({
                        method: "rvsf.rvsf.doctype.physical_verification.physical_verification.make_work_order",
                        frm: frm
                    });
                });
            }

        });
	},
    after_workflow_action(frm) {
        if (
            ["Inspected", "Verified", "Authorised"]
            .includes(frm.doc.workflow_state)
        ) {
            frappe.call({
                method: "rvsf.rvsf.doctype.physical_verification.physical_verification.update_workflow_details",
                args: {
                    physical_verification: frm.doc.name,
                    session_user: frappe.session.user
                },
                callback: function(r) {
                    if (r.message?.status === "success") {
                        frappe.show_alert({
                            message: __(r.message.message),
                            indicator: "green"
                        }, 5);

                        frm.reload_doc();
                        frm.refresh();
                    }
                }
            });
        }
    },
    supplier_address(frm) {
        if (!frm.doc.supplier_address) {
            frm.get_field("address").$wrapper.empty();
            return;
        }

        frappe.db.get_doc("Address", frm.doc.supplier_address)
            .then(addr => {
                let full_address = [
                    addr.address_line1,
                    addr.address_line2,
                    addr.city,
                    addr.state,
                    addr.pincode,
                    addr.country
                ]
                .filter(Boolean)
                .join("<br>");

                frm.get_field("address").$wrapper.html(`
                    <div style="padding:8px;border:1px solid #ddd;background:#f9f9f9;">
                        ${full_address}
                    </div>
                `);
            });
    },
    vehicle_condition_assessment_template(frm) {
        if (!frm.doc.vehicle_condition_assessment_template) return;
        frappe.call({
            method: "rvsf.rvsf.doctype.physical_verification.physical_verification.get_vehicle_assessment_template",
            args: {
                template: frm.doc.vehicle_condition_assessment_template
            },
            callback(r) {
                if (!r.message) return;

                frm.clear_table("vehicle_condition_assessment");

                r.message.forEach(item => {
                    let row = frm.add_child("vehicle_condition_assessment");
                    row.item = item.item_code
                });

                frm.refresh_field("vehicle_condition_assessment");
            }
        });
    }
});
