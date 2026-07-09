// Copyright (c) 2026, saheer and contributors
// For license information, please see license.txt

frappe.ui.form.on("Vehicle Category", {
    onload(frm) {
        if (frm.is_new() && !frm.doc.monthly_wise_scrap_valuation?.length) {
            frm.call("populate_months");
        }
    }
});
