# System Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Server (main.py)                 │
│                                                              │
│  GET  /health          → Simple health check                │
│  POST /analyze_video   → Video analysis pipeline            │
│  GET  /docs            → Interactive API documentation      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Video Processor (video_processor.py)            │
│                                                              │
│  1. Open video file                                         │
│  2. Sample frames (every Nth frame)                        │
│  3. Run detection pipeline                                  │
│  4. Run tracking pipeline                                   │
│  5. Estimate weights                                        │
│  6. Generate annotated video                                │
│  7. Save JSON results                                       │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────────┐
│  Detector    │    │   Tracker    │    │ WeightEstimator  │
│ (detector.py)│    │ (tracker.py) │    │(weight_est.py)   │
│              │    │              │    │                  │
│ YOLOv8       │    │ ByteTrack    │    │ Feature-based    │
│ Detection    │    │ Tracking     │    │ Proxy Index      │
└──────────────┘    └──────────────┘    └──────────────────┘
```

## Data Flow

```
Input Video
    │
    ▼
Frame Sampling (every Nth frame)
    │
    ▼
┌───────────────────────────────────┐
│         DETECTION                 │
│                                   │
│  Frame → YOLOv8 → Bounding Boxes  │
│                   + Confidences   │
└───────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────┐
│         TRACKING                  │
│                                   │
│  Detections → ByteTrack → Tracks  │
│               (IoU Match)         │
│                   + Track IDs     │
└───────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────┐
│         COUNT                     │
│                                   │
│  Tracks → Count Active Tracks     │
│           (unique IDs)            │
└───────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────┐
│    WEIGHT ESTIMATION              │
│                                   │
│  Tracks → Extract Features        │
│           (bbox area, conf)       │
│        → Calculate Proxy Index    │
└───────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────┐
│    OUTPUT GENERATION              │
│                                   │
│  1. Annotated Video               │
│     (boxes, IDs, count overlay)   │
│                                   │
│  2. JSON Results                  │
│     (counts, tracks, weights)     │
└───────────────────────────────────┘
```

## Detection Module (detector.py)

```
Frame (numpy array)
    │
    ▼
┌─────────────────────────┐
│    YOLOv8 Inference     │
│                         │
│  • Input: 640x640 RGB   │
│  • Model: yolov8n.pt    │
│  • Output: Detections   │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│   Filter Bird Class     │
│   (COCO class 14)       │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│   Apply Confidence      │
│   Threshold             │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│   Apply NMS             │
│   (IoU threshold)       │
└─────────────────────────┘
    │
    ▼
List of detections:
[x1, y1, x2, y2, confidence]
```

## Tracking Module (tracker.py)

```
Detections + Previous Tracks
    │
    ▼
┌────────────────────────────┐
│  Separate by Confidence    │
│  • High: conf >= 0.5       │
│  • Low:  conf < 0.5        │
└────────────────────────────┘
    │
    ▼
┌────────────────────────────┐
│  Match High Conf to Tracks │
│  (IoU-based matching)      │
│  • Compute IoU matrix      │
│  • Greedy matching         │
│  • Threshold: 0.7          │
└────────────────────────────┘
    │
    ▼
┌────────────────────────────┐
│  Update Matched Tracks     │
│  • Reset age to 0          │
│  • Update position         │
│  • Increment hits          │
└────────────────────────────┘
    │
    ▼
┌────────────────────────────┐
│  Match Low Conf to         │
│  Unmatched Tracks          │
│  (Second chance)           │
└────────────────────────────┘
    │
    ▼
┌────────────────────────────┐
│  Create New Tracks         │
│  (Unmatched high conf)     │
│  • Assign new ID           │
│  • Initialize track        │
└────────────────────────────┘
    │
    ▼
┌────────────────────────────┐
│  Age Unmatched Tracks      │
│  • age += 1                │
│  • Remove if age > 30      │
└────────────────────────────┘
    │
    ▼
Active Tracks with IDs:
[x1, y1, x2, y2, track_id]
```

## Weight Estimation Module (weight_estimator.py)

```
Track History
(boxes, confidences)
    │
    ▼
┌─────────────────────────┐
│  Calculate Areas        │
│  area = (x2-x1)*(y2-y1) │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│  Filter Small Boxes     │
│  area > MIN_BOX_AREA    │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│  Compute Weights        │
│  w = conf * exp(-t*0.01)│
│  (recent = higher)      │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│  Weighted Mean Area     │
│  mean_area = Σ(w*area)  │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│  Calculate Index        │
│  index = mean_area *    │
│          area_factor *  │
│          density_factor │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│  Calculate Confidence   │
│  obs_conf = min(1, n/30)│
│  det_conf = mean(confs) │
│  conf = (obs+det)/2     │
└─────────────────────────┘
    │
    ▼
Weight Index + Confidence
```

## API Request Flow

```
Client
  │
  │ POST /analyze_video
  │ (multipart/form-data)
  │ • video file
  │ • fps_sample=5
  │ • conf_thresh=0.25
  │ • iou_thresh=0.45
  │
  ▼
