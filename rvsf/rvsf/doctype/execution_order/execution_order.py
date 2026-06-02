# Copyright (c) 2026, saheer and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.model.document import Document


class ExecutionOrder(Document):
    def validate(self):
        self.status = "Draft"
    def on_submit(self):
        self.db_set("status", "Submitted")
        for operation in self.operations:
            self.create_execution_job_card(operation)
            
    def create_execution_job_card(self, operation):
        existing_job_card = frappe.db.exists(
            "Execution Job Card",
            {
                "execution_order": self.name,
                "operation": operation.operation,
                "sequence_id": operation.sequence_id,
                "docstatus": ["!=", 2]
            }
        )
        if existing_job_card:
            frappe.msgprint(
                f"Job Card already exists for operation {operation.operation}",
                indicator="orange",
                alert=True
            )
            return existing_job_card
        
        job_card = frappe.new_doc("Execution Job Card")
        job_card.operation = operation.operation
        job_card.execution_order = self.name
        job_card.vehicle = self.vehicle
        job_card.source_warehouse = self.source_warehouse
        job_card.wip_warehouse = self.wip_warehouse
        job_card.expected_start_date = operation.planned_start_time
        job_card.expected_end_date = operation.planned_end_time
        job_card.expected_time_required_in_mins = operation.time
        job_card.sequence_id = operation.sequence_id
        if frappe.db.exists("Operation", operation.operation):
            operation_doc = frappe.get_doc("Operation", operation.operation)
            if operation_doc.custom_is_recovery_operation:
                job_card.is_recovery_operation = 1
        job_card.append("scheduled_time_logs", {
            "from_time": operation.planned_start_time,
            "to_time": operation.planned_end_time,
            "time_in_mins": operation.time
        })

        job_card.insert(ignore_permissions=True)

        frappe.msgprint(
            f"Job Card {job_card.name} created",
            indicator="green",
            alert=True
        )

        return job_card.name
    def on_cancel(self):
        self.db_set("status", "Cancelled")
        draft_job_cards = frappe.get_all(
            "Execution Job Card",
            filters={
                "execution_order": self.name,
                "docstatus": 0
            },
            pluck="name"
        )
        for job_card in draft_job_cards:
            frappe.delete_doc(
                "Execution Job Card",
                job_card,
                ignore_permissions=True
            )
            
@frappe.whitelist()
def get_routing_details(routing):

    if not frappe.db.exists("Routing", routing):
        frappe.throw("Routing not found")

    routing_doc = frappe.get_doc("Routing", routing)

    return routing_doc.as_dict()

@frappe.whitelist()
def create_selected_job_cards(execution_order, operations):
    operations = json.loads(operations)
    doc = frappe.get_doc("Execution Order", execution_order)
    for row in doc.operations:

        if row.operation in operations:

            doc.create_execution_job_card(row)
            
@frappe.whitelist()
def get_missing_job_card_operations(execution_order):
    doc = frappe.get_doc("Execution Order", execution_order)
    missing_operations = []
    for row in doc.operations:
        existing_job_card = frappe.db.exists(
            "Execution Job Card",
            {
                "execution_order": doc.name,
                "operation": row.operation,
                "sequence_id": row.sequence_id,
                "docstatus": ["!=", 2]
            }
        )
        if not existing_job_card:

            missing_operations.append({
                "name": row.name,
                "operation": row.operation
            })
    return missing_operations

@frappe.whitelist()
def create_disassembly_stock_entry(execution_order):

    doc = frappe.get_doc("Execution Order", execution_order)

    if not doc.vehicle:
        frappe.throw("Vehicle is mandatory.")

    if not doc.source_warehouse:
        frappe.throw("Source Warehouse is mandatory.")

    if not doc.recovered_parts:
        frappe.throw("Recovered Parts not found.")

    # Validate rates
    for row in doc.recovered_parts:
        if not row.warehouse:
            frappe.throw(
                f"Target Warehouse is mandatory for Item {row.item_code}"
            )
    recovered_total = 0

    for row in doc.recovered_parts:
        recovered_total += (row.qty * row.rate)

    stock_entry = frappe.new_doc("Stock Entry")

    stock_entry.company = doc.company
    stock_entry.stock_entry_type = "Disassemble"
    stock_entry.custom_execution_order = doc.name
    # Source Item (Vehicle)
    stock_entry.append("items", {
        "item_code": doc.vehicle,
        "qty": 1,
        "s_warehouse": doc.source_warehouse,
        # "basic_rate": valuation_rate
    })

    # Recovered Parts
    for row in doc.recovered_parts:

        stock_entry.append("items", {
            "item_code": row.item_code,
            "qty": row.qty,
            "t_warehouse": row.warehouse,
            "basic_rate": row.rate,
            "is_finished_item": 1
        })

    stock_entry.insert(ignore_permissions=True)
    # Uncomment if you want automatic submission
    stock_entry.submit()
    frappe.db.set_value(
    "Execution Order",
    doc.name,
    {
        "status": "Completed",
    },
    update_modified=False
    )


    return stock_entry.name