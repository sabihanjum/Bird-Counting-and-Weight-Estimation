"""
Weight estimation module using bounding box features
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

from config import WEIGHT_AREA_FACTOR, WEIGHT_DENSITY_FACTOR, MIN_BOX_AREA
from utils import calculate_bbox_area

logger = logging.getLogger(__name__)


class WeightEstimator:
    """
    Estimate bird weights from tracking data using bounding box features.
    
    Since ground truth weights are typically unavailable, this calculates
    a weight proxy/index based on bird area and movement patterns.
    """
    
    def __init__(self):
        """Initialize weight estimator"""
        self.area_to_weight_factor = WEIGHT_AREA_FACTOR
        self.density_factor = WEIGHT_DENSITY_FACTOR
        self.calibration_model = None
        
    def estimate_weights(self, tracks: Dict) -> Dict:
        """
        Estimate weights for all tracked birds
        
        Args:
            tracks: Dictionary of track data with boxes and confidences
            
        Returns:
            Dictionary with per-bird and aggregate weight estimates
        """
        per_bird_weights = []
        all_weight_indices = []
        
        for track_id, track_data in tracks.items():
            boxes = np.array(track_data['boxes'])
            confidences = np.array(track_data['confidences'])
            
            if len(boxes) == 0:
                continue
            
            # Calculate weight index for this bird
            weight_index, confidence = self._calculate_weight_index(
                boxes, confidences
            )
            
            if weight_index > 0:
                per_bird_weights.append({
                    'track_id': int(track_id),
                    'weight_index': float(weight_index),
                    'confidence': float(confidence),
                    'num_observations': len(boxes)
                })
                
                all_weight_indices.append(weight_index)
        
        # Calculate aggregate statistics
        if len(all_weight_indices) > 0:
            aggregate = {
                'mean_weight_index': float(np.mean(all_weight_indices)),
                'std': float(np.std(all_weight_indices)),
                'median_weight_index': float(np.median(all_weight_indices)),
                'min_weight_index': float(np.min(all_weight_indices)),
                'max_weight_index': float(np.max(all_weight_indices)),
                'total_birds': len(all_weight_indices)
            }
        else:
            aggregate = {
                'mean_weight_index': 0.0,
                'std': 0.0,
                'median_weight_index': 0.0,
                'min_weight_index': 0.0,
                'max_weight_index': 0.0,
                'total_birds': 0
            }
        
        result = {
            'unit': 'index',
            'per_bird': per_bird_weights,
            'aggregate': aggregate,
            'calibration_note': self._get_calibration_notes(),
            'methodology': {
                'features': [
                    'Bounding box area (pixels²)',
                    'Track confidence (detection reliability)',
                    'Temporal consistency (number of observations)'
                ],
                'assumptions': [
                    'Fixed camera position and angle',
                    'Birds on flat surface',
                    'Consistent lighting conditions',
                    'Camera height remains constant'
                ]
            }
        }
        
        logger.info(f"Weight estimation complete for {len(per_bird_weights)} birds")
        return result
    
    def _calculate_weight_index(self, boxes: np.ndarray, 
                                confidences: np.ndarray) -> Tuple[float, float]:
        """
        Calculate weight index from bounding boxes
        
        Args:
            boxes: Array of [x1, y1, x2, y2] boxes
            confidences: Array of detection confidences
            
        Returns:
            (weight_index, confidence)
        """
        # Calculate areas
        widths = boxes[:, 2] - boxes[:, 0]
        heights = boxes[:, 3] - boxes[:, 1]
        areas = widths * heights
        
        # Filter out very small boxes
        valid_indices = areas > MIN_BOX_AREA
        if not np.any(valid_indices):
            return 0.0, 0.0
        
        areas = areas[valid_indices]
        confidences = confidences[valid_indices]
        
        # Weight by confidence and temporal consistency
        # More recent observations are slightly more important
        weights = confidences * np.exp(-np.arange(len(confidences)) * 0.01)
        weights = weights / np.sum(weights)
        
        # Weighted mean area
        mean_area = np.average(areas, weights=weights)
        
        # Calculate weight index
        weight_index = mean_area * self.area_to_weight_factor * self.density_factor
        
        # Confidence based on number of observations and mean confidence
        observation_confidence = min(1.0, len(boxes) / 30.0)
        detection_confidence = np.mean(confidences)
        overall_confidence = (observation_confidence + detection_confidence) / 2
        
        return weight_index, overall_confidence
    
    def _get_calibration_notes(self) -> str:
        """Get calibration instructions"""
        return (
            'Weight index is a proxy based on bird bounding box area. '
            'To convert to grams, calibration is required with: '
            '(1) Known weights for 10-20 birds at various sizes, '
            '(2) Camera calibration data (pixel-to-cm ratio at floor level), '
            '(3) Regression model training: weight_grams = alpha * weight_index + beta. '
            'Current formula: weight_index = mean_area * area_factor * density_factor'
        )
    
    def calibrate(self, weight_indices: np.ndarray, actual_weights: np.ndarray) -> Dict:
        """
        Calibrate weight estimator with ground truth weights
        
        Args:
            weight_indices: Array of calculated weight indices
            actual_weights: Array of actual weights in grams
            
        Returns:
            Calibration parameters
        """
        from sklearn.linear_model import LinearRegression
        
        model = LinearRegression()
        X = weight_indices.reshape(-1, 1)
        y = actual_weights
        
        model.fit(X, y)
        
        self.calibration_model = model
        logger.info(f"Calibration: weight = {model.coef_[0]:.4f} * index + {model.intercept_:.4f}")
        
        return {
            'alpha': float(model.coef_[0]),
            'beta': float(model.intercept_),
            'r2_score': float(model.score(X, y))
        }
