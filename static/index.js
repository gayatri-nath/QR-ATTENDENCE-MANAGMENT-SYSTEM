document.addEventListener('DOMContentLoaded', () => {
    const statusText = document.getElementById('scannerStatus');
    const scanResult = document.getElementById('scanResult');
    const startButton = document.getElementById('startScan');
    const reader = document.getElementById('reader');

    let html5QrCode;
    let scanning = false;

    const updateButton = () => {
        if (scanning) {
            startButton.innerHTML = '<i class="fas fa-stop-circle me-2"></i>Stop Camera';
            startButton.classList.remove('btn-secondary');
            startButton.classList.add('btn-primary');
        } else {
            startButton.innerHTML = '<i class="fas fa-camera-retro me-2"></i>Start Camera';
            startButton.classList.remove('btn-primary');
            startButton.classList.add('btn-secondary');
        }
    };

    const setStatus = (message) => {
        statusText.textContent = message;
    };

    const setResult = (message) => {
        scanResult.textContent = message;
    };

    const stopScanner = () => {
        if (!html5QrCode) return Promise.resolve();
        return html5QrCode.stop().then(() => {
            scanning = false;
            updateButton();
            setStatus('Ready to scan');
            setResult('No scan yet');
        });
    };

    const startScanner = () => {
        if (!html5QrCode) {
            html5QrCode = new Html5Qrcode('reader');
        }

        return html5QrCode.start(
            { facingMode: 'environment' },
            {
                fps: 10,
                qrbox: { width: 260, height: 260 },
                disableFlip: false,
            },
            (decodedText) => {
                setStatus('QR code detected');
                setResult(decodedText);
            },
            (errorMessage) => {
                setStatus('Scanning...');
            }
        ).then(() => {
            scanning = true;
            updateButton();
            setStatus('Camera activated. Scanning...');
            setResult('Waiting for QR code');
        }).catch((err) => {
            setStatus('Unable to start camera');
            console.error(err);
        });
    };

    startButton.addEventListener('click', () => {
        if (scanning) {
            stopScanner().catch((err) => {
                setStatus('Error stopping camera');
                console.error(err);
            });
        } else {
            startScanner();
        }
    });

    updateButton();
});
