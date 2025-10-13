# Queen Bee Detection - Testing Guide

## 🐝 Question 2: Testing Queen Detection with Photos

### Current Status ⚠️

**The AI model (`queen_bee.tflite`) is a PLACEHOLDER and will NOT detect real queens accurately.**

Why?
- The TFLite model needs to be **trained on actual bee images**
- Currently using a generic object detection model
- Requires dataset of queen bee images for training

---

## 🎯 How Queen Detection Currently Works

### Architecture Overview

```
Camera → OpenCV Frame → TFLite Model → Bounding Box + Confidence
         (640x480)      (320x320 input)   [ymin, xmin, ymax, xmax]
```

### Code Flow (`real_components.py`)

```python
class RealVisionProcessor:
    def __init__(self, model_path):
        self.interpreter = tflite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        # Model expects 320x320x3 input
    
    def detect_queen(self, frame):
        # 1. Resize frame to 320x320
        input_data = cv2.resize(frame, (320, 320))
        
        # 2. Run TFLite inference
        self.interpreter.set_tensor(input_index, input_data)
        self.interpreter.invoke()
        
        # 3. Get output (bounding boxes, classes, scores)
        boxes = self.interpreter.get_tensor(output_boxes_index)
        scores = self.interpreter.get_tensor(output_scores_index)
        
        # 4. Filter by confidence threshold (>0.5)
        if scores[0] > 0.5:
            return (boxes[0], scores[0])
        
        return (None, None)
```

---

## 📸 Method 1: Test with Static Image (Recommended)

### Step 1: Add Test Image Function

Add this to `real_components.py`:

```python
def test_image_detection(self, image_path):
    """Test queen detection on a static image file."""
    try:
        # Load image from file
        frame = cv2.imread(image_path)
        
        if frame is None:
            print(f"❌ Error: Could not load image from {image_path}")
            return None
        
        print(f"✅ Loaded image: {image_path} (Shape: {frame.shape})")
        
        # Run detection
        box, confidence = self.detect_queen(frame)
        
        if box is not None:
            print(f"🐝 QUEEN DETECTED!")
            print(f"   Confidence: {confidence:.2%}")
            print(f"   Bounding Box: {box}")
            
            # Draw box on image
            h, w, _ = frame.shape
            x_min, y_min = int(box[1] * w), int(box[0] * h)
            x_max, y_max = int(box[3] * w), int(box[2] * h)
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 3)
            
            # Add confidence label
            label = f"Queen: {confidence:.0%}"
            cv2.putText(frame, label, (x_min, y_min - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
            # Save annotated image
            output_path = image_path.replace('.jpg', '_detected.jpg')
            cv2.imwrite(output_path, frame)
            print(f"✅ Saved annotated image: {output_path}")
            
            return (box, confidence, output_path)
        else:
            print("❌ No queen detected in image")
            return None
            
    except Exception as e:
        print(f"❌ Error testing image: {e}")
        return None
```

### Step 2: Create Test Script

Create `test_queen_detection.py`:

```python
#!/usr/bin/env python3
"""
Test queen bee detection on a static image.
Usage: python test_queen_detection.py path/to/bee_image.jpg
"""

import sys
import cv2
from real_components import RealVisionProcessor

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_queen_detection.py <image_path>")
        print("Example: python test_queen_detection.py test_images/hive_frame.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    print("="*60)
    print("🐝 Smart Hive AI - Queen Detection Test")
    print("="*60)
    print(f"Testing image: {image_path}")
    print(f"Model: queen_bee.tflite")
    print("-"*60)
    
    # Initialize vision processor
    processor = RealVisionProcessor(model_path="queen_bee.tflite")
    
    # Test detection
    result = processor.test_image_detection(image_path)
    
    if result:
        box, confidence, output_path = result
        print("="*60)
        print("✅ DETECTION SUCCESSFUL")
        print(f"📊 Confidence: {confidence:.2%}")
        print(f"📦 Bounding Box: {box}")
        print(f"💾 Annotated image saved: {output_path}")
        print("="*60)
    else:
        print("="*60)
        print("❌ NO QUEEN DETECTED")
        print("="*60)
        print("\nPossible reasons:")
        print("  • Image doesn't contain a queen bee")
        print("  • Model not trained on bee images")
        print("  • Confidence threshold too high (>50%)")
        print("  • Image quality/lighting issues")

if __name__ == "__main__":
    main()
```

### Step 3: Run Test

```bash
# Create test images folder
mkdir test_images

# Add a bee image (download from internet or use your own)
# Example: hive_frame.jpg, queen_bee.jpg, bee_cluster.jpg

# Run test
python test_queen_detection.py test_images/hive_frame.jpg
```

**Expected Output:**
```
============================================================
🐝 Smart Hive AI - Queen Detection Test
============================================================
Testing image: test_images/hive_frame.jpg
Model: queen_bee.tflite
------------------------------------------------------------
✅ Loaded image: test_images/hive_frame.jpg (Shape: (1080, 1920, 3))
🐝 QUEEN DETECTED!
   Confidence: 87.50%
   Bounding Box: [0.45, 0.32, 0.58, 0.41]
✅ Saved annotated image: test_images/hive_frame_detected.jpg
============================================================
✅ DETECTION SUCCESSFUL
📊 Confidence: 87.50%
📦 Bounding Box: [0.45, 0.32, 0.58, 0.41]
💾 Annotated image saved: test_images/hive_frame_detected.jpg
============================================================
```

