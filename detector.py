"""
Bird detection using YOLOv8
"""
import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Tuple
import logging

from config import YOLO_MODEL, DEFAULT_CONF_THRESH, DEFAULT_IOU_THRESH

logger = logging.getLogger(__name__)


class BirdDetector:
    """
    Bird detection using YOLOv8 pretrained model.
    Detects birds (class 14 in COCO dataset) with bounding boxes.
    """
    
    def __init__(self, conf_thresh: float = DEFAULT_CONF_THRESH, 
                 iou_thresh: float = DEFAULT_IOU_THRESH):
        """
        Initialize bird detector
        
        Args:
            conf_thresh: Confidence threshold for detections
            iou_thresh: IoU threshold for NMS
        """
        self.conf_thresh = conf_thresh
        self.iou_thresh = iou_thresh
        
        logger.info(f"Loading YOLOv8 model: {YOLO_MODEL}")
        self.model = YOLO(YOLO_MODEL)
        logger.info("YOLOv8 model loaded successfully")
        
    def detect(self, frame: np.ndarray) -> List[List]:
        """
        Detect birds in frame
        
        Args:
            frame: Input image frame
            
        Returns:
            List of detections [x1, y1, x2, y2, confidence]
        """
        # Run detection
        results = self.model(frame, conf=self.conf_thresh, 
                           iou=self.iou_thresh, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Filter for bird class (class 14 in COCO dataset)
                if int(box.cls) == 14:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf)
                    detections.append([x1, y1, x2, y2, conf])
        
        return detections