FastAPI Server
  │
  ├─→ Validate parameters
  │
  ├─→ Save temp file
  │
  ├─→ VideoProcessor.process_video()
  │    │
  │    ├─→ For each sampled frame:
  │    │    │
  │    │    ├─→ Detector.detect()
  │    │    │   (YOLOv8 inference)
  │    │    │
  │    │    ├─→ Tracker.update()
  │    │    │   (ByteTrack matching)
  │    │    │
  │    │    └─→ Store count & tracks
  │    │
  │    └─→ Return {counts, tracks}
  │
  ├─→ VideoProcessor.create_annotated_video()
  │    └─→ Generate MP4 with annotations
  │
  ├─→ WeightEstimator.estimate_weights()
  │    └─→ Calculate indices
  │
  ├─→ Save JSON results
  │
  └─→ Return response
      {
        counts,
        tracks_sample,
        weight_estimates,
        artifacts
      }
```

## Component Dependencies

```
main.py
  ├─→ video_processor.py
  │     ├─→ detector.py
  │     │     └─→ YOLOv8 (ultralytics)
  │     ├─→ tracker.py
  │     │     └─→ utils.py (IoU)
  │     └─→ weight_estimator.py
  │           └─→ utils.py (bbox area)
  ├─→ utils.py
  └─→ config.py
```

## External Dependencies

```
┌──────────────────────────────────────┐
│        Python Packages               │
├──────────────────────────────────────┤
│  • fastapi          (API framework)  │
│  • uvicorn          (ASGI server)    │
│  • ultralytics      (YOLOv8)        │
│  • opencv-python    (video I/O)     │
│  • torch            (PyTorch)       │
│  • numpy            (arrays)        │
│  • scipy            (scientific)    │
│  • scikit-learn     (ML utils)      │
│  • filterpy         (Kalman)        │
└──────────────────────────────────────┘
```

## File I/O

```
Input:
  • Video file (MP4, AVI, MOV, MKV)
  • Parameters (fps_sample, conf_thresh, iou_thresh)

Output:
  • Annotated video: outputs/[name]_annotated_[time].mp4
  • JSON results: outputs/[name]_tracks_[time].json
  • API response: JSON with counts, tracks, weights

Temporary:
  • Uploaded video (deleted after processing)
```

## Configuration Flow

```
config.py
  │
  ├─→ Detection Config
  │   • YOLO_MODEL = "yolov8n.pt"
  │   • DEFAULT_CONF_THRESH = 0.25
  │   • DEFAULT_IOU_THRESH = 0.45
  │
  ├─→ Tracking Config
  │   • TRACK_THRESH = 0.5
  │   • TRACK_BUFFER = 30
  │   • MATCH_THRESH = 0.7
  │
  ├─→ Weight Config
  │   • WEIGHT_AREA_FACTOR = 0.15
  │   • WEIGHT_DENSITY_FACTOR = 1.0
  │
  └─→ API Config
      • API_HOST = "0.0.0.0"
      • API_PORT = 8000
```

## Error Handling

```
API Request
  │
  ├─→ Parameter Validation
  │   • fps_sample >= 1
  │   • 0 <= conf_thresh <= 1
  │   • 0 <= iou_thresh <= 1
  │   └─→ HTTPException(400) if invalid
  │
  ├─→ Video File Processing
  │   • Check file exists
  │   • Check codec supported
  │   └─→ HTTPException(500) if error
  │
  └─→ Cleanup
      • Delete temp file
      • Always executed (finally block)
```

## Logging

```
Application Startup
  ├─→ INFO: "Starting server..."
  └─→ INFO: "Loading YOLOv8 model..."

Video Processing
  ├─→ INFO: "Processing video: [filename]"
  ├─→ INFO: "Video: N frames at F FPS"
  ├─→ INFO: "Processing every N frame(s)"
  ├─→ INFO: "Processed M frames..."
  └─→ INFO: "Processing complete"

Weight Estimation
  ├─→ INFO: "Estimating weights..."
  └─→ INFO: "Weight estimation complete for N birds"

Output Generation
  ├─→ INFO: "Creating annotated video..."
  └─→ INFO: "Annotated video saved to [path]"

Errors
  └─→ ERROR: "Error processing video: [details]"
```

## Performance Considerations

```
Bottlenecks:
  1. YOLOv8 inference (GPU accelerated)
  2. Video encoding (CPU bound)
  3. File I/O (disk speed)

Optimizations:
  1. Frame sampling (process every Nth frame)
  2. Model size (yolov8n is fastest)
  3. GPU acceleration (CUDA)
  4. Batch processing (future)

Memory:
  • Peak: ~4 GB (depends on video resolution)
  • Managed: frames processed one at a time
  • Cleanup: temporary files deleted
```

---

This architecture provides:
- ✅ Clear separation of concerns
- ✅ Modular design (easy to extend)
- ✅ Efficient processing pipeline
- ✅ Robust error handling
- ✅ Scalable structure
