frappe.pages['entry-pass-qr-scanner'].on_page_load = function(wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Entry Pass QR Scanner',
		single_column: true
	});

	$(page.body).html(`
		<div class="qr-scanner-container" style="
			max-width:700px;
			margin:40px auto;
			padding:30px;
			background:#fff;
			border-radius:12px;
			box-shadow:0 2px 10px rgba(0,0,0,0.08);
		">

			<div style="text-align:center;margin-bottom:25px;">
				<h3 style="margin-bottom:8px;">Vehicle Exit Scanner</h3>
				<p style="color:#666;">
					Scan the Entry Pass QR Code to record vehicle exit.
				</p>
			</div>

			<div class="form-group">
				<label><strong>Scan QR Code</strong></label>

				<input
					type="text"
					id="qr_scan_input"
					class="form-control"
					placeholder="Waiting for QR Scan..."
					autocomplete="off"
					autofocus
					style="
						height:50px;
						font-size:20px;
						text-align:center;
						font-weight:bold;
					">
			</div>

			<div id="scan_status"
				style="
					margin-top:20px;
					padding:15px;
					border-radius:8px;
					background:#f8f9fa;
					text-align:center;
					font-size:16px;
				">

				🟡 Waiting for QR Scan...

			</div>

			<div id="vehicle_details" style="margin-top:25px;"></div>

		</div>
	`);

	// Keep cursor always inside scanner input
	const input = $("#qr_scan_input");

	input.focus();

	setInterval(() => {
		input.focus();
	}, 1000);

	// Scanner automatically sends Enter
	input.on("keypress", function(e) {

		if (e.which === 13) {

			const qr = $(this).val().trim();

			if (!qr) return;

			frappe.call({
    method: "rvsf.rvsf.doctype.entry_pass.entry_pass.scan_entry_pass",
    args: {
        entry_pass: qr
    },
    callback: function(r) {

        if (!r.exc && r.message.success) {

            $("#scan_status").html(`
                <div style="color:green;font-weight:bold;">
                    ✔ ${r.message.message}
                </div>
            `);

            $("#vehicle_details").html(`
                <table class="table table-bordered">
                    <tr>
                        <th>Entry Pass</th>
                        <td>${r.message.entry_pass}</td>
                    </tr>
                    <tr>
                        <th>Vehicle</th>
                        <td>${r.message.vehicle}</td>
                    </tr>
                    <tr>
                        <th>Customer</th>
                        <td>${r.message.customer}</td>
                    </tr>
                    <tr>
                        <th>Exit Time</th>
                        <td>${r.message.exit_time}</td>
                    </tr>
                </table>
            `);

            $("#qr_scan_input").val("").focus();
        }
    }
});

			$("#scan_status").html(`
				🟢 Processing...
			`);

			// Next step
			// frappe.call(...)
			// Update Entry Pass
			// Show Vehicle Details

			$(this).val("");
		}
	});
};