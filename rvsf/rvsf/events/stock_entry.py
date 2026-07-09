
import frappe
from frappe import _
from frappe.utils import flt


def validate(self, method=None):
	if self.purpose == "Disassemble" and self.custom_execution_order:
		add_rvsf_additional_cost(self, self.custom_execution_order)

def on_submit(self, method=None):
	if self.stock_entry_type == "Disassemble" and self.custom_execution_order:	
		if frappe.db.exists("Execution Order", self.custom_execution_order):
			purchase_lead = frappe.db.get_value("Execution Order", self.custom_execution_order, "purchase_lead")
			purchase_lead_doc = frappe.get_doc("Purchase Lead", purchase_lead)
			purchase_lead_doc.db_set("status", "Ready For Certification")
def on_cancel(self, method=None):
	
	if self.stock_entry_type == "Disassemble" and self.custom_execution_order:
		if frappe.db.exists("Execution Order", self.custom_execution_order):
			frappe.db.set_value(
				"Execution Order",
				self.custom_execution_order,
				{
					"status": "Work In Progress",
				},
				update_modified=False
			)
			purchase_lead = frappe.db.get_value("Execution Order", self.custom_execution_order, "purchase_lead")
			purchase_lead_doc = frappe.get_doc("Purchase Lead", purchase_lead)
			purchase_lead_doc.db_set("status", "Accepted")


def add_rvsf_additional_cost(stock_entry, execution_order_name):
	
	if not execution_order_name:
		return
	
	try:
		execution_order = frappe.get_doc("Execution Order", execution_order_name)
	except frappe.DoesNotExistError:
		frappe.log_error(
			f"Execution Order {execution_order_name} not found",
			"RVSF Stock Entry Additional Cost"
		)
		return
	
	# Get company and settings
	company = stock_entry.company
	
	# Get expense account from company settings
	company_settings = frappe.db.get_value(
		"Company",
		company,
		["default_expense_account", "default_operating_cost_account"],
		as_dict=True
	)
	
	# Determine expense account (prefer operating cost account)
	expense_account = (
		company_settings.get("default_operating_cost_account") or 
		company_settings.get("default_expense_account")
	)
	
	if not expense_account:
		frappe.log_error(
			f"No expense account configured for company {company}",
			"RVSF Stock Entry Additional Cost"
		)
		return
	
	# Clear existing RVSF additional costs to prevent duplicates
	# Keep only non-RVSF costs (if any from other sources)
	stock_entry.additional_costs = [
		row for row in stock_entry.get("additional_costs", [])
		if not row.description or not row.description.startswith("RVSF:")
	]
	
	# Add operating costs from Execution Order
	add_execution_order_operating_cost(
		stock_entry,
		execution_order,
		expense_account
	)
	
	# Add additional operating costs from Execution Order
	add_execution_order_additional_cost(
		stock_entry,
		execution_order,
		expense_account
	)


def add_execution_order_operating_cost(stock_entry, execution_order, expense_account):
	
	
	if not execution_order.get("operations"):
		return
	
	# Calculate total operating cost from all operations
	# This will be used as the total amount to distribute
	total_operating_cost = flt(0)
	
	for operation in execution_order.get("operations", []):
		if operation.actual_operating_cost:
			total_operating_cost += flt(operation.actual_operating_cost)
	
	# If there are line-item operating costs, append them individually
	# (This allows ERPNext to distribute them properly)
	for operation in execution_order.get("operations", []):
		if operation.actual_operating_cost and flt(operation.actual_operating_cost) > 0:
			stock_entry.append(
    "additional_costs",
    {
        "expense_account": expense_account,
        "description": _("RVSF: Operation: {0}").format(
            operation.operation or "Operation"
        ),
        "amount": flt(operation.actual_operating_cost),
        "base_amount": flt(operation.actual_operating_cost),
        "has_operating_cost": 1,
    },
)


def add_execution_order_additional_cost(stock_entry, execution_order, expense_account):
	
	
	if execution_order.additional_operating_cost and flt(execution_order.additional_operating_cost) > 0:
		stock_entry.append(
			"additional_costs",
			{
				"expense_account": expense_account,
				"description": _("RVSF: Additional Operating Cost"),
				"amount": flt(execution_order.additional_operating_cost),
			},
		)