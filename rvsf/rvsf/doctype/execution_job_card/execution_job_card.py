# Copyright (c) 2026, saheer and contributors
# For license information, please see license.txt

from pydoc import doc

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, time_diff_in_seconds

class ExecutionJobCard(Document):
	def validate(self):
     
		self.update_job_status()
		if self.status != "Open":
			self.sync_operation_status()
	def on_submit(self):
		if not self.time_logs:
			frappe.throw(
				"Please start and complete the operation before submitting this Job Card."
			)
		for row in self.time_logs:
			if row.from_time and not row.to_time:
				frappe.throw("Please stop the running timer before submitting.")
		self.db_set("status", "Completed")
		self.sync_operation_actuals()
		self.sync_operation_status()
		self.update_execution_order_actuals()
		self.map_recovered_parts_to_execution_order()
		self.update_execution_order_status()
		self.check_recovered_parts()
		
	def on_cancel(self):
		self.db_set("status", "Cancelled")
		self.sync_operation_actuals()
		self.remove_recovered_parts_from_execution_order()
		self.update_execution_order_status()
		self.update_execution_order_actuals()
	def on_trash(self):
		self.reset_operation_status()
	def update_job_status(self):
		if not self.time_logs:
			self.status = "Open"
			self.actual_start_date = None
			self.actual_end_date = None
			self.total_time_in_mins = 0
			return
		elif self.time_logs and self.amended_from:
			self.status = "Work In Progress"
	def update_execution_order_status(self):

		if not self.execution_order:
			return

		execution_order = frappe.get_doc(
			"Execution Order",
			self.execution_order
		)

		completed_operations = len([
			row for row in execution_order.operations
			if row.status == "Completed"
		])
		if completed_operations > 0:

			execution_order.status = "Work In Progress"

		else:

			execution_order.status = "Submitted"

		execution_order.flags.ignore_validate_update_after_submit = True
		execution_order.save(ignore_version=True)
	def reset_operation_status(self):
		if not self.execution_order:
			return

		execution_order = frappe.get_doc(
			"Execution Order",
			self.execution_order
		)

		# Check whether any other job card exists for this operation
		exists = frappe.db.exists(
			"Execution Job Card",
			{
				"execution_order": self.execution_order,
				"operation": self.operation,
				"name": ["!=", self.name]
			}
		)

		if not exists:

			for row in execution_order.operations:
				if row.operation == self.operation:
					frappe.db.set_value(
						row.doctype,
						row.name,
						"status",
						"Pending"
					)
					break
 
	def map_recovered_parts_to_execution_order(doc, method=None):

		if not doc.execution_order:
			return

		execution_order = frappe.get_doc(
			"Execution Order",
			doc.execution_order
		)

		# Validation
		for row in execution_order.recovered_parts:

			if row.source_job_card == doc.name:
				frappe.throw(
					f"Recovered Parts from Job Card {doc.name} "
					f"already exist in Execution Order {execution_order.name}"
				)

		# Map rows
		for row in doc.recovered_parts:

			execution_order.append("recovered_parts", {
				"item_code": row.item_code,
				"item_name": row.item_name,
				"qty": row.qty,
				"weight": row.weight,
				"uom": row.uom,
				"warehouse": row.warehouse,
				"source_job_card": doc.name,
				"operation": doc.operation
			})

		execution_order.flags.ignore_validate_update_after_submit = True
		execution_order.save()
  
	def remove_recovered_parts_from_execution_order(doc, method=None):
		if not doc.execution_order:
			return

		exists = frappe.db.exists(
			"Execution Order Recovered Parts",
			{
				"parent": doc.execution_order,
				"source_job_card": doc.name
			}
		)

		if not exists:
			return

		frappe.db.delete(
			"Execution Order Recovered Parts",
			{
				"parent": doc.execution_order,
				"source_job_card": doc.name
			}
		)
	def sync_operation_status(self):
		if not self.execution_order:
			return

		execution_order = frappe.get_doc(
			"Execution Order",
			self.execution_order
		)

		for row in execution_order.operations:

			if row.operation == self.operation:

				row.status = self.status
				break

		execution_order.flags.ignore_validate_update_after_submit = True
		execution_order.save(ignore_version=True)
	
	def sync_operation_actuals(self):
		if not self.execution_order:
			return

		execution_order = frappe.get_doc(
			"Execution Order",
			self.execution_order
		)

		for row in execution_order.operations:

			if row.operation != self.operation:
				continue

			# Submit
			if self.docstatus == 1:
				row.actual_start_time = self.actual_start_date
				row.actual_end_time = self.actual_end_date
				row.actual_operation_time = self.total_time_in_mins

				# adjust according to your costing logic
				row.actual_operating_cost = (
					self.total_time_in_mins * (row.hour_rate or 0) / 60
				)
			# Cancel
			elif self.docstatus == 2:
				row.status = "Pending"
				row.actual_start_time = None
				row.actual_end_time = None
				row.actual_operation_time = 0
				row.actual_operating_cost = 0

			break

		execution_order.flags.ignore_validate_update_after_submit = True
		execution_order.save(ignore_version=True)

	def update_execution_order_actuals(self):

		if not self.execution_order:
			return

		execution_order = frappe.get_doc(
			"Execution Order",
			self.execution_order
		)

		# Get submitted Job Cards
		job_cards = frappe.get_all(
			"Execution Job Card",
			filters={
				"execution_order": self.execution_order,
				"docstatus": 1
			},
			fields=[
				"actual_start_date",
				"actual_end_date"
			]
		)

		# Actual Start Date
		start_dates = [
			d.actual_start_date
			for d in job_cards
			if d.actual_start_date
		]

		execution_order.actual_start_date = (
			min(start_dates) if start_dates else None
		)

		# Calculate Actual Operation Time and Cost from Operations table
		total_minutes = sum(
			(row.actual_operation_time or 0)
			for row in execution_order.operations
		)

		execution_order.actual_operation_time = total_minutes / 60

		execution_order.actual_operating_cost = sum(
			(row.actual_operating_cost or 0)
			for row in execution_order.operations
		)
		execution_order.total_operating_cost = sum(row.actual_operating_cost or 0 for row in execution_order.operations) + execution_order.additional_operating_cost
		# Update Actual End Date only when all operations are completed
		total_operations = len(execution_order.operations)

		completed_operations = len([
			row for row in execution_order.operations
			if row.status == "Completed"
		])

		if (
			total_operations > 0
			and completed_operations == total_operations
		):

			end_dates = [
				d.actual_end_date
				for d in job_cards
				if d.actual_end_date
			]

			execution_order.actual_end_date = (
				max(end_dates) if end_dates else None
			)

		else:

			execution_order.actual_end_date = None

		execution_order.flags.ignore_validate_update_after_submit = True
		execution_order.save(ignore_version=True)
	def check_recovered_parts(self):
		if not self.recovered_parts and self.is_recovery_operation:
			frappe.throw("Please add recovered parts before submitting the Job Card.")
