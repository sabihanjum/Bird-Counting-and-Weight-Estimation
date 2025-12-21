"""
Configuration settings for Bird Counting and Weight Estimation System
"""
import os
from pathlib import Path

# Project directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "outputs"
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"
MODELS_DIR = BASE_DIR / "models"

# Create directories
OUTPUT_DIR.mkdir(exist_ok=True)
SAMPLE_DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# YOLO model configuration
YOLO_MODEL = "yolov8n.pt"  # Nano model for speed
YOLO_MODEL_PATH = MODELS_DIR / YOLO_MODEL

# Detection parameters (defaults)
DEFAULT_CONF_THRESH = 0.25
DEFAULT_IOU_THRESH = 0.45
DEFAULT_FPS_SAMPLE = 5  # Process every 5th frame

# Tracking parameters
TRACK_THRESH = 0.5  # High confidence track threshold
TRACK_BUFFER = 30  # Maximum frames to keep track alive without detection
MATCH_THRESH = 0.7  # IoU threshold for matching tracks

# Weight estimation parameters
WEIGHT_AREA_FACTOR = 0.15  # Calibration factor for area to weight
WEIGHT_DENSITY_FACTOR = 1.0
MIN_BOX_AREA = 100  # Minimum bounding box area (pixels)

# API settings
API_HOST = "0.0.0.0"
API_PORT = 8000
MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500 MB

# Video output settings
VIDEO_CODEC = "mp4v"
OUTPUT_FPS = 30

# Visualization settings
BOX_COLOR = (0, 255, 0)  # Green
TEXT_COLOR = (255, 255, 255)  # White
FONT_SCALE = 0.6
FONT_THICKNESS = 2