---

## 📸 Method 2: Upload Image to Dashboard (Future Enhancement)

### Add Upload Endpoint to Dashboard

This would allow you to upload images through the web interface:

```python
# In dashboard_app.py

@app.route('/test_detection', methods=['POST'])
def test_detection():
    """Upload an image to test queen detection."""
    if 'image' not in request.files:
        return jsonify({'error': 'No image file'}), 400
    
    file = request.files['image']
    
    # Save temporarily
    temp_path = f"/tmp/test_{int(time.time())}.jpg"
    file.save(temp_path)
    
    # Forward to edge device for processing
    # (Would need API endpoint on edge device)
    
    return jsonify({'status': 'Processing...', 'image_path': temp_path})
```

---

## 🎓 Training Your Own Model (Advanced)

### Why You Need Custom Training

The placeholder model doesn't know what a queen bee looks like. You need:

1. **Dataset**: 500-1000 images of bee frames
2. **Annotations**: Bounding boxes around queen bees
3. **Training**: YOLOv5/YOLOv8 training on your dataset
4. **Conversion**: PyTorch → TFLite format

### Simplified Training Process

```bash
# 1. Collect images of your hive frames
#    - Take 500+ photos with your USB camera
#    - Include various lighting conditions
#    - Ensure queen is visible in ~200 images

# 2. Annotate using LabelImg
pip install labelImg
labelImg

# 3. Train YOLOv5
git clone https://github.com/ultralytics/yolov5
cd yolov5
pip install -r requirements.txt

# Create dataset.yaml:
# train: ../bee_dataset/images/train
# val: ../bee_dataset/images/val
# nc: 1  # Number of classes (just "queen")
# names: ['queen']

python train.py --img 320 --batch 16 --epochs 100 \
  --data dataset.yaml --weights yolov5s.pt

# 4. Export to TFLite
python export.py --weights runs/train/exp/weights/best.pt \
  --include tflite --img 320

# 5. Copy to project
cp runs/train/exp/weights/best-fp16.tflite ../queen_bee.tflite
```

### Easier Alternative: Use Pre-trained Bee Detection Model

Check if there's an existing model:
- https://universe.roboflow.com (search "bee queen detection")
- Kaggle datasets
- GitHub repositories

---

## 🧪 Testing Strategy

### Phase 1: Validate Model Loading
```python
# Does the model load without errors?
processor = RealVisionProcessor("queen_bee.tflite")
# ✅ Should print: "Initialized Real Vision Processor"
```

### Phase 2: Test with Known Images
```bash
# Test images you KNOW contain queens
python test_queen_detection.py test_images/confirmed_queen.jpg

# Test images you KNOW are queen-less
python test_queen_detection.py test_images/worker_bees_only.jpg
```

### Phase 3: Live Camera Test
```python
# Capture a frame and test
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
box, conf = processor.detect_queen(frame)
print(f"Detection result: {box}, {conf}")
```

### Phase 4: Production Validation
```bash
# Let system run for 1 hour
# Check MQTT messages for queen detections
# Verify S3 uploaded images match detection events
```

---

## 📊 Evaluation Metrics

### For Your Thesis

Track these metrics:
- **True Positives**: Correctly detected queens
- **False Positives**: Detected queen when none present
- **False Negatives**: Missed queen that was present
- **Precision**: TP / (TP + FP)
- **Recall**: TP / (TP + FN)
- **F1 Score**: 2 × (Precision × Recall) / (Precision + Recall)

### Example Results Table

| Image Set | True Positives | False Positives | False Negatives | Precision | Recall |
|-----------|---------------|-----------------|-----------------|-----------|--------|
| Test Set 1 (n=50) | 42 | 3 | 5 | 93.3% | 89.4% |
| Test Set 2 (n=100) | 87 | 8 | 5 | 91.6% | 94.6% |

---

## ⚠️ Important Notes

### Current Limitations

1. **Model is placeholder** - Will not detect real queens until trained
2. **No dataset included** - You must collect your own images
3. **Training required** - Needs 500+ annotated images
4. **Hardware dependent** - Raspberry Pi 4 recommended (Pi 3 is slow)

### Expected Performance

- **With placeholder model**: Random/no detections
- **With custom-trained model**: 80-95% accuracy (depends on dataset quality)
- **Processing speed**: ~2-5 FPS on Raspberry Pi 4

---

## ✅ Quick Test Checklist

- [ ] Download sample bee images from internet
- [ ] Add `test_image_detection()` function to `real_components.py`
- [ ] Create `test_queen_detection.py` script
- [ ] Run test on sample images
- [ ] Check if model loads successfully
- [ ] Verify output image shows bounding box
- [ ] Document results for thesis

---

## 🚀 Next Steps

1. **Immediate**: Test with any bee image to verify system works
2. **Short-term**: Collect 50-100 images from your actual hive
3. **Medium-term**: Annotate images and train custom model
4. **Long-term**: Deploy trained model and validate accuracy

**Bottom Line**: The infrastructure is ready. You just need to train the model on real bee data! 🐝
