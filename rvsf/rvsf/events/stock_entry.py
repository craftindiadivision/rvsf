import frappe

def on_cancel(self,method=None):
    if self.stock_entry_type == "Disassembly" and self.custom_execution_order:
        if frappe.db.exists("Execution Order", self.custom_execution_order):
            frappe.db.set_value(
                "Execution Order",
                self.custom_execution_order,
                {
                    "status": "Work In Progress",
                },
                update_modified=False
            )