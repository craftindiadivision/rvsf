// Copyright (c) 2026, saheer and contributors
// For license information, please see license.txt

frappe.ui.form.on("Execution Order", {
	refresh(frm) {

        if (frm.doc.docstatus !== 1) return;

        frappe.call({
            method: "rvsf.rvsf.doctype.execution_order.execution_order.get_missing_job_card_operations",
            args: {
                execution_order: frm.doc.name
            },
            callback: function(r) {

                if (!r.message || !r.message.length) {
                    return;
                }

                frm.add_custom_button(__("Create Job Card"), function() {

                    let operations_data = [];

                        (frm.doc.operations || [])
                            .sort((a, b) => a.sequence_id - b.sequence_id)
                            .forEach(row => {

                                operations_data.push({
                                    operation: row.operation
                                });
                            });

                    const dialog = frappe.prompt(

                        {
                            fieldname: "operations",

                            fieldtype: "Table",

                            label: __("Operations"),

                            cannot_add_rows: true,

                            in_place_edit: false,

                            fields: [
                                {
                                    fieldtype: "Data",
                                    fieldname: "operation",
                                    label: __("Operation"),
                                    read_only: 1,
                                    in_list_view: 1
                                }
                            ],

                            data: operations_data,

                            get_data: () => operations_data
                        },

                        function () {

                            const selected_rows =
                                dialog.fields_dict.operations.grid.get_selected_children();

                            if (!selected_rows.length) {

                                frappe.msgprint(
                                    __("Please select at least one operation")
                                );

                                return;
                            }

                            let operations = selected_rows.map(row => row.operation);

                            frappe.call({

                                method: "rvsf.rvsf.doctype.execution_order.execution_order.create_selected_job_cards",

                                freeze: true,
                                
                                args: {
                                    execution_order: frm.doc.name,
                                    operations: operations
                                },

                                callback: function () {

                                    frm.reload_doc();
                                }
                            });

                            dialog.hide();
                        },

                        __("Create Job Cards"),

                        __("Create")
                    );

                });
            }
        });
        const all_operations_completed =
        (frm.doc.operations || []).length > 0 &&
        (frm.doc.operations || []).every(
            row => row.status === "Completed"
        );
        // let editable = frm.doc.workflow_state === "Under Valuation";

        // frm.fields_dict.recovered_parts.grid.update_docfield_property(
        //     "rate",
        //     "read_only",
        //     editable ? 0 : 1
        // );

        frm.refresh_field("recovered_parts");
        if (
            frm.doc.docstatus === 1 &&
            all_operations_completed && frm.doc.status === "Work In Progress" 
        ) {
            frm.add_custom_button(__("Finish"), () => {
                frm.trigger("finish_execution_order");
            });
        }
    },
    routing(frm) {
            frappe.call({
                method: "rvsf.rvsf.doctype.execution_order.execution_order.get_routing_details",
                args: {
                    routing: frm.doc.routing
                },
                callback: function(r) {
                    if (r.message) {
                        let routing = r.message;
                        if (routing.operations) {
                            frm.clear_table("operations");
                            routing.operations.forEach(row => {
                                let child = frm.add_child("operations");
                                child.operation = row.operation;
                                child.workstation = row.workstation;
                                child.workstation_type = row.workstation_type;
                                child.time = row.time_in_mins;
                                child.hour_rate = row.hour_rate;
                                child.planned_operating_cost = row.operating_cost;
                                child.sequence_id = row.sequence_id;
                            });
                            frm.refresh_field("operations");
                            calculateTotalOperatingCost(frm);
                        }
                    }
                },
            });
    }, 
    additional_operating_cost(frm) {
        calculateTotalOperatingCost(frm);
    },
    finish_execution_order(frm) {

    // let missing_rate = (frm.doc.recovered_parts || []).filter(
    //     row => !row.rate || row.rate <= 0
    // );

    // if (missing_rate.length) {

    //     frappe.msgprint(
    //         __("Please enter rate for all recovered parts.")
    //     );

    //     return;
    // }

    frappe.call({
        method: "rvsf.rvsf.doctype.execution_order.execution_order.create_disassembly_stock_entry",
        args: {
            execution_order: frm.doc.name
        },
        freeze: true,
        freeze_message: __("Creating Stock Entry...")
    }).then(r => {

        frappe.show_alert({
            message: __("Stock Entry Created: {0}", [r.message]),
            indicator: "green"
        });

        frm.reload_doc();
    });
}
});

frappe.ui.form.on("Execution Order Operation", {
    time(frm, cdt, cdn) {
        let child = frappe.get_doc(cdt, cdn);
        child.planned_operating_cost = (child.time / 60) * child.hour_rate;
        frm.refresh_field("operations");
        calculateTotalOperatingCost(frm);
    }
});

function calculateTotalOperatingCost(frm) {
    let totalCost = 0;
    frm.doc.operations.forEach(row => {
        totalCost += row.planned_operating_cost || 0;
    });
    frm.set_value("planned_operating_cost", totalCost);
    if (frm.doc.actual_operating_cost && frm.doc.actual_operating_cost > 0) {
        frm.set_value("total_operating_cost", frm.doc.actual_operating_cost + (frm.doc.additional_operating_cost || 0)); 
    } else {
        frm.set_value("total_operating_cost", frm.doc.planned_operating_cost + (frm.doc.additional_operating_cost || 0));
    }
}

frappe.ui.form.on("Execution Order Recovered Parts", {

    qty(frm, cdt, cdn) {
        calculate_amount(frm, cdt, cdn);
    },

    rate(frm, cdt, cdn) {
        calculate_amount(frm, cdt, cdn);
    }
});

function calculate_amount(frm, cdt, cdn) {

    let row = locals[cdt][cdn];

    row.amount = flt(row.qty) * flt(row.rate);

    frm.refresh_field("recovered_parts");
}