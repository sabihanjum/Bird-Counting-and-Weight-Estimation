# Bird Counting and Weight Estimation from Poultry CCTV Videos

## Overview

This project implements a comprehensive computer vision system for analyzing poultry farm CCTV footage to **count birds** and **estimate weights** from video. The system uses state-of-the-art deep learning models (YOLOv8) for detection and ByteTrack algorithm for robust multi-object tracking with stable ID assignment.

## Features

### ✅ Bird Counting (Mandatory)
- **Detection**: YOLOv8-based bird detection with bounding boxes and confidence scores
- **Tracking**: ByteTrack algorithm for stable ID assignment across frames
- **Count Over Time**: Timestamp → count mapping with frame-by-frame analysis
- **Occlusion Handling**: Track persistence across missing detections (up to 30 frames)
- **ID Switch Prevention**: IoU-based matching with confidence thresholds
- **Double-Counting Prevention**: Unique track IDs maintained throughout video lifecycle

### ✅ Weight Estimation (Mandatory)
- **Feature-Based Approach**: Uses bounding box area as primary feature
- **Weight Proxy/Index**: Outputs relative weight index (not absolute grams)
- **Calibration Support**: Framework for converting index to grams with ground truth
- **Per-Bird Estimates**: Individual weight indices for each tracked bird
- **Aggregate Statistics**: Mean, median, std, min, max across all birds
- **Confidence Scores**: Uncertainty estimation based on observation count and quality

### ✅ Artifacts Generation
- **Annotated Video**: Bounding boxes, tracking IDs, count overlay, timestamps
- **JSON Output**: Complete analysis results with counts, tracks, and weights
- **Visualization**: Color-coded tracks with consistent colors per ID

### ✅ FastAPI Service
- **GET /health**: Health check endpoint
- **POST /analyze_video**: Video analysis with configurable parameters
- **Interactive Docs**: Swagger UI at `/docs` and ReDoc at `/redoc`

## Project Structure

```
Bird Counting and Weight Estimation/
├── main.py                    # FastAPI application
├── detector.py                # YOLOv8 bird detection
├── tracker.py                 # ByteTrack tracking algorithm
├── weight_estimator.py        # Weight estimation module
├── video_processor.py         # Video processing pipeline
├── utils.py                   # Utility functions
├── config.py                  # Configuration settings
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── .env.example              # Environment variables template
├── outputs/                   # Generated outputs
│   ├── annotated videos
│   └── JSON results
├── sample_data/               # Sample input videos
└── models/                    # Downloaded YOLO models
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip package manager
- (Optional) CUDA-capable GPU for faster processing
- (Optional) FFmpeg for additional video codec support

### Installation

1. **Clone or extract the project**:
   ```bash
   cd "Bird Counting and Weight Estimation"
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

   This will install:
   - FastAPI & Uvicorn (API framework)
   - OpenCV (video processing)
   - Ultralytics YOLOv8 (object detection)
   - PyTorch (deep learning backend)
   - NumPy, SciPy, scikit-learn (numerical computing)
   - FilterPy (Kalman filtering for tracking)

4. **Download YOLOv8 model** (automatic on first run):
   The YOLOv8 nano model (`yolov8n.pt`) will be automatically downloaded on first use.

## Running the API

### Start the Server

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### API Documentation

Interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Usage

### 1. Health Check

```bash
curl http://localhost:8000/health
```

**Response**:
```json
{
  "status": "OK",
  "message": "Bird Counting API is running"
}
```

### 2. Analyze Video

#### Windows PowerShell:

```powershell
curl.exe -X POST "http://localhost:8000/analyze_video" `
  -F "video=@sample_data/poultry_video.mp4" `
  -F "fps_sample=5" `
  -F "conf_thresh=0.25" `
  -F "iou_thresh=0.45" `
  -o response.json
```

#### Linux/Mac:

```bash
curl -X POST "http://localhost:8000/analyze_video" \
  -F "video=@sample_data/poultry_video.mp4" \
  -F "fps_sample=5" \
  -F "conf_thresh=0.25" \
  -F "iou_thresh=0.45" \
  -o response.json
