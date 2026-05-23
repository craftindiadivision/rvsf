// Copyright (c) 2026, saheer and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Gate Pass", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("Gate Pass", {
    refresh(frm) {
        if (frm.doc.docstatus === 0) {
        frm.add_custom_button(
            __("Select Time Slot"),
            function () {
                if (!frm.doc.scheduled_date) {
                    frappe.msgprint({
                        title: __("Mandatory"),
                        message: __("Please select Scheduled Date"),
                        indicator: "red"
                    });
                    return;
                }
                if (!frm.doc.time_slot_template) {
                    frappe.msgprint({
                        title: __("Mandatory"),
                        message: __("Please select Time Slot Template"),
                        indicator: "red"
                    });
                    return;
                }
                frappe.call({
                    method: "rvsf.rvsf.doctype.gate_pass.gate_pass.get_available_slots",
                    args: {
                        template: frm.doc.time_slot_template,
                        scheduled_date: frm.doc.scheduled_date
                    },
                    callback: function(r) {
                        show_slot_dialog(frm, r.message);
                    }
                });
            }
        );
    }
        else if (frm.doc.docstatus === 1 && frm.doc.status === "Valid" && !frm.doc.is_entry_pass_issued) {
            frm.add_custom_button(__("Entry Pass"), function () {
                frappe.model.open_mapped_doc({
                    method: "rvsf.rvsf.doctype.gate_pass.gate_pass.make_entry_pass",
                    frm: frm
                });
            });
        }
    if (frm.doc.docstatus === 1 && frm.doc.status === "Valid" && frm.doc.is_entry_pass_issued){
            frm.add_custom_button(__("Verify Documents"), function () {
                frappe.model.open_mapped_doc({
                    method: "rvsf.rvsf.doctype.gate_pass.gate_pass.verify_documents",
                    frm: frm
                });
            });
        }
    },
    after_workflow_action(frm) {
            if (
                ["Issued", "Valid", "Invalid"]
                .includes(frm.doc.workflow_state)
            ) {
                frappe.call({
                    method: "rvsf.rvsf.doctype.gate_pass.gate_pass.issue_gate_pass",
                    args: {
                        gate_pass: frm.doc.name,
                        session_user: frappe.session.user
                    },
                    callback: function(r) {
                        if (r.message?.status === "success") {
                            frappe.show_alert({
                                message: __(r.message.message),
                                indicator: "green"
                            }, 5);
                            frm.reload_doc();
                        }
                    }
                });
            }
        }
});
function show_slot_dialog(frm, slots) {
    let html = `
        <div style="
            display:flex;
            flex-wrap:wrap;
            gap:10px;
        ">
    `;
    if (slots.length === 0) {
        frappe.msgprint({
            title: __("Holiday"),
            message: __("The selected date is a holiday."),
            indicator: "orange"
        });
        return;
    }
    slots.forEach(slot => {
        let disabled = slot.available ? "" : "disabled";
        let color = slot.available
            ? "#28a745"
            : "#dc3545";
        let label = `
            ${slot.start_time} - ${slot.end_time}
            <br>
            ${slot.booked}/${slot.capacity}
        `;
        html += `
            <button
                class="slot-btn btn btn-sm"
                data-start="${slot.start_time}"
                data-end="${slot.end_time}"
                style="
                    border:none;
                    padding:15px;
                    border-radius:10px;
                    background:${color};
                    color:white;
                    min-width:160px;
                    cursor:pointer;
                "
                ${disabled}
            >
                ${label}
            </button>
        `;
    });
    html += `</div>`;
    let dialog = new frappe.ui.Dialog({
        title: "Select Time Slot",
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "slot_html"
            }
        ]
    });
    dialog.show();
    dialog.fields_dict.slot_html.wrapper.innerHTML = html;
    $(dialog.fields_dict.slot_html.wrapper).on("click", ".slot-btn", function() {
        let start = $(this).data("start");
        let end = $(this).data("end");
        frm.set_value("start_time", start);
        frm.set_value("end_time", end);
        dialog.hide();
    });
}