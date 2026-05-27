# Copyright (c) 2026, saheer and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta
from frappe.utils import get_time



class TimeSlotTemplate(Document):

    @frappe.whitelist()
    def generate_weekly_slots(self):

        # clear existing rows
        self.set("slot_details", [])

        start_time = get_time(self.start_time)
        end_time = get_time(self.end_time)

        for working_day in self.working_days:

            # if not working_day.enabled:
            #     continue

            current = datetime.combine(
                datetime.today(),
                start_time
            )

            end_datetime = datetime.combine(
                datetime.today(),
                end_time
            )

            while current < end_datetime:

                slot_end = current + timedelta(
                    minutes=self.slot_duration
                )

                self.append("slot_details", {
                    "day": working_day.day,
                    "start_time": current.time(),
                    "end_time": slot_end.time(),
                    "capacity": self.max_vehicles_per_slot
                })

                current = slot_end

        # optional sorting by weekday + start time
        day_order = {
            "Monday": 1,
            "Tuesday": 2,
            "Wednesday": 3,
            "Thursday": 4,
            "Friday": 5,
            "Saturday": 6,
            "Sunday": 7
        }

        self.slot_details.sort(
            key=lambda x: (
                day_order.get(x.day, 99),
                x.start_time
            )
        )

        # reset idx properly
        for idx, row in enumerate(self.slot_details, start=1):
            row.idx = idx

        self.save(ignore_permissions=True)

        frappe.db.commit()

        return True