document.addEventListener("DOMContentLoaded", () => {
  const startButton = document.getElementById("startScan");
  const readerElement = document.getElementById("reader");
  const statusElement = document.getElementById("scannerStatus");
  const resultElement = document.getElementById("scanResult");

  let html5QrCode = null;
  let scanning = false;

  function updateStatus(message) {
    if (statusElement) {
      statusElement.textContent = message;
    }
  }

  function updateResult(message) {
    if (resultElement) {
      resultElement.textContent = message;
    }
  }

  function resetScanner() {
    if (html5QrCode) {
      html5QrCode.stop().catch(() => {}).finally(() => html5QrCode.clear().catch(() => {}));
      html5QrCode = null;
    }
    scanning = false;
    if (startButton) {
      startButton.innerHTML = '<i class="fas fa-camera-retro me-2"></i>Start Scan';
      startButton.classList.remove("active");
    }
    updateStatus("Scanner stopped");
  }

  function onScanSuccess(decodedText) {
    if (!scanning) {
      return;
    }
    resetScanner();
    updateStatus("QR scanned successfully");
    updateResult(decodedText);

    fetch("/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ student_id: decodedText }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.status === "success") {
          updateStatus(data.message);
          updateResult(`${data.student_name} · ${data.attendance_status || "Present"}`);
        } else {
          updateStatus(data.message || "Unable to record attendance.");
        }
      })
      .catch(() => {
        updateStatus("Network error while sending scan data.");
      });
  }

  function onScanError(_) {
    // Ignored scan errors during camera preview.
  }

  function startScanner() {
    if (!readerElement || scanning || typeof Html5Qrcode === "undefined") {
      updateStatus("QR scanner unavailable.");
      return;
    }

    html5QrCode = new Html5Qrcode("reader");
    html5QrCode
      .start(
        { facingMode: "environment" },
        { fps: 10, qrbox: { width: 280, height: 280 } },
        onScanSuccess,
        onScanError
      )
      .then(() => {
        scanning = true;
        if (startButton) {
          startButton.innerHTML = '<i class="fas fa-stop me-2"></i>Stop Scan';
          startButton.classList.add("active");
        }
        updateStatus("Point the camera at the QR code.");
      })
      .catch(() => {
        updateStatus("Unable to access camera. Please allow camera permissions.");
      });
  }

  if (startButton) {
    startButton.addEventListener("click", (event) => {
      event.preventDefault();
      if (scanning) {
        resetScanner();
      } else {
        startScanner();
      }
    });
  }

  document.querySelectorAll(".delete-form").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!confirm("Delete this student and their attendance history?")) {
        event.preventDefault();
      }
    });
  });
});
