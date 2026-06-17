frappe.listview_settings["Execution Job Card"] = {
	has_indicator_for_draft: true,

	get_indicator(doc) {
		const status_colors = {
			"Open": "red",
			"Work In Progress": "orange",
			"On Hold": "light-blue",
		};

		const status = doc.status || "Open";

		return [
			__(status),
			status_colors[status] || "gray",
			`status,=,${status}`
		];
	}
};