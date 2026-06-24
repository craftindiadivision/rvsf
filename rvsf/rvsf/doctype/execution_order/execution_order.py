# Copyright (c) 2026, saheer and contributors
# For license information, please see license.txt

import json
import datetime

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
    add_days,
    add_to_date,
    cint,
    flt,
    get_datetime,
    get_time,
    getdate,
    time_diff_in_hours,
)
from dateutil.relativedelta import relativedelta

from erpnext.manufacturing.doctype.manufacturing_settings.manufacturing_settings import (
    get_mins_between_operations,
)


def time_diff_in_minutes(end, start):
    from frappe.utils import time_diff
    return time_diff(end, start).total_seconds() / 60


class ExecutionOrder(Document):
    
    def validate(self):
        self.status = "Draft"

    def before_save(self):
        if self.planned_start_date and self.get("operations"):
            self.schedule_operations()

    def on_submit(self):
        self.db_set("status", "Submitted")
        for operation in self.operations:
            self.create_execution_job_card(operation)

    def on_cancel(self):
        self.db_set("status", "Cancelled")
        draft_job_cards = frappe.get_all(
            "Execution Job Card",
            filters={"execution_order": self.name, "docstatus": 0},
            pluck="name",
        )
        for job_card in draft_job_cards:
            frappe.delete_doc("Execution Job Card", job_card, ignore_permissions=True)

    def on_update_after_submit(self):
        previous_state = self.get_doc_before_save()

        if (
            previous_state
            and previous_state.workflow_state != "Under Valuation"
            and self.workflow_state == "Under Valuation"
        ):
            self.validate_job_cards_before_valuation()
    def schedule_operations(self):
        for idx, row in enumerate(self.operations):
            self._set_operation_start_end_time(row, idx)
        last_end = self.operations[-1].planned_end_time if self.operations else None
        if last_end:
            self.planned_end_date = last_end

    def _set_operation_start_end_time(self, row, idx):
        if idx == 0:
            row.planned_start_time = self.planned_start_date

        elif self.operations[idx - 1].sequence_id:
            prev_seq = self.operations[idx - 1].sequence_id
            curr_seq = row.sequence_id

            if prev_seq == curr_seq:
                row.planned_start_time = self.operations[idx - 1].planned_start_time
            else:
                same_seq_ops = [
                    op for op in self.operations
                    if op.sequence_id == prev_seq
                ]
                latest_end = max(
                    get_datetime(op.planned_end_time)
                    for op in same_seq_ops
                    if op.planned_end_time
                )
                row.planned_start_time = latest_end + get_mins_between_operations()
        else:
            row.planned_start_time = (
                get_datetime(self.operations[idx - 1].planned_end_time)
                + get_mins_between_operations()
            )
        row.planned_end_time = (
            get_datetime(row.planned_start_time)
            + relativedelta(minutes=flt(row.time))
        )
        if get_datetime(row.planned_start_time) == get_datetime(row.planned_end_time):
            frappe.throw(
                _(
                    "Row #{0}: Planned start time cannot equal planned end time "
                    "for operation {1}. Check that 'Time (mins)' is greater than 0."
                ).format(row.idx, row.operation)
            )

    def schedule_with_workstation(self, row):
        if not row.workstation:
            return []
        schedule_row = frappe._dict(
            planned_start_time=get_datetime(row.planned_start_time),
            planned_end_time=get_datetime(row.planned_end_time),
            remaining_time_in_mins=flt(row.time),
            time_in_mins=flt(row.time),
        )

        scheduled_slots = []
        schedule_row.remaining_time_in_mins = schedule_row.time_in_mins

        while schedule_row.remaining_time_in_mins > 0:
            self._validate_overlap_for_workstation(schedule_row, row)
            self._check_workstation_time(schedule_row, row, scheduled_slots)

        return scheduled_slots

    def _validate_overlap_for_workstation(self, schedule_row, op_row):
       
        conflict = self._get_conflicting_slot(schedule_row, op_row)
        if not conflict:
            return  

        if conflict.get("planned_start_time"):
            new_start = get_datetime(conflict["planned_start_time"])
        else:
            new_start = (
                get_datetime(conflict["to_time"]) + get_mins_between_operations()
            )

        schedule_row.planned_start_time = new_start
        schedule_row.planned_end_time = add_to_date(
            new_start, minutes=schedule_row.remaining_time_in_mins
        )
        self._validate_overlap_for_workstation(schedule_row, op_row)

    def _get_conflicting_slot(self, schedule_row, op_row):
        from_time = schedule_row.planned_start_time
        to_time = schedule_row.planned_end_time
        workstation = op_row.workstation

        # Query overlapping scheduled time log rows on other Execution Job Cards
        conflicts = frappe.db.sql(
            """
            SELECT
                ejc.name,
                stl.from_time,
                stl.to_time
            FROM
                `tabExecution Job Card` ejc
            JOIN
                `tabJob Card Scheduled Time` stl ON stl.parent = ejc.name
            WHERE
                ejc.workstation = %(workstation)s
                AND ejc.docstatus < 2
                AND ejc.name != %(self_name)s
                AND (
                    (stl.from_time < %(from_time)s AND stl.to_time  > %(from_time)s)
                    OR (stl.from_time < %(to_time)s  AND stl.to_time  > %(to_time)s)
                    OR (stl.from_time >= %(from_time)s AND stl.to_time <= %(to_time)s)
                )
            ORDER BY stl.to_time ASC
            LIMIT 1
            """,
            {
                "workstation": workstation,
                "self_name": self.name or "New Execution Order",
                "from_time": from_time,
                "to_time": to_time,
            },
            as_dict=True,
        )

        return conflicts[0] if conflicts else None

    def _check_workstation_time(self, schedule_row, op_row, scheduled_slots):
        workstation_doc = frappe.get_cached_doc("Workstation", op_row.workstation)
        allow_overtime = cint(
            frappe.db.get_single_value("Manufacturing Settings", "allow_overtime")
        )
        if not workstation_doc.working_hours or allow_overtime:
            end_time = add_to_date(
                schedule_row.planned_start_time,
                minutes=schedule_row.remaining_time_in_mins,
            )
            scheduled_slots.append(
                {
                    "from_time": schedule_row.planned_start_time,
                    "to_time": end_time,
                    "time_in_mins": schedule_row.remaining_time_in_mins,
                }
            )
            schedule_row.planned_start_time = end_time
            schedule_row.remaining_time_in_mins = 0.0
            return

        start_date = getdate(schedule_row.planned_start_time)
        start_time = get_time(schedule_row.planned_start_time)

        new_start_date = workstation_doc.validate_workstation_holiday(start_date)
        if new_start_date != start_date:
            schedule_row.planned_start_time = datetime.datetime.combine(
                new_start_date, start_time
            )
            start_date = new_start_date

        total_slots = len(workstation_doc.working_hours)
        slot_used = False

        for i, shift in enumerate(workstation_doc.working_hours):
            ws_start = datetime.datetime.combine(start_date, get_time(shift.start_time))
            ws_end = datetime.datetime.combine(start_date, get_time(shift.end_time))

            if not (ws_start <= get_datetime(schedule_row.planned_start_time) <= ws_end):
                continue

            slot_used = True
            available_mins = time_diff_in_minutes(ws_end, schedule_row.planned_start_time)

            if available_mins >= schedule_row.remaining_time_in_mins:
                slot_end = add_to_date(
                    schedule_row.planned_start_time,
                    minutes=schedule_row.remaining_time_in_mins,
                )
                scheduled_slots.append(
                    {
                        "from_time": schedule_row.planned_start_time,
                        "to_time": slot_end,
                        "time_in_mins": schedule_row.remaining_time_in_mins,
                    }
                )
                schedule_row.planned_start_time = slot_end
                schedule_row.remaining_time_in_mins = 0.0
            else:
                scheduled_slots.append(
                    {
                        "from_time": schedule_row.planned_start_time,
                        "to_time": ws_end,
                        "time_in_mins": available_mins,
                    }
                )
                schedule_row.remaining_time_in_mins -= available_mins

                if i + 1 < total_slots:
                    schedule_row.planned_start_time = datetime.datetime.combine(
                        start_date,
                        get_time(workstation_doc.working_hours[i + 1].start_time),
                    )
                else:
                    next_day = add_days(start_date, 1)
                    schedule_row.planned_start_time = datetime.datetime.combine(
                        next_day,
                        get_time(workstation_doc.working_hours[0].start_time),
                    )
            break   
        if not slot_used and workstation_doc.working_hours:
            first_shift_start = datetime.datetime.combine(
                start_date,
                get_time(workstation_doc.working_hours[0].start_time),
            )
            if get_datetime(schedule_row.planned_start_time) < first_shift_start:
                schedule_row.planned_start_time = first_shift_start
            else:
                next_day = add_days(start_date, 1)
                schedule_row.planned_start_time = datetime.datetime.combine(
                    next_day,
                    get_time(workstation_doc.working_hours[0].start_time),
                )

    def create_execution_job_card(self, operation):
        existing_job_card = frappe.db.exists(
            "Execution Job Card",
            {
                "execution_order": self.name,
                "operation": operation.operation,
                "sequence_id": operation.sequence_id,
                "docstatus": ["!=", 2],
            },
        )
        if existing_job_card:
            frappe.msgprint(
                f"Job Card already exists for operation {operation.operation}",
                indicator="orange",
                alert=True,
            )
            return existing_job_card

        enable_capacity_planning = not cint(
            frappe.db.get_single_value("Manufacturing Settings", "disable_capacity_planning")
        )

        if enable_capacity_planning and operation.workstation:
            scheduled_slots = self.schedule_with_workstation(operation)
        else:
            scheduled_slots = [
                {
                    "from_time": operation.planned_start_time,
                    "to_time": operation.planned_end_time,
                    "time_in_mins": flt(operation.time),
                }
            ]
        settings = frappe.get_cached_doc("RVSF Settings")
        operation_type_map = {
            row.operation: row.operation_type
            for row in settings.operation_type_mapping
        }
        job_card = frappe.new_doc("Execution Job Card")
        job_card.operation = operation.operation
        job_card.execution_order = self.name
        job_card.vehicle = self.vehicle
        job_card.workstation = operation.workstation
        job_card.workstation_type = operation.workstation_type
        job_card.source_warehouse = self.source_warehouse
        job_card.wip_warehouse = self.wip_warehouse
        job_card.sequence_id = operation.sequence_id
        job_card.hour_rate = operation.hour_rate
        job_card.expected_time_required_in_mins = flt(operation.time)
        job_card.operation_type = operation_type_map.get(operation.operation)
        if (
            job_card.operation_type == "Depollution"
            and self.purchase_lead
            and frappe.db.exists("Purchase Lead", self.purchase_lead)
        ):
            job_card.fuel_type = frappe.db.get_value(
                "Purchase Lead",
                self.purchase_lead,
                "fuel_type"
            )
            
        job_card.expected_start_date = scheduled_slots[0]["from_time"]
        job_card.expected_end_date   = scheduled_slots[-1]["to_time"]

        if frappe.db.exists("Operation", operation.operation):
            operation_doc = frappe.get_doc("Operation", operation.operation)
            if operation_doc.get("custom_is_recovery_operation"):
                job_card.is_recovery_operation = 1

        for slot in scheduled_slots:
            job_card.append(
                "scheduled_time_logs",
                {
                    "from_time":    slot["from_time"],
                    "to_time":      slot["to_time"],
                    "time_in_mins": slot["time_in_mins"],
                },
            )

        job_card.insert(ignore_permissions=True)
        frappe.db.set_value(
            operation.doctype,
            operation.name,
            {
                "planned_start_time": scheduled_slots[0]["from_time"],
                "planned_end_time":   scheduled_slots[-1]["to_time"],
            },
            update_modified=False,
        )

        frappe.msgprint(
            f"Job Card {job_card.name} created for {operation.operation}",
            indicator="green",
            alert=True,
        )

        return job_card.name

    def calculate_operating_cost(self):
        self.planned_operating_cost = 0.0
        self.actual_operating_cost  = 0.0

        for row in self.get("operations"):
            if not row.hour_rate and row.workstation:
                row.hour_rate = (
                    frappe.get_cached_value("Workstation", row.workstation, "hour_rate") or 0.0
                )

            row.planned_operating_cost = flt(row.hour_rate) * (flt(row.time) / 60.0)
            row.actual_operating_cost  = flt(row.hour_rate) * (flt(row.actual_operation_time) / 60.0)

            self.planned_operating_cost += row.planned_operating_cost
            self.actual_operating_cost  += row.actual_operating_cost

        self.total_operating_cost = (
            flt(self.planned_operating_cost)
            + flt(self.additional_operating_cost or 0)
        )
    def validate_job_cards_before_valuation(self):
        pending = frappe.get_all(
            "Execution Job Card",
            filters={
                "execution_order": self.name,
                "docstatus": 0
            },
            pluck="name"
        )

        if pending:
            frappe.throw(
                _("All Execution Job Cards must be submitted before sending for valuation.")
            )
