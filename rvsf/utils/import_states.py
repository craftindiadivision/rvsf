import json
import frappe
import os

def import_states_and_districts():
    path = frappe.get_app_path(
        "rvsf",
        "setup",
        "india_states_districts_latest.json"
    )

    print("App Path:", frappe.get_app_path("rvsf"))
    print("Setup Path:", frappe.get_app_path("rvsf", "setup"))
    print("Full Path:", path)
    print("Exists:", os.path.exists(path))
    print(path,333333333333333399999999999999999999999999999999999)
    print(path)
    print(os.path.exists(path))
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(22222222244444444444444444)
    for item in data:
        state_name = item.get("state")

        if not state_name:
            continue
        print(444444444444444444444444)
        # Create State if it doesn't exist
        state_doc_name = frappe.db.exists("State", {"state": state_name})

        if not state_doc_name:
            state_doc = frappe.new_doc("State")
            state_doc.state = state_name
            state_doc.insert(ignore_permissions=True)
            state_doc_name = state_doc.name
            print(f"Created State: {state_name}")
        else:
            print(f"State already exists: {state_name}")

        # Create Districts
        for district_name in item.get("districts", []):
            if not frappe.db.exists(
                "District",
                {
                    "district": district_name,
                    "state": state_doc_name,
                },
            ):
                district_doc = frappe.new_doc("District")
                district_doc.district = district_name
                district_doc.state = state_doc_name
                district_doc.insert(ignore_permissions=True)
                print(f"   Created District: {district_name}")
            else:
                print(f"   District already exists: {district_name}")

    frappe.db.commit()
    print("States and Districts imported successfully.")