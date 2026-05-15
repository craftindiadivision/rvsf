frappe.ui.form.on("Supplier Quotation", {
    after_workflow_action(frm) {
        console.log("after_workflow_action called");
        frappe.call({
            method: "rvsf.rvsf.events.supplier_quotation.update_supplier_quotation_status",
            args: {
                supplier_quotation:frm.doc.name
            }
        })
    }
})