```

#### Parameters:

- `video` (required): Video file to analyze (mp4, avi, mov, mkv)
- `fps_sample` (optional, default=5): Process every Nth frame
  - 1 = all frames (slowest, most accurate)
  - 5 = every 5th frame (recommended balance)
  - 10 = every 10th frame (fastest, may miss fast movements)
- `conf_thresh` (optional, default=0.25): Detection confidence threshold (0.0-1.0)
  - Lower values: More detections, more false positives
  - Higher values: Fewer detections, fewer false positives
- `iou_thresh` (optional, default=0.45): IoU threshold for NMS (0.0-1.0)

#### Response Structure:

```json
{
  "counts": [
    {
      "timestamp": "00:00:00",
      "count": 15,
      "frame": 0
    },
    {
      "timestamp": "00:00:01",
      "count": 16,
      "frame": 30
    }
  ],
  "tracks_sample": [
    {
      "track_id": 1,
      "boxes": [[100.5, 200.3, 150.8, 250.6], ...],
      "confidences": [0.89, 0.92, ...]
    }
  ],
  "weight_estimates": {
    "unit": "index",
    "per_bird": [
      {
        "track_id": 1,
        "weight_index": 245.3,
        "confidence": 0.85,
        "num_observations": 120
      }
    ],
    "aggregate": {
      "mean_weight_index": 238.5,
      "std": 15.2,
      "median_weight_index": 240.1,
      "min_weight_index": 180.3,
      "max_weight_index": 295.7,
      "total_birds": 18
    },
    "calibration_note": "Weight index based on bird area. Requires calibration with known weights.",
    "methodology": {
      "features": [
        "Bounding box area (pixels²)",
        "Track confidence (detection reliability)",
        "Temporal consistency (number of observations)"
      ],
      "assumptions": [
        "Fixed camera position and angle",
        "Birds on flat surface",
        "Consistent lighting conditions",
        "Camera height remains constant"
      ]
    }
  },
  "artifacts": {
    "annotated_video": "outputs/video_annotated_20231218_143022.mp4",
    "tracks_json": "outputs/video_tracks_20231218_143022.json"
  },
  "video_info": {
    "filename": "poultry_video.mp4",
    "total_frames_processed": 450,
    "total_tracks": 25
  }
}
```

## Implementation Details

### 1. Bird Counting Method

#### Detection
- **Model**: YOLOv8 nano (yolov8n.pt) pretrained on COCO dataset
- **Bird Class**: COCO class 14 (bird)
- **Process**: Frame → YOLO → Bounding boxes + confidences
- **NMS**: Non-Maximum Suppression to eliminate duplicate detections

#### Tracking
- **Algorithm**: ByteTrack (simple implementation)
- **Features**:
  - IoU-based matching between detections and tracks
  - Two-stage association (high confidence, then low confidence)
  - Track buffer for handling occlusions (30 frames default)
  - Greedy matching for detection-to-track assignment

#### Handling Occlusions
- Tracks remain active for up to 30 frames without detections
- Re-association when bird reappears using IoU matching
- Age tracking: tracks age +1 per frame without detection
- Dead track removal: tracks with age > track_buffer are deleted

#### Preventing ID Switches
- High IoU threshold (0.7) for confident matches
- Two-stage matching (high conf first, low conf for remaining)
- Consistent track ID throughout bird's lifetime
- New ID only assigned to unmatched high-confidence detections

#### Avoiding Double-Counting
- Each detection matched to at most one track
- Unique track IDs prevent counting same bird multiple times
- Track count = number of active tracks at current frame

### 2. Weight Estimation Approach

Since ground truth weights are typically unavailable in CCTV footage, we implement a **Weight Proxy Index**:

#### Formula
```
weight_index = mean_area × area_factor × density_factor
```

Where:
- `mean_area`: Weighted average of bounding box areas across track lifetime
- `area_factor`: Calibration constant (default: 0.15)
- `density_factor`: Bird density adjustment (default: 1.0)

#### Features Used
1. **Bounding Box Area**: Primary indicator of bird size (pixels²)
2. **Temporal Consistency**: Averages across multiple observations
3. **Detection Confidence**: Weights observations by detection quality
4. **Observation Count**: More observations = higher confidence

#### Confidence Calculation
```
observation_confidence = min(1.0, num_observations / 30)
detection_confidence = mean(confidences)
overall_confidence = (observation_confidence + detection_confidence) / 2
```

### Converting Weight Index to Grams

To convert the proxy to actual weights, you need:

#### 1. Camera Calibration
- Place reference object of known size (e.g., 20cm × 20cm checkerboard)
- Calculate pixel-to-cm conversion factor at floor level
- Account for camera height, angle, and lens distortion

#### 2. Ground Truth Data Collection
- Manually weigh 15-20 birds at various growth stages
- Record weights (grams) and video timestamps
- Extract weight indices for these birds from video

#### 3. Regression Model Training
- Train linear regression: `weight_grams = α × weight_index + β`
- Use scikit-learn's LinearRegression
- Evaluate with R² score and RMSE

#### 4. Calibration Code
```python
from weight_estimator import WeightEstimator

