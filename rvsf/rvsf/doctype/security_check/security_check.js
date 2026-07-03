// Copyright (c) 2026, saheer and contributors
// For license information, please see license.txt

frappe.ui.form.on("Security Check", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }
        frappe.db.exists("Physical Verification", {
            security_check: frm.doc.name
        }).then((exists) => {
            if (!exists && frm.doc.docstatus === 1) {
                frm.add_custom_button(__("Physical Verification"), function () {
                    frappe.model.open_mapped_doc({
                        method: "rvsf.rvsf.doctype.security_check.security_check.make_physical_verification",
                        frm: frm
                    });
                });
            }
        });
    },
    security_verification_checklist_template(frm) {
        if (!frm.doc.security_verification_checklist_template) {
            frm.clear_table("security_verification_form");
            frm.refresh_field("security_verification_form");
            return;
        }

        frappe.call({
            method: "rvsf.rvsf.doctype.security_check.security_check.get_security_verification_checklist_template_details",
            args: {
                template: frm.doc.security_verification_checklist_template
            },
            callback: function(r) {
                if (r.message) {
                    frm.clear_table("security_verification_form");

                    r.message.forEach(function(d) {
                        let row = frm.add_child("security_verification_form");
                        row.inspection_question = d.inspection_question;
                    });

                    frm.refresh_field("security_verification_form");
                }
            }
        });
    },
    after_workflow_action(frm) {
        if (frm.doc.workflow_state === "Inspected" && !frm.doc.inspector_id) {
            frappe.call({
                method: "rvsf.rvsf.doctype.security_check.security_check.set_inspector",
                args: {
                    docname: frm.doc.name
                },
                callback: function() {
                    frm.reload_doc();
                }
            });
        }
    }
});