@frappe.whitelist()
def get_routing_details(routing):
    if not frappe.db.exists("Routing", routing):
        frappe.throw("Routing not found")
    return frappe.get_doc("Routing", routing).as_dict()


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
    missing = []
    for row in doc.operations:
        exists = frappe.db.exists(
            "Execution Job Card",
            {
                "execution_order": doc.name,
                "operation": row.operation,
                "sequence_id": row.sequence_id,
                "docstatus": ["!=", 2],
            },
        )
        if not exists:
            missing.append({"name": row.name, "operation": row.operation})
    return missing

@frappe.whitelist()
def create_disassembly_stock_entry(execution_order):
    doc = frappe.get_doc("Execution Order", execution_order)

    if not doc.vehicle:
        frappe.throw("Vehicle is mandatory.")
    if not doc.source_warehouse:
        frappe.throw("Source Warehouse is mandatory.")
    if not doc.recovered_parts:
        frappe.throw("Recovered Parts not found.")

    for row in doc.recovered_parts:
        if not row.warehouse:
            frappe.throw(f"Target Warehouse is mandatory for Item {row.item_code}")

    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.company = doc.company
    stock_entry.stock_entry_type = "Disassemble"
    stock_entry.custom_execution_order = doc.name

    stock_entry.append("items", {
        "item_code":doc.vehicle,
        "qty":1,
        "s_warehouse": doc.source_warehouse,
    })

    for row in doc.recovered_parts:
        # if frappe.db.exists("Item", row.item_code):
        #     frappe.db.set_value(
        #         "Item",
        #         row.item_code,
        #         {
        #             "weight_per_unit": row.weight or 0.0,
        #             "weight_uom": row.weight_uom or ""
        #         }
        #     )
        stock_entry.append("items", {
            "item_code": row.item_code,
            "qty": row.qty,
            "t_warehouse": row.warehouse,
            "basic_rate": row.rate,
            "is_finished_item": 1,
        })

    stock_entry.insert(ignore_permissions=True)
    stock_entry.submit()

    frappe.db.set_value(
        "Execution Order",
        doc.name,
        {"status": "Completed"},
        update_modified=False,
    )
    return stock_entry.name