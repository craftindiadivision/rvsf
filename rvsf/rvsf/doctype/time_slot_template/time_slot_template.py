# Copyright (c) 2026, saheer and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta
from frappe.utils import get_time
from datetime import datetime, timedelta
from frappe.model.document import Document
from frappe.utils import get_time
import frappe


class TimeSlotTemplate(Document):

    @frappe.whitelist()
    def generate_weekly_slots(self):

        # clear existing child rows from db + memory
        self.set("slot_details", [])

        start_time = get_time(self.start_time)
        end_time = get_time(self.end_time)

        for working_day in self.working_days:

            if not working_day.enabled:
                continue

            current = datetime.combine(
                datetime.today(),
                start_time
            )

            end_datetime = datetime.combine(
                datetime.today(),
                end_time
            )

            idx = 1

            while current < end_datetime:

                slot_end = current + timedelta(
                    minutes=self.slot_duration
                )

                self.append("slot_details", {
                    "idx": idx,
                    "day": working_day.day,
                    "start_time": current.time(),
                    "end_time": slot_end.time(),
                    "capacity": self.max_vehicles_per_slot
                })

                current = slot_end
                idx += 1

        # persist directly into db
        self.save(ignore_permissions=True)

        frappe.db.commit()

        return True