estimator = WeightEstimator()

# Your collected data
weight_indices = np.array([245.3, 238.5, 260.1, ...])  # From video
actual_weights = np.array([1200, 1180, 1250, ...])  # Manually weighed (grams)

# Calibrate
calibration_params = estimator.calibrate(weight_indices, actual_weights)
print(f"Model: weight = {calibration_params['alpha']:.2f} * index + {calibration_params['beta']:.2f}")
print(f"R² Score: {calibration_params['r2_score']:.3f}")
```

### Assumptions
- Fixed camera position (no pan/tilt/zoom)
- Birds on a flat, uniform surface
- Consistent lighting conditions
- Camera height remains constant
- Single camera view (no multi-view fusion)

## Output Artifacts

### 1. Annotated Video
- **Location**: `outputs/[filename]_annotated_[timestamp].mp4`
- **Contents**:
  - Bounding boxes with color-coded track IDs
  - Detection confidence scores
  - Bird count overlay (top-left corner)
  - Timestamp overlay
- **Format**: MP4 (H.264 codec)
- **FPS**: Original FPS / fps_sample

### 2. Tracks JSON
- **Location**: `outputs/[filename]_tracks_[timestamp].json`
- **Contents**:
  - Complete tracking data for all birds
  - Frame-by-frame counts
  - Weight estimates per bird
  - Video metadata
- **Format**: JSON with proper indentation

### 3. API Response JSON
- Returned directly from `/analyze_video` endpoint
- Contains sampled data (first 100 count records, first 10 tracks)
- References to generated artifact files

## Performance Optimization

### Frame Sampling
- **fps_sample=1**: Process all frames (slowest, most accurate)
- **fps_sample=5**: Recommended for 30 FPS videos (good balance)
- **fps_sample=10**: Faster processing, may miss fast birds

### Model Selection
To use larger YOLO models (better accuracy, slower):

Edit `config.py`:
```python
YOLO_MODEL = "yolov8s.pt"  # Small
YOLO_MODEL = "yolov8m.pt"  # Medium
YOLO_MODEL = "yolov8l.pt"  # Large
YOLO_MODEL = "yolov8x.pt"  # Extra Large
```

### GPU Acceleration
- PyTorch automatically uses CUDA if available
- YOLOv8 will utilize GPU for inference
- 10-20x speedup on GPU vs CPU

### Typical Performance
- **GPU (RTX 3080)**: ~50-80 FPS processing speed
- **CPU (Intel i7)**: ~3-8 FPS processing speed
- **Memory**: ~2-4 GB for typical videos

## Troubleshooting

### Issue: "No birds detected"
**Solutions**:
- Lower `conf_thresh` to 0.2 or 0.15
- Check if video actually contains birds
- Verify birds are visible and not too small
- Consider training custom model on poultry dataset

### Issue: "Too many false positives"
**Solutions**:
- Increase `conf_thresh` to 0.4 or 0.5
- Increase `iou_thresh` to reduce overlapping boxes
- Filter by minimum bounding box area in config

### Issue: "Frequent ID switches"
**Solutions**:
- Increase `TRACK_BUFFER` in config.py (default: 30)
- Decrease `fps_sample` to process more frames
- Lower `MATCH_THRESH` for stricter IoU matching

### Issue: "Processing too slow"
**Solutions**:
- Increase `fps_sample` (e.g., 10 or 15)
- Use smaller YOLO model (yolov8n is smallest)
- Reduce video resolution before processing
- Enable GPU if available

### Issue: "Out of memory"
**Solutions**:
- Process shorter video segments
- Increase `fps_sample`
- Use smaller YOLO model
- Close other applications

## Configuration

Edit `config.py` to customize:

```python
# Detection parameters
DEFAULT_CONF_THRESH = 0.25  # Detection confidence threshold
DEFAULT_IOU_THRESH = 0.45   # NMS IoU threshold
DEFAULT_FPS_SAMPLE = 5      # Frame sampling rate

