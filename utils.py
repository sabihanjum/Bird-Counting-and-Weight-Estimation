"""
Utility functions for video processing and analysis
"""
import cv2
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


def extract_video_metadata(video_path: str) -> Dict:
    """Extract metadata from video file"""
    cap = cv2.VideoCapture(video_path)
    
    metadata = {
        'fps': cap.get(cv2.CAP_PROP_FPS),
        'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        'duration_seconds': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
    }
    
    cap.release()
    return metadata


def frame_to_timestamp(frame_idx: int, fps: float) -> str:
    """Convert frame index to timestamp string HH:MM:SS"""
    seconds = frame_idx / fps
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def calculate_iou(box1: np.ndarray, box2: np.ndarray) -> float:
    """Calculate Intersection over Union"""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0


def calculate_bbox_area(bbox: np.ndarray) -> float:
    """Calculate bounding box area"""
    return (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])


def get_bbox_center(bbox: np.ndarray) -> tuple:
    """Get bounding box center coordinates"""
    cx = (bbox[0] + bbox[2]) / 2
    cy = (bbox[1] + bbox[3]) / 2
    return cx, cy


def save_json_output(data: Dict, output_path: Path):
    """Save analysis results to JSON file"""
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)


def generate_color_for_id(track_id: int) -> tuple:
    """Generate consistent color for track ID"""
    np.random.seed(track_id)
    return tuple(map(int, np.random.randint(0, 255, 3)))


def draw_bbox_with_label(frame: np.ndarray, bbox: List, label: str, color: tuple) -> np.ndarray:
    """Draw bounding box with label on frame"""
    x1, y1, x2, y2 = map(int, bbox)
    
    # Draw rectangle
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    
    # Draw label background
    label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
    cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), 
                  (x1 + label_size[0], y1), color, -1)
    
    # Draw label text
    cv2.putText(frame, label, (x1, y1 - 5), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    return frame


def draw_count_overlay(frame: np.ndarray, count: int, timestamp: str) -> np.ndarray:
    """Draw bird count and timestamp overlay"""
    # Draw background
    cv2.rectangle(frame, (10, 10), (300, 80), (0, 0, 0), -1)
    
    # Draw count
    cv2.putText(frame, f"Count: {count}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # Draw timestamp
    cv2.putText(frame, f"Time: {timestamp}", (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    return frame


def create_output_filename(input_filename: str, suffix: str, extension: str) -> str:
    """Create output filename with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = Path(input_filename).stem
    return f"{base_name}_{suffix}_{timestamp}.{extension}"
