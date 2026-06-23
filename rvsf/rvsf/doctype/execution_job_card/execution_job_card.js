// Copyright (c) 2026, saheer and contributors
// For license information, please see license.txt

frappe.ui.form.on("Execution Job Card", {

    refresh(frm) {

        frm.trigger("setup_timer");

        frm.clear_custom_buttons();

        // START JOB
        if (
            frm.doc.docstatus === 0 &&
            (!frm.doc.status || frm.doc.status === "Open")
        ) {

            frm.add_custom_button(__("Start Job"), function () {
                console.log("Start Job");
                frm.trigger("open_employee_dialog");
            });
        }

        // RESUME JOB
        if (
            frm.doc.docstatus === 0 &&
            frm.doc.status === "On Hold"
        ) {

            frm.add_custom_button(__("Resume Job"), async function () {

                await frappe.call({

                    method: "rvsf.rvsf.doctype.execution_job_card.execution_job_card.resume_job",

                    args: {
                        docname: frm.doc.name
                    }
                });

                frm.reload_doc();
            });
        }

        // PAUSE JOB
        if (
            frm.doc.docstatus === 0 &&
            frm.doc.status === "Work In Progress" && !frm.doc.actual_end_date
        ) {

            frm.add_custom_button(__("Pause Job"), async function () {

                await frappe.call({
                    method: "rvsf.rvsf.doctype.execution_job_card.execution_job_card.pause_job",
                    args: {
                        docname: frm.doc.name
                    }
                });

                frm.reload_doc();
            });
        }

        // FINISH JOB
        if (
            frm.doc.docstatus === 0 &&
            frm.doc.status === "Work In Progress" && !frm.doc.actual_end_date
        ) {

            frm.add_custom_button(__("Finish Job"), function () {

                frappe.confirm(
                    "Are you sure you want to finish this Job?",
                    async () => {

                        await frappe.call({
                            method: "rvsf.rvsf.doctype.execution_job_card.execution_job_card.finish_job",
                            args: {
                                docname: frm.doc.name
                            }
                        });

                        frm.reload_doc();
                    }
                );
            });
        }
    },

    open_employee_dialog(frm) {

        let dialog = new frappe.ui.Dialog({

            title: __("Select Employees"),

            fields: [
                {
                    fieldname: "employees",
                    fieldtype: "Table MultiSelect",
                    label: __("Employees"),
                    options: "Assign Employee",
                    reqd: 1
                }
            ],

            primary_action_label: __("Start Job"),

            primary_action: async function(values) {

                if (!values.employees || !values.employees.length) {

                    frappe.msgprint(__("Please select Employees"));

                    return;
                }

                // prepare employee list
                let employees = values.employees.map(row => row.employee);

                // clear existing rows
                frm.clear_table("employee");

                // add selected employees into child table
                employees.forEach(employee => {

                    let child = frm.add_child("employee");

                    child.employee = employee;
                });

                frm.refresh_field("employee");

                await frm.save();

                await frappe.call({

                    method: "rvsf.rvsf.doctype.execution_job_card.execution_job_card.start_job",

                    args: {
                        docname: frm.doc.name,
                        employees: JSON.stringify(employees)
                    }
                });

                dialog.hide();

                frm.reload_doc();
            }
        });

        dialog.show();
    },
    setup_timer(frm) {

        if (frm.timer_interval) {
            clearInterval(frm.timer_interval);
        }

        frm.toolbar.page.inner_toolbar.find(".stopwatch").remove();

        if (frm.doc.status !== "Work In Progress") {
            return;
        }

        if (!frm.doc.time_logs || !frm.doc.time_logs.length) {
            return;
        }

        let active_logs = frm.doc.time_logs.filter(row => {
            return row.from_time && !row.to_time;
        });

        if (!active_logs.length) {
            return;
        }

        let latest_log = active_logs[0];

        const timer_html = `
            <div class="stopwatch"
                style="
                    font-weight:bold;
                    margin:0px 13px 0px 2px;
                    color:#545454;
                    font-size:18px;
                    display:inline-block;
                    vertical-align:text-bottom;
                ">
                <span class="hours">00</span>
                <span class="colon">:</span>
                <span class="minutes">00</span>
                <span class="colon">:</span>
                <span class="seconds">00</span>
            </div>
        `;

        let section = frm.toolbar.page.add_inner_message(timer_html);

        function update_timer() {

            let start = moment(latest_log.from_time);
            let now = moment();

            let duration = moment.duration(now.diff(start));

            let hours = String(
                Math.floor(duration.asHours())
            ).padStart(2, '0');

            let minutes = String(
                duration.minutes()
            ).padStart(2, '0');

            let seconds = String(
                duration.seconds()
            ).padStart(2, '0');

            $(section).find(".hours").text(hours);
            $(section).find(".minutes").text(minutes);
            $(section).find(".seconds").text(seconds);
        }

        update_timer();

        frm.timer_interval = setInterval(() => {
            update_timer();
        }, 1000);
    },
    recovered_parts_template(frm) {

    if (!frm.doc.recovered_parts_template) return;

        frappe.call({
            method: "rvsf.rvsf.doctype.execution_job_card.execution_job_card.get_recovered_parts_template",
            args: {
                template: frm.doc.recovered_parts_template
            },
            callback: function(r) {

                if (r.message) {

                    // clear existing rows
                    frm.clear_table("recovered_parts");

                    (r.message || []).forEach(row => {

                        let child = frm.add_child("recovered_parts");

                        child.item_code = row.item_code;
                        child.item_name = row.item_name;
                        child.uom = row.uom;
                        child.warehouse = row.default_warehouse;
                    });

                    frm.refresh_field("recovered_parts");
                }
            }
        });
    }
});

frappe.ui.form.on("Recovered Item", {
    weight(frm, cdt, cdn) {
        calculate_total_weight(frm);
    },

    recovered_items_remove(frm) {
        calculate_total_weight(frm);
    }
});

function calculate_total_weight(frm) {
    let total = 0;

    (frm.doc.recovered_items || []).forEach(row => {
        total += flt(row.weight);
    });

    frm.set_value("total_weight", total);
}