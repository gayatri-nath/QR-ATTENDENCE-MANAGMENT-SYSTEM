import cv2

# Initialize OpenCV QR code detector
detector = cv2.QRCodeDetector()

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame")
        break
=---=    data, points, _ = detector.detectAndDecode(frame)
    if data:
        print(f"Scanned Data: {data}")
        # Optional: Save to your attendance database here
        break

    cv2.imshow("QR Code Scanner - press 'q' to quit", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows() 