@frappe.whitelist()
def start_job(docname, employees=None):
    import json
    doc = frappe.get_doc("Execution Job Card", docname)

    # handle json string
    if isinstance(employees, str):
        employees = json.loads(employees)

    employees = employees or []

    if not employees:
        frappe.throw("Please select at least one employee")

    current_time = now_datetime()

    # prevent duplicate running logs
    for row in doc.time_logs:

        if row.from_time and not row.to_time:

            frappe.throw("Job is already running")

    # first start
    if not doc.actual_start_date:
        doc.actual_start_date = current_time
    # clear existing employee rows
    doc.set("employee", [])

    existing_employees = []

    for employee in employees:
        if employee in existing_employees:
            continue
        existing_employees.append(employee)
        # add employee child table
        doc.append("employee", {
            "employee": employee
        })

        # add time log
        doc.append("time_logs", {
            "employee": employee,
            "from_time": current_time
        })

    doc.status = "Work In Progress"

    doc.save(ignore_permissions=True)
    doc.sync_operation_status()
    frappe.db.commit()

    
    
@frappe.whitelist()
def finish_job(docname):

    doc = frappe.get_doc("Execution Job Card", docname)

    current_time = now_datetime()

    for row in doc.time_logs:

        if row.from_time and not row.to_time:

            row.to_time = current_time

            total_seconds = time_diff_in_seconds(
                row.to_time,
                row.from_time
            )

            row.time_in_mins = total_seconds / 60

    doc.actual_end_date = current_time
    doc.status = "Work In Progress"

    calculate_total_time(doc)

    doc.save(ignore_permissions=True)
    doc.sync_operation_status()
    frappe.db.commit()
    
@frappe.whitelist()
def pause_job(docname):

    doc = frappe.get_doc("Execution Job Card", docname)

    current_time = now_datetime()

    active_found = False

    for row in doc.time_logs:

        if row.from_time and not row.to_time:

            row.to_time = current_time

            total_seconds = time_diff_in_seconds(
                row.to_time,
                row.from_time
            )

            row.time_in_mins = total_seconds / 60

            active_found = True

    if not active_found:
        frappe.throw("No active logs found")

    doc.status = "On Hold"

    calculate_total_time(doc)

    doc.save(ignore_permissions=True)
    doc.sync_operation_status()
    frappe.db.commit()

@frappe.whitelist()
def resume_job(docname):
    doc = frappe.get_doc("Execution Job Card", docname)

    current_time = now_datetime()

    # prevent duplicate running logs
    for row in doc.time_logs:

        if row.from_time and not row.to_time:

            frappe.throw("Job is already running")

    if not doc.employee:

        frappe.throw("No employees assigned to this Job")

    for row in doc.employee:

        doc.append("time_logs", {
            "employee": row.employee,
            "from_time": current_time
        })

    doc.status = "Work In Progress"

    doc.save(ignore_permissions=True)
    doc.sync_operation_status()
    frappe.db.commit()

def calculate_total_time(doc):

    total_mins = 0

    for row in doc.time_logs:

        if row.time_in_mins:
            total_mins += row.time_in_mins

    doc.total_time_in_mins = total_mins

    
@frappe.whitelist()
def get_recovered_parts_template(template):
    if frappe.db.exists("Recovered Parts Template", template):
        doc = frappe.get_doc("Recovered Parts Template", template)
        data = []
        for row in doc.recovered_parts:
            data.append({
                "item_code": row.item_code,
                "item_name": row.item_name,
                "uom": row.uom,
                "default_warehouse": row.default_warehouse,
            })
        return data

