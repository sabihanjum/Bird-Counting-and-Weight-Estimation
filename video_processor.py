"""
Video processing pipeline integrating detection, tracking, and weight estimation
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List
from collections import defaultdict
import logging

from detector import BirdDetector
from tracker import ByteTracker
from weight_estimator import WeightEstimator
from utils import (
    extract_video_metadata,
    frame_to_timestamp,
    generate_color_for_id,
    draw_bbox_with_label,
    draw_count_overlay
)
from config import VIDEO_CODEC, OUTPUT_FPS

logger = logging.getLogger(__name__)


class VideoProcessor:
    """
    Main video processing pipeline for bird counting and weight estimation
    """
    
    def __init__(self, conf_thresh: float = 0.25, iou_thresh: float = 0.45):
        """
        Initialize video processor
        
        Args:
            conf_thresh: Detection confidence threshold
            iou_thresh: IoU threshold for NMS
        """
        self.conf_thresh = conf_thresh
        self.iou_thresh = iou_thresh
        
    def process_video(self, video_path: str, fps_sample: int = 5) -> Dict:
        """
        Process video and return tracking results
        
        Args:
            video_path: Path to input video
            fps_sample: Process every Nth frame
            
        Returns:
            Dictionary containing counts, tracks, and metadata
        """
        logger.info(f"Processing video: {video_path}")
        
        # Initialize components
        detector = BirdDetector(self.conf_thresh, self.iou_thresh)
        tracker = ByteTracker(track_thresh=self.conf_thresh, 
                            track_buffer=30, match_thresh=0.7)
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        # Get video metadata
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"Video: {total_frames} frames at {fps} FPS")
        logger.info(f"Processing every {fps_sample} frame(s)")
        
        # Storage for results
        counts = []
        all_tracks = defaultdict(lambda: {
            'boxes': [],
            'confidences': [],
            'frames': []
        })
        
        frame_idx = 0
        processed_frames = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Sample frames
            if frame_idx % fps_sample == 0:
                # Detect birds
                detections = detector.detect(frame)
                
                # Update tracker
                tracks = tracker.update(detections)
                
                # Count birds
                bird_count = len(tracks)
                
                # Calculate timestamp
                timestamp = frame_to_timestamp(frame_idx, fps)
                
                counts.append({
                    'timestamp': timestamp,
                    'count': bird_count,
                    'frame': frame_idx
                })
                
                # Store track information
                for track in tracks:
                    track_id = int(track[4])
                    box = track[:4].tolist()
                    
                    # Find confidence from original detection
                    conf = 0.0
                    for det in detections:
                        det_box = np.array(det[:4])
                        track_box = np.array(box)
                        if np.allclose(det_box, track_box, atol=1.0):
                            conf = det[4]
                            break
                    
                    all_tracks[track_id]['boxes'].append(box)
                    all_tracks[track_id]['confidences'].append(float(conf))
                    all_tracks[track_id]['frames'].append(frame_idx)
                
                processed_frames += 1
                
                if processed_frames % 30 == 0:
                    logger.info(f"Processed {processed_frames} frames, current count: {bird_count}")
            
            frame_idx += 1
        
        cap.release()
        
        logger.info(f"Processing complete: {processed_frames} frames processed")
        logger.info(f"Total unique tracks: {len(all_tracks)}")
        
        return {
            'counts': counts,
            'tracks': dict(all_tracks),
            'video_info': {
                'fps': fps,
                'total_frames': total_frames,
                'processed_frames': processed_frames
            }
        }
    
    def create_annotated_video(self, video_path: str, tracks: Dict, 
                              counts: List[Dict], output_path: str, 
                              fps_sample: int = 5):
        """
        Create annotated video with bounding boxes and tracking IDs
        
        Args:
            video_path: Input video path
            tracks: Track data dictionary
            counts: Count data list
            output_path: Output video path
            fps_sample: Frame sampling rate
        """
        logger.info("Creating annotated video...")
        
        cap = cv2.VideoCapture(video_path)
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        fourcc = cv2.VideoWriter_fourcc(*VIDEO_CODEC)
        out = cv2.VideoWriter(output_path, fourcc, fps / fps_sample, (width, height))
        
        # Create frame-to-tracks mapping
        frame_tracks = defaultdict(list)
        for track_id, track_data in tracks.items():
            for i, frame_idx in enumerate(track_data['frames']):
                frame_tracks[frame_idx].append({
                    'id': track_id,
                    'box': track_data['boxes'][i],
                    'conf': track_data['confidences'][i]
                })
        
        # Create frame-to-count mapping
        frame_counts = {c['frame']: c['count'] for c in counts}
        
        frame_idx = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_idx % fps_sample == 0:
                # Draw tracks
                if frame_idx in frame_tracks:
                    for track in frame_tracks[frame_idx]:
                        box = track['box']
                        track_id = track['id']
                        conf = track['conf']
                        
                        # Draw bounding box
                        color = generate_color_for_id(track_id)
                        label = f"ID:{track_id} {conf:.2f}"
                        frame = draw_bbox_with_label(frame, box, label, color)
                
                # Draw count overlay
                count = frame_counts.get(frame_idx, 0)
                timestamp = frame_to_timestamp(frame_idx, fps)
                frame = draw_count_overlay(frame, count, timestamp)
                
                out.write(frame)
            
            frame_idx += 1
        
        cap.release()
        out.release()
        
        logger.info(f"Annotated video saved to {output_path}")
