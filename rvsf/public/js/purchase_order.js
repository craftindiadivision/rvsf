frappe.ui.form.on("Purchase Order", {
    refresh(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("Create Gate Pass"), function () {
                frappe.model.open_mapped_doc({
                    method: "rvsf.rvsf.events.purchase_order.make_gate_pass",
                    frm: frm
                });
            })
        }
    }
})