# Tracking parameters
TRACK_THRESH = 0.5          # High confidence threshold
TRACK_BUFFER = 30           # Max frames without detection
MATCH_THRESH = 0.7          # IoU threshold for matching

# Weight estimation
WEIGHT_AREA_FACTOR = 0.15   # Area-to-weight conversion factor
WEIGHT_DENSITY_FACTOR = 1.0 # Density adjustment
MIN_BOX_AREA = 100          # Minimum box area (pixels²)

# API settings
API_HOST = "0.0.0.0"
API_PORT = 8000
```

## Limitations

1. **Weight Proxy Not Absolute**: Outputs relative index, not grams
2. **Calibration Required**: Needs ground truth data for gram conversion
3. **Fixed Camera**: Assumes static camera with constant view
4. **Flat Surface**: Assumes birds on uniform ground plane
5. **Single Class**: Detects only "bird" class (COCO class 14)
6. **Occlusion Limits**: Very long occlusions (>30 frames) may cause ID loss
7. **Perspective Distortion**: No advanced perspective correction

## Future Improvements

1. **Custom Model Training**: Train YOLOv8 on poultry-specific dataset
2. **Camera Calibration**: Implement full camera calibration pipeline
3. **Multi-Camera Fusion**: Combine multiple camera views
4. **Re-Identification**: Add appearance features (color, texture)
5. **Behavior Analysis**: Detect feeding, drinking, abnormal movements
6. **Real-Time Streaming**: Process live CCTV feeds
7. **Database Integration**: Store results in PostgreSQL/MongoDB
8. **Alert System**: Notify when count anomalies detected
9. **Growth Tracking**: Monitor individual bird growth over time
10. **Species Classification**: Identify different bird species/breeds

## Sample Datasets

### Recommended Sources:
1. **Kaggle**:
   - Search: "poultry detection", "chicken counting", "bird tracking"
   - Look for COCO-format annotations
   
2. **Roboflow Universe**:
   - Poultry farm datasets with bounding box annotations
   
3. **YouTube**:
   - Download sample poultry farm CCTV footage
   - Use for testing (respect copyright)

### Dataset Requirements:
- Fixed camera angle (top-down or angled view)
- Good lighting conditions
- Clear bird visibility
- MP4, AVI, or MOV format
- Resolution: 720p or higher recommended

## Testing

### Unit Tests
```bash
pytest tests/
```

### Integration Test
```bash
python test_api.py sample_data/test_video.mp4
```

### Manual Test
1. Start API server: `python main.py`
2. Upload test video through Swagger UI at `/docs`
3. Check `outputs/` folder for generated artifacts
4. Verify count overlay and tracking IDs in annotated video

## Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t bird-counting .
docker run -p 8000:8000 -v $(pwd)/outputs:/app/outputs bird-counting
```

### Production Considerations
- Use Gunicorn with multiple workers
- Add NGINX reverse proxy
- Implement request queuing for large videos
- Set up monitoring (Prometheus, Grafana)
- Add authentication (API keys, JWT)
- Enable HTTPS (Let's Encrypt)

## License

This project is submitted as part of the ML/AI Engineer assessment for Kuppismart Solutions. 

## Author

**Sabiha Anjum**  
Candidate for ML/AI Engineer Internship  
Kuppismart Solutions (Livestockify)

## Acknowledgments

- **Ultralytics YOLOv8**: Object detection framework
- **ByteTrack**: Multi-object tracking algorithm
- **FastAPI**: Modern web framework for APIs
- **OpenCV**: Computer vision library

## References

1. Jocher, G., Chaurasia, A., & Qiu, J. (2023). Ultralytics YOLOv8. https://github.com/ultralytics/ultralytics
2. Zhang, Y., et al. (2022). ByteTrack: Multi-Object Tracking by Associating Every Detection Box. ECCV 2022.
3. COCO Dataset: https://cocodataset.org/

---

**Note**: This system provides a proof-of-concept implementation. For production use, consider:
- Training custom model on poultry-specific dataset
- Implementing camera calibration for accurate weight measurement
- Adding robust error handling and logging
- Setting up continuous monitoring and alerting
- Conducting thorough validation with ground truth data

## Support

For issues or questions:
1. Check this README thoroughly
2. Review the code comments
3. Check GitHub repositories provided as references
4. Contact: [Your Contact Information]

**Last Updated**: December 2025  
**Version**: 1.0.0
