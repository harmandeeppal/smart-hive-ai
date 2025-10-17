from picamera2 import Picamera2
import cv2
from ultralytics import YOLO
import numpy as np
import os
from datetime import datetime

# Paths
INPUT_DIR = "inputs"
OUTPUT_DIR = "outputs"
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load YOLO model
model = YOLO("best.pt")

# Initialize Picamera2
picam2 = Picamera2()
preview_config = picam2.create_preview_configuration(main={"size": (640, 480)})
picam2.configure(preview_config)
picam2.start()

print("✅ NOIR camera started. Press SPACE to capture & detect, Q to quit.")

while True:
    frame = picam2.capture_array()

    # Show live feed
    cv2.imshow("Live Feed", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

    elif key == 32:  # SPACE key pressed
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_path = os.path.join(INPUT_DIR, f"input_{timestamp}.jpg")
        output_path = os.path.join(OUTPUT_DIR, f"output_{timestamp}.jpg")

        # Save input image
        cv2.imwrite(input_path, frame)

        # Convert frame for YOLO if necessary
        if len(frame.shape) == 2 or frame.shape[2] == 1:
            frame_input = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
        else:
            frame_input = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Run YOLO detection
        results = model.predict(frame_input, imgsz=640, conf=0.1)
        output = frame.copy()
        detected = False

        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls_id = int(box.cls[0])
                label = model.names[cls_id]
                if label.lower() == "queen":
                    detected = True
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(output, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(
                        output,
                        "Queen",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 0, 255),
                        2,
                    )

        # Add detection text
        text = "Queen detected" if detected else "No queen"
        color = (0, 255, 0) if detected else (0, 0, 255)
        cv2.putText(output, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        # Show output and save it
        cv2.imshow("Detection Result", output)
        cv2.imwrite(output_path, output)

        print(f"📸 Saved input: {input_path}")
        print(f"✅ Saved output: {output_path}")
        print(f"🟢 Result: {text}")

        cv2.waitKey(0)
        cv2.destroyWindow("Detection Result")

picam2.stop()
cv2.destroyAllWindows()

