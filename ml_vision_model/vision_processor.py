#!/usr/bin/env python3
"""
Vision Model Processor - YOLO-based Queen Bee Detection

This module provides a wrapper for YOLOv8 queen bee detection.
Integrates with the main SmartHiveSystem for real-time video processing.

Dependencies:
    - ultralytics (YOLOv8)
    - opencv-python
    - numpy

Author: Smart Hive AI Team
Created: October 2025
"""

import cv2
import logging
import time
import config
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VisionProcessor:
    """
    Wrapper for YOLO-based queen bee detection.
    
    This class handles:
    - Model loading and initialization
    - Frame processing and inference
    - Bounding box extraction
    - Confidence filtering
    
    Attributes:
        model_path (str): Path to YOLO model file (.pt format)
        confidence_threshold (float): Minimum confidence for detection (0.0-1.0)
        enabled (bool): Whether processing is currently enabled
        last_result (dict): Results from last frame processed
        inference_time_ms (float): Time taken for last inference
    
    Example:
        >>> processor = VisionProcessor('models/vision_model.pt', confidence_threshold=0.7)
        >>> frame = cv2.imread('image.jpg')
        >>> result = processor.process_frame(frame)
        >>> print(f"Queen detected: {result['detected']}")
    """
    
    def __init__(self, model_path: str = None, confidence_threshold: float = 0.7, use_camera: bool = True):
        """
        Initialize vision processor with YOLO model.
        
        Args:
            model_path (str): Path to YOLO model file (vision_model.pt). If None, uses config.VISION_MODEL_PATH
            confidence_threshold (float): Minimum confidence for detection (0.5-0.95)
            use_camera (bool): Whether to initialize camera access (for edge-app only, not for vision service)
        
        Raises:
            FileNotFoundError: If model file not found
            RuntimeError: If YOLO initialization fails
        """
        # Use config default if not provided
        if model_path is None:
            model_path = config.VISION_MODEL_PATH
            
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.use_camera = use_camera
        self.enabled = True
        self.last_result = {"detected": False, "confidence": 0.0, "boxes": []}
        self.inference_time_ms = 0.0
        self.model = None
        self.camera = None  # Only initialize if use_camera=True
        
        try:
            logger.info(f"Loading YOLO model from {model_path}")
            # Check if file exists before trying to load
            import os
            if not os.path.exists(model_path):
                logger.error(f"❌ Model file not found: {model_path}")
                logger.warning("Checked paths:")
                logger.warning(f"  - Absolute: {os.path.abspath(model_path)}")
                logger.warning(f"  - CWD: {os.getcwd()}")
                logger.warning(f"  - File exists: {os.path.exists(model_path)}")
                raise FileNotFoundError(f"Model file not found at {model_path}")
            
            from ultralytics import YOLO
            import torch
            
            # Add safe globals for PyTorch 2.6+ compatibility
            # This allows loading YOLO models trained with older PyTorch versions
            try:
                from ultralytics.nn.tasks import DetectionModel
                import torch.nn.modules.container as container
                
                # Add all necessary PyTorch classes for YOLO model loading
                safe_classes = [
                    DetectionModel,
                    container.Sequential,
                    torch.nn.modules.conv.Conv2d,
                    torch.nn.modules.pooling.MaxPool2d,
                    torch.nn.modules.activation.SiLU,
                    torch.nn.modules.batchnorm.BatchNorm2d,
                    torch.nn.modules.upsampling.Upsample,
                ]
                torch.serialization.add_safe_globals(safe_classes)
            except Exception as e:
                logger.warning(f"Could not add PyTorch safe globals: {e}")
            
            self.model = YOLO(model_path)
            logger.info("✅ YOLO model loaded successfully")
        except FileNotFoundError as e:
            logger.error(f"❌ Model file not found: {e}")
            logger.warning("Vision model will be disabled. System will continue without vision detection.")
            self.enabled = False
        except ImportError as e:
            logger.error(f"❌ Import error: {e}")
            logger.warning("Vision model will be disabled. System will continue without vision detection.")
            self.enabled = False
        except Exception as e:
            logger.error(f"❌ Failed to load YOLO model: {type(e).__name__}: {e}")
            logger.warning(f"Working directory: {os.getcwd()}")
            logger.warning(f"Model path: {os.path.abspath(model_path)}")
            logger.warning("Vision model will be disabled. System will continue without vision detection.")
            self.enabled = False
        
        # Initialize camera only if requested (edge-app only, not for vision service)
        if self.use_camera and self.enabled:
            try:
                from real_components import RealVisionProcessor
                camera_config = RealVisionProcessor()
                self.camera = camera_config.camera
                if self.camera and self.camera.isOpened():
                    logger.info("✅ Camera initialized successfully")
                else:
                    logger.warning("⚠️  Camera not available (may be running in mock environment)")
                    self.camera = None
            except Exception as e:
                logger.warning(f"⚠️  Could not initialize camera: {e}")
                self.camera = None
    
    def process_frame(self, frame: cv2.Mat) -> Dict:
        """
        Process a single frame and detect queen bee.
        
        Args:
            frame (cv2.Mat): Input frame in BGR format (OpenCV standard)
        
        Returns:
            Dict with keys:
                - detected (bool): Whether queen bee was detected
                - confidence (float): Max confidence score if detected
                - boxes (List[List[int]]): Bounding boxes [[x1,y1,x2,y2], ...]
                - timestamp (float): Processing timestamp
        
        Raises:
            Exception: If frame processing fails (logged and returned in result)
        """
        if not self.enabled or self.model is None or frame is None:
            return self.last_result
        
        try:
            # Resize if needed (YOLO expects specific dimensions)
            if frame.shape != (480, 640, 3):
                frame = cv2.resize(frame, (640, 480))
            
            # Inference
            start_time = time.time()
            results = self.model.predict(
                frame,
                imgsz=640,
                conf=self.confidence_threshold,
                verbose=False
            )
            self.inference_time_ms = (time.time() - start_time) * 1000
            
            # Parse results
            detected = False
            max_confidence = 0.0
            boxes = []
            
            for result in results:
                if result.boxes is None or len(result.boxes) == 0:
                    continue
                
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    label = self.model.names.get(cls_id, "unknown")
                    confidence = float(box.conf[0])
                    
                    # Only process "queen" class detections
                    if label.lower() == "queen" and confidence >= self.confidence_threshold:
                        detected = True
                        max_confidence = max(max_confidence, confidence)
                        
                        # Extract bounding box coordinates
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        boxes.append([x1, y1, x2, y2])
            
            # Store result
            self.last_result = {
                "detected": detected,
                "confidence": round(max_confidence, 3) if detected else 0.0,
                "boxes": boxes,
                "timestamp": time.time(),
                "inference_time_ms": round(self.inference_time_ms, 2)
            }
            
            if detected:
                logger.debug(f"👑 Queen detected with confidence {max_confidence:.3f}")
            
            return self.last_result
        
        except Exception as e:
            logger.error(f"❌ Frame processing error: {e}")
            return {
                "detected": False,
                "confidence": 0.0,
                "boxes": [],
                "error": str(e)
            }
    
    def draw_detections(self, frame: cv2.Mat, result: Dict) -> cv2.Mat:
        """
        Draw bounding boxes and labels on frame.
        
        Args:
            frame (cv2.Mat): Input frame (BGR format)
            result (Dict): Detection result from process_frame()
        
        Returns:
            cv2.Mat: Frame with drawn detections
        """
        output = frame.copy()
        
        if result.get("detected", False):
            for box in result.get("boxes", []):
                x1, y1, x2, y2 = box
                # Draw red rectangle
                cv2.rectangle(output, (x1, y1), (x2, y2), (0, 0, 255), 2)
                # Draw label
                label = f"Queen ({result['confidence']:.2f})"
                cv2.putText(
                    output, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2
                )
        
        # Add status text
        status_text = "Vision: Active" if self.enabled else "Vision: Disabled"
        cv2.putText(output, status_text, (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        return output
    
    def enable(self):
        """Enable vision processing."""
        if self.model is not None:
            self.enabled = True
            logger.info("✅ Vision processing enabled")
    
    def disable(self):
        """Disable vision processing."""
        self.enabled = False
        logger.info("⏹ Vision processing disabled")
    
    def get_status(self) -> Dict:
        """Get current vision processor status."""
        return {
            "enabled": self.enabled,
            "model_loaded": self.model is not None,
            "last_result": self.last_result,
            "inference_time_ms": self.inference_time_ms
        }
