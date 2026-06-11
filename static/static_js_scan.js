// JS for QR scanning (for index.html)
function onScanSuccess(decodedText, decodedResult) {
    // Send scanned QR (email) to backend
    fetch('/scan', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ email: decodedText })   // FIXED
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
    })
    .catch(() => alert('Error marking attendance.'));
}

if (window.Html5QrcodeScanner) {
    let html5QrcodeScanner = new Html5QrcodeScanner(
        "reader", { fps: 10, qrbox: 250 });
    html5QrcodeScanner.render(onScanSuccess);
}