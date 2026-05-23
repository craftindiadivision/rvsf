// Copyright (c) 2026, saheer and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Time Slot Template", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on("Time Slot Template", {
    refresh(frm) {

        frm.add_custom_button(
            __("Generate Weekly Slots"),
            function () {

                frm.call({
                    method: "generate_weekly_slots",
                    doc: frm.doc,
                    callback: function () {
                        frm.reload_doc();
                    }
                });

            }
        );

    }
});