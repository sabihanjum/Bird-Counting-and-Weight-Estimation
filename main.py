"""
FastAPI application for bird counting and weight estimation
"""
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import os
import shutil
from pathlib import Path
from typing import Optional
import tempfile
import logging
import json

from video_processor import VideoProcessor
from weight_estimator import WeightEstimator
from utils import save_json_output, create_output_filename
from config import OUTPUT_DIR, API_HOST, API_PORT, DEFAULT_CONF_THRESH, DEFAULT_IOU_THRESH, DEFAULT_FPS_SAMPLE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Bird Counting and Weight Estimation API",
    description="Analyze poultry CCTV videos for bird counting and weight estimation",
    version="1.0.0"
)


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        Simple OK response
    """
    return {"status": "OK", "message": "Bird Counting API is running"}


@app.post("/analyze_video")
async def analyze_video(
    video: UploadFile = File(..., description="Video file to analyze"),
    fps_sample: Optional[int] = Form(DEFAULT_FPS_SAMPLE, description="Process every Nth frame"),
    conf_thresh: Optional[float] = Form(DEFAULT_CONF_THRESH, description="Detection confidence threshold"),
    iou_thresh: Optional[float] = Form(DEFAULT_IOU_THRESH, description="IoU threshold for NMS")
):
    """
    Analyze video for bird counting and weight estimation
    
    Parameters:
    - video: Video file (MP4, AVI, etc.)
    - fps_sample: Process every Nth frame (default: 5)
    - conf_thresh: Detection confidence threshold (default: 0.25)
    - iou_thresh: IoU threshold for NMS (default: 0.45)
    
    Returns:
    - counts: Time series of bird counts
    - tracks_sample: Sample tracking data
    - weight_estimates: Weight proxy indices
    - artifacts: Paths to generated files
    """
    temp_video_path = None
    
    try:
        # Validate parameters
        if fps_sample < 1:
            raise HTTPException(status_code=400, detail="fps_sample must be >= 1")
        if not (0.0 <= conf_thresh <= 1.0):
            raise HTTPException(status_code=400, detail="conf_thresh must be between 0 and 1")
        if not (0.0 <= iou_thresh <= 1.0):
            raise HTTPException(status_code=400, detail="iou_thresh must be between 0 and 1")
        
        # Save uploaded video to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(video.filename).suffix) as temp_file:
            temp_video_path = temp_file.name
            shutil.copyfileobj(video.file, temp_file)
        
        logger.info(f"Processing video: {video.filename}")
        logger.info(f"Parameters - fps_sample: {fps_sample}, conf_thresh: {conf_thresh}, iou_thresh: {iou_thresh}")
        
        # Initialize video processor
        processor = VideoProcessor(conf_thresh=conf_thresh, iou_thresh=iou_thresh)
        
        # Process video
        results = processor.process_video(temp_video_path, fps_sample=fps_sample)
        
        # Generate output filenames
        base_name = Path(video.filename).stem
        annotated_video_filename = create_output_filename(base_name, "annotated", "mp4")
        tracks_json_filename = create_output_filename(base_name, "tracks", "json")
        
        annotated_video_path = OUTPUT_DIR / annotated_video_filename
        tracks_json_path = OUTPUT_DIR / tracks_json_filename
        
        # Create annotated video
        logger.info("Creating annotated video...")
        processor.create_annotated_video(
            temp_video_path,
            results['tracks'],
            results['counts'],
            str(annotated_video_path),
            fps_sample=fps_sample
        )
        
        # Estimate weights
        logger.info("Estimating weights...")
        weight_estimator = WeightEstimator()
        weight_estimates = weight_estimator.estimate_weights(results['tracks'])
        
        # Save tracks to JSON
        tracks_data = {
            'counts': results['counts'],
            'tracks': results['tracks'],
            'weight_estimates': weight_estimates,
            'video_info': results['video_info']
        }
        save_json_output(tracks_data, tracks_json_path)
        
        # Sample tracks for response (limit to first 10)
        tracks_sample = []
        for track_id, track_data in list(results['tracks'].items())[:10]:
            if len(track_data['boxes']) > 0:
                mid_idx = len(track_data['boxes']) // 2
                tracks_sample.append({
                    'track_id': int(track_id),
                    'boxes': track_data['boxes'][:5],  # First 5 boxes
                    'confidences': track_data['confidences'][:5]
                })
        
        # Prepare response
        response = {
            "counts": results['counts'][:100],  # First 100 count records
            "tracks_sample": tracks_sample,
            "weight_estimates": weight_estimates,
            "artifacts": {
                "annotated_video": str(annotated_video_path),
                "tracks_json": str(tracks_json_path)
            },
            "video_info": {
                "filename": video.filename,
                "total_frames_processed": len(results['counts']),
                "total_tracks": len(results['tracks'])
            }
        }
        
        logger.info("Analysis complete")
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")
    
    finally:
        # Clean up temporary file
        if temp_video_path and os.path.exists(temp_video_path):
            os.unlink(temp_video_path)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Bird Counting and Weight Estimation API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "analyze_video": "/analyze_video (POST)",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {API_HOST}:{API_PORT}")
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True
    )
