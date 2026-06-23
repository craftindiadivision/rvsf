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
            frappe.call({
                method: "rvsf.rvsf.doctype.gate_pass.gate_pass.check_physical_verification",
                args: {
                    gate_pass: frm.doc.name
                },
                callback: function(r) {
                    if (!r.message) {
                        frm.add_custom_button(__("Verify Documents"), function () {
                            frappe.model.open_mapped_doc({
                                method: "rvsf.rvsf.doctype.gate_pass.gate_pass.verify_documents",
                                frm: frm
                            });
                        });
                    }
                }
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
    if (slots.length === 0) {
        frappe.msgprint({
            title: __("Holiday"),
            message: __("The selected date is a holiday."),
            indicator: "orange"
        });
        return;
    }

    let slots_html = "";

    slots.forEach(slot => {
        const is_available = slot.available;
        const disabled_attr = is_available ? "" : "disabled";
        const fill_pct = slot.capacity > 0
            ? Math.round((slot.booked / slot.capacity) * 100)
            : 100;

        slots_html += `
            <button
                class="slot-btn"
                data-start="${slot.start_time}"
                data-end="${slot.end_time}"
                ${disabled_attr}
                style="
                    display: flex;
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 6px;
                    padding: 10px 12px;
                    border-radius: 8px;
                    border: 1px solid ${is_available ? "#d1d5db" : "#e5e7eb"};
                    background: ${is_available ? "#ffffff" : "#f9fafb"};
                    color: inherit;
                    min-width: 140px;
                    cursor: ${is_available ? "pointer" : "not-allowed"};
                    opacity: ${is_available ? "1" : "0.5"};
                    text-align: left;
                    transition: border-color 0.15s, background 0.15s;
                "
                onmouseover="${is_available ? "this.style.borderColor='#6b7280'; this.style.background='#f9fafb';" : ""}"
                onmouseout="${is_available ? "this.style.borderColor='#d1d5db'; this.style.background='#ffffff';" : ""}"
            >
                <span style="
                    font-size: 13px;
                    font-weight: 500;
                    color: #111827;
                    letter-spacing: 0.01em;
                ">
                    ${slot.start_time} &ndash; ${slot.end_time}
                </span>
                <span style="
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    font-size: 11px;
                    color: #6b7280;
                ">
                    <span style="
                        width: 36px;
                        height: 3px;
                        background: #e5e7eb;
                        border-radius: 2px;
                        overflow: hidden;
                        display: inline-block;
                        vertical-align: middle;
                    ">
                        <span style="
                            display: block;
                            height: 100%;
                            width: ${fill_pct}%;
                            border-radius: 2px;
                            background: ${is_available ? "#6b7280" : "#d1d5db"};
                        "></span>
                    </span>
                    ${slot.booked}/${slot.capacity} booked
                </span>
            </button>
        `;
    });

    const html = `
        <div style="padding: 4px 0 8px;">
            <div style="
                display: flex;
                align-items: center;
                gap: 16px;
                margin-bottom: 16px;
                padding-bottom: 12px;
                border-bottom: 1px solid #f3f4f6;
            ">
                <span style="display:flex;align-items:center;gap:5px;font-size:12px;color:#6b7280;">
                    <span style="width:8px;height:8px;border-radius:50%;background:#6b7280;display:inline-block;"></span>
                    Available
                </span>
                <span style="display:flex;align-items:center;gap:5px;font-size:12px;color:#9ca3af;">
                    <span style="width:8px;height:8px;border-radius:50%;background:#d1d5db;display:inline-block;"></span>
                    Fully booked
                </span>
            </div>
            <div style="
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            ">${slots_html}</div>
        </div>
    `;

    let dialog = new frappe.ui.Dialog({
        title: __("Select Time Slot"),
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "slot_html"
            }
        ]
    });

    dialog.show();
    dialog.fields_dict.slot_html.wrapper.innerHTML = html;

    $(dialog.fields_dict.slot_html.wrapper).on("click", ".slot-btn", function () {
        let start = $(this).data("start");
        let end = $(this).data("end");
        frm.set_value("start_time", start);
        frm.set_value("end_time", end);
        dialog.hide();
    });
}