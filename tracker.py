"""
ByteTrack implementation for bird tracking
"""
import numpy as np
from typing import List, Dict, Tuple
from collections import defaultdict
import logging

from utils import calculate_iou

logger = logging.getLogger(__name__)


class ByteTracker:
    """
    Simple ByteTrack implementation for object tracking.
    Handles stable ID assignment, occlusions, and ID switches.
    """
    
    def __init__(self, track_thresh: float = 0.5, track_buffer: int = 30, match_thresh: float = 0.7):
        """
        Initialize ByteTracker
        
        Args:
            track_thresh: Confidence threshold for high confidence tracks
            track_buffer: Maximum frames to keep track alive without detection
            match_thresh: IoU threshold for matching detections to tracks
        """
        self.track_thresh = track_thresh
        self.track_buffer = track_buffer
        self.match_thresh = match_thresh
        
        self.tracks: Dict = {}
        self.next_id = 1
        self.frame_count = 0
        
    def update(self, detections: List[List]) -> List[List]:
        """
        Update tracks with new detections
        
        Args:
            detections: List of [x1, y1, x2, y2, confidence]
            
        Returns:
            List of [x1, y1, x2, y2, track_id]
        """
        self.frame_count += 1
        
        if len(detections) == 0:
            # Age existing tracks and remove dead tracks
            dead_tracks = []
            for track_id in self.tracks:
                self.tracks[track_id]['age'] += 1
                if self.tracks[track_id]['age'] > self.track_buffer:
                    dead_tracks.append(track_id)
            for track_id in dead_tracks:
                del self.tracks[track_id]
            return []
        
        # Separate high and low confidence detections
        high_conf_dets = [d for d in detections if d[4] >= self.track_thresh]
        low_conf_dets = [d for d in detections if d[4] < self.track_thresh]
        
        # Match high confidence detections to existing tracks
        matched_tracks, unmatched_dets, unmatched_tracks = self._match(
            high_conf_dets, self.tracks
        )
        
        # Update matched tracks
        for det_idx, track_id in matched_tracks:
            det = high_conf_dets[det_idx]
            self.tracks[track_id]['box'] = det[:4]
            self.tracks[track_id]['confidence'] = det[4]
            self.tracks[track_id]['age'] = 0
            self.tracks[track_id]['hits'] += 1
        
        # Try to match low confidence detections to unmatched tracks
        if len(low_conf_dets) > 0 and len(unmatched_tracks) > 0:
            unmatched_track_dict = {tid: self.tracks[tid] for tid in unmatched_tracks}
            matched_tracks_low, _, remaining_unmatched = self._match(
                low_conf_dets, unmatched_track_dict
            )
            
            for det_idx, track_id in matched_tracks_low:
                det = low_conf_dets[det_idx]
                self.tracks[track_id]['box'] = det[:4]
                self.tracks[track_id]['confidence'] = det[4]
                self.tracks[track_id]['age'] = 0
                self.tracks[track_id]['hits'] += 1
            
            unmatched_tracks = remaining_unmatched
        
        # Create new tracks for unmatched high confidence detections
        for det_idx in unmatched_dets:
            det = high_conf_dets[det_idx]
            self.tracks[self.next_id] = {
                'box': det[:4],
                'confidence': det[4],
                'age': 0,
                'hits': 1,
                'start_frame': self.frame_count
            }
            self.next_id += 1
        
        # Age unmatched tracks
        for track_id in unmatched_tracks:
            self.tracks[track_id]['age'] += 1
        
        # Remove dead tracks
        dead_tracks = [tid for tid, t in self.tracks.items() 
                      if t['age'] > self.track_buffer]
        for track_id in dead_tracks:
            del self.tracks[track_id]
        
        # Return active tracks
        results = []
        for track_id, track in self.tracks.items():
            if track['age'] == 0:  # Only return tracks updated this frame
                box = track['box']
                results.append([box[0], box[1], box[2], box[3], track_id])
        
        return results
    
    def _match(self, detections: List, tracks: Dict) -> Tuple[List, List, List]:
        """
        Match detections to tracks using IoU
        
        Returns:
            matched: List of (det_idx, track_id) pairs
            unmatched_dets: List of unmatched detection indices
            unmatched_tracks: List of unmatched track IDs
        """
        if len(detections) == 0 or len(tracks) == 0:
            return [], list(range(len(detections))), list(tracks.keys())
        
        # Compute IoU matrix
        iou_matrix = np.zeros((len(detections), len(tracks)))
        track_ids = list(tracks.keys())
        
        for i, det in enumerate(detections):
            for j, track_id in enumerate(track_ids):
                iou_matrix[i, j] = calculate_iou(
                    np.array(det[:4]), 
                    np.array(tracks[track_id]['box'])
                )
        
        # Greedy matching
        matched = []
        unmatched_dets = list(range(len(detections)))
        unmatched_tracks = track_ids.copy()
        
        while len(unmatched_dets) > 0 and len(unmatched_tracks) > 0:
            # Find maximum IoU
            max_iou = 0
            max_det = -1
            max_track = -1
            
            for i in unmatched_dets:
                for j, tid in enumerate(unmatched_tracks):
                    track_idx = track_ids.index(tid)
                    if iou_matrix[i, track_idx] > max_iou:
                        max_iou = iou_matrix[i, track_idx]
                        max_det = i
                        max_track = tid
            
            if max_iou < self.match_thresh:
                break
            
            matched.append((max_det, max_track))
            unmatched_dets.remove(max_det)
            unmatched_tracks.remove(max_track)
        
        return matched, unmatched_dets, unmatched_tracks
