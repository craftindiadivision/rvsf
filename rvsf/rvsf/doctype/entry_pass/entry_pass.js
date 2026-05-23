// Copyright (c) 2026, saheer and contributors
// For license information, please see license.txt

frappe.ui.form.on("Entry Pass", {
    entry_time(frm) {
        let user = frappe.session.user;
        frm.set_value("entry_approved_by", user);
        frm.set_value(
            "entry_approved_by_name",
            frappe.user.full_name()
        );
    },
    exit_time(frm) {
        let user = frappe.session.user;
        frm.set_value("exit_approved_by", user);
        frm.set_value(
            "exit_approved_by_name",
            frappe.user.full_name()
        );
    }
});
