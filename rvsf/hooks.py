app_name = "rvsf"
app_title = "Rvsf"
app_publisher = "saheer"
app_description = "SILK custom app"
app_email = "saheercp26@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "rvsf",
# 		"logo": "/assets/rvsf/logo.png",
# 		"title": "Rvsf",
# 		"route": "/rvsf",
# 		"has_permission": "rvsf.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/rvsf/css/rvsf.css"
# app_include_js = "/assets/rvsf/js/rvsf.js"

# include js, css files in header of web template
# web_include_css = "/assets/rvsf/css/rvsf.css"
# web_include_js = "/assets/rvsf/js/rvsf.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "rvsf/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Supplier Quotation": "public/js/supplier_quotation.js",
    "Purchase Order": "public/js/purchase_order.js",
    "Purchase Receipt": "public/js/purchase_receipt.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "rvsf/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "rvsf.utils.jinja_methods",
# 	"filters": "rvsf.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "rvsf.install.before_install"
# after_install = "rvsf.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "rvsf.uninstall.before_uninstall"
# after_uninstall = "rvsf.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "rvsf.utils.before_app_install"
# after_app_install = "rvsf.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "rvsf.utils.before_app_uninstall"
# after_app_uninstall = "rvsf.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "rvsf.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "rvsf.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }
doc_events = {
    "Stock Entry": {
        "validate": "rvsf.rvsf.events.stock_entry.validate",
        "on_cancel": "rvsf.rvsf.events.stock_entry.on_cancel",
        "on_submit": "rvsf.rvsf.events.stock_entry.on_submit"
    },
    "Purchase Receipt": {
        "validate": "rvsf.rvsf.events.purchase_receipt.validate_purchase_receipt",
        "on_submit": "rvsf.rvsf.events.purchase_receipt.on_submit",
    },
    "Purchase Order": {
        "on_submit": "rvsf.rvsf.events.purchase_order.on_submit",
        "on_cancel": "rvsf.rvsf.events.purchase_order.on_cancel"
    }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"rvsf.tasks.all"
# 	],
# 	"daily": [
# 		"rvsf.tasks.daily"
# 	],
# 	"hourly": [
# 		"rvsf.tasks.hourly"
# 	],
# 	"weekly": [
# 		"rvsf.tasks.weekly"
# 	],
# 	"monthly": [
# 		"rvsf.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "rvsf.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "rvsf.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "rvsf.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "rvsf.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["rvsf.utils.before_request"]
# after_request = ["rvsf.utils.after_request"]

# Job Events
# ----------
# before_job = ["rvsf.utils.before_job"]
# after_job = ["rvsf.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"rvsf.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

fixtures = [
    {
        "dt": "Workflow",
        "filters": [
            ["name", "in", ["Supplier Quotation","Gate Pass","Physical Verification","Security Check"]]
        ]
    },
    {
        "dt": "Custom Field",
        "filters": [
            [
                "name",
                "in",
                [
                    "Item-custom_vehicle_details",
                    "Item-custom_vehicle_registration_no",
                    "Item-custom_maker_name",
                    "Item-custom_model_name",
                    "Item-custom_monthyear_of_manufacture",
                    "Item-custom_chassis_no",
                    "Item-custom_engine_no",
                    "Item-custom_state_name",
                    "Item-custom_rto_name",
                    "Supplier Quotation-custom_purchase_lead",
                    "Item-custom_column_break_ylzr4",
                    "Item-custom_column_break_hx6lh",
                    "Supplier Quotation-custom_reason_for_rejection",
                    "Supplier Quotation-custom_reason",
                    "Item-custom_ownership_type",
                    "Stock Entry-custom_execution_order",
                    "Operation-custom_is_recovery_operation",
                    "Purchase Order-custom_purchase_lead",
                    "Purchase Receipt-custom_purchase_lead",
                    "Purchase Receipt-custom_cod",
                    "Purchase Receipt-custom_cod_details",
                    "Purchase Receipt-custom_certificate_of_deposit",
                    "Purchase Receipt-custom_gross_weight",
                    "Purchase Receipt-custom_weight_details",
                    "Purchase Receipt-custom_rc_weight",
                    "Purchase Receipt-custom_get_weight_details",
                    "Purchase Receipt-custom_cost_details",
                    "Purchase Receipt-custom_scrap_cost_per_kg",
                    "Purchase Receipt-custom_scrap_amount",
                    "Supplier Quotation-custom_signature",
                    "Supplier Quotation-custom_customer_sign"
                ]
            ]
        ]
    },
    {
        "dt": "Property Setter",
        "filters": [
            [
                "name",
                "in",
                [
                    "Item-main-field_order",
                    "Supplier Quotation-main-field_order",
                    "Vehicle-last_odometer-reqd",
                    "Vehicle-uom-default",
                    "Stock Entry-main-field_order",
                    "Operation-main-field_order",
                    "Purchase Order-main-field_order",
                    "Purchase Receipt-main-field_order",
                    "Purchase Order-main-links_order",
                    "Purchase Receipt-main-links_order",
                    "Supplier Quotation-main-field_order"
                    
                ]   
            ]
        ]
    },
    {
    "dt": "Workflow State",
    "filters": [
        ["name", "in", [
            "Draft","Sent","Revised","Rejected","Accepted","Cancelled","Issued","Valid","Invalid","Inspected","Verified", "Authorised","Submitted", "Under Valuation", 
            "Valuation Approved", "Yard Entry Approved", "Yard Entry Rejected", "Under Review"
        ]]
    ]
    },
    {
    "dt": "Workflow Action Master",
    "filters": [
        ["name", "in", [
            "Sent To Supplier","Revise","Reject","Accept","Cancel","Issue","Valid","Invalid","Inspect","Verify","Authorise", "Submit","Send For Valuation","Approve Valuation",
            "Approve Yard Entry","Reject Yard Entry"
        ]]
    ]
    },
]