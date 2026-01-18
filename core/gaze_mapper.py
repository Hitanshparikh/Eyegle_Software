"""
Gaze Mapper - Maps eye position to screen coordinates
Handles calibration, normalization, and screen mapping
"""

import numpy as np
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass
import json
from pathlib import Path
from utils.logger import setup_logger


@dataclass
class CalibrationPoint:
    """Single calibration point data"""
    screen_pos: np.ndarray  # Target position on screen
    gaze_pos: np.ndarray    # Measured gaze position
    iris_left: np.ndarray   # Left iris position
    iris_right: np.ndarray  # Right iris position


class GazeMapper:
    """Maps eye gaze to screen coordinates with calibration"""
    
    def __init__(self, config: dict, screen_width: int, screen_height: int):
        """
        Initialize gaze mapper
        
        Args:
            config: Gaze configuration dictionary
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.logger = setup_logger("GazeMapper")
        self.config = config
        
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Calibration data
        self.calibration_points: List[CalibrationPoint] = []
        self.is_calibrated = False
        
        # Transformation matrices (from gaze space to screen space)
        self.transform_matrix: Optional[np.ndarray] = None
        
        # Eye dominance (used for weighted averaging)
        self.eye_dominance = config.get('eye_dominance', 'both')  # 'left', 'right', 'both'
        
        # Gaze estimation bounds (normalized -1 to 1)
        self.gaze_bounds = {
            'x_min': -1.0,
            'x_max': 1.0,
            'y_min': -1.0,
            'y_max': 1.0
        }
        
        # Default mapping (if no calibration)
        self._init_default_mapping()
        
    def _init_default_mapping(self):
        """Initialize default mapping without calibration"""
        # Simple linear mapping as fallback
        self.transform_matrix = np.array([
            [self.screen_width / 2, 0, self.screen_width / 2],
            [0, self.screen_height / 2, self.screen_height / 2]
        ])
        
    def estimate_gaze(self, left_iris: Optional[np.ndarray],
                      right_iris: Optional[np.ndarray],
                      frame_width: int, frame_height: int) -> Optional[np.ndarray]:
        """
        Estimate gaze direction from iris positions
        
        Args:
            left_iris: Left iris center in frame coordinates
            right_iris: Right iris center in frame coordinates
            frame_width: Frame width
            frame_height: Frame height
            
        Returns:
            Normalized gaze vector [x, y] in range [-1, 1] or None
        """
        if left_iris is None and right_iris is None:
            return None
        
        # Handle single array inputs (convert tuples to numpy arrays)
        if left_iris is not None and not isinstance(left_iris, np.ndarray):
            left_iris = np.array(left_iris)
        if right_iris is not None and not isinstance(right_iris, np.ndarray):
            right_iris = np.array(right_iris)
        
        # Normalize iris positions to [-1, 1]
        normalized_positions = []
        
        if left_iris is not None:
            left_norm = np.array([
                (left_iris[0] / frame_width) * 2 - 1,
                (left_iris[1] / frame_height) * 2 - 1
            ])
            normalized_positions.append(left_norm)
        
        if right_iris is not None:
            right_norm = np.array([
                (right_iris[0] / frame_width) * 2 - 1,
                (right_iris[1] / frame_height) * 2 - 1
            ])
            normalized_positions.append(right_norm)
        
        # Average based on eye dominance
        if len(normalized_positions) == 2:
            if self.eye_dominance == 'left':
                gaze = normalized_positions[0]
            elif self.eye_dominance == 'right':
                gaze = normalized_positions[1]
            else:  # both
                gaze = np.mean(normalized_positions, axis=0)
        else:
            gaze = normalized_positions[0]
        
        return gaze
    
    def gaze_to_screen(self, gaze: np.ndarray) -> np.ndarray:
        """
        Map normalized gaze to screen coordinates
        
        Args:
            gaze: Normalized gaze vector [x, y] in range [-1, 1]
            
        Returns:
            Screen coordinates [x, y] in pixels
        """
        # Apply transformation matrix
        gaze_homogeneous = np.array([gaze[0], gaze[1], 1.0])
        screen_pos = self.transform_matrix @ gaze_homogeneous
        
        # Clamp to screen bounds
        screen_pos[0] = np.clip(screen_pos[0], 0, self.screen_width)
        screen_pos[1] = np.clip(screen_pos[1], 0, self.screen_height)
        
        return screen_pos
    
    def add_calibration_point(self, screen_pos: np.ndarray,
                             left_iris: np.ndarray,
                             right_iris: np.ndarray,
                             frame_width: int, frame_height: int):
        """
        Add a calibration point
        
        Args:
            screen_pos: Target screen position [x, y]
            left_iris: Left iris position in frame
            right_iris: Right iris position in frame
            frame_width: Frame width
            frame_height: Frame height
        """
        gaze = self.estimate_gaze(left_iris, right_iris, frame_width, frame_height)
        
        if gaze is not None:
            point = CalibrationPoint(
                screen_pos=screen_pos,
                gaze_pos=gaze,
                iris_left=left_iris,
                iris_right=right_iris
            )
            self.calibration_points.append(point)
            self.logger.info(f"✓ Calibration point added: {len(self.calibration_points)}")
    
    def compute_calibration(self) -> bool:
        """
        Compute transformation matrix from calibration points
        
        Returns:
            True if calibration successful
        """
        if len(self.calibration_points) < 4:
            self.logger.warning("⚠️ Need at least 4 calibration points")
            return False
        
        try:
            # Build matrices for least squares
            # We want to find M such that: screen_pos = M @ [gaze_x, gaze_y, 1]
            
            gaze_points = []
            screen_points = []
            
            for point in self.calibration_points:
                gaze_points.append([point.gaze_pos[0], point.gaze_pos[1], 1.0])
                screen_points.append([point.screen_pos[0], point.screen_pos[1]])
            
            gaze_matrix = np.array(gaze_points)  # N x 3
            screen_matrix = np.array(screen_points)  # N x 2
            
            # Solve for transformation matrix using least squares
            # M.T = (G.T @ G)^-1 @ G.T @ S
            transform_T = np.linalg.lstsq(gaze_matrix, screen_matrix, rcond=None)[0]
            self.transform_matrix = transform_T.T  # 2 x 3
            
            self.is_calibrated = True
            self.logger.info(f"✅ Calibration complete with {len(self.calibration_points)} points")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Calibration failed: {e}")
            return False
    
    def reset_calibration(self):
        """Reset calibration data"""
        self.calibration_points.clear()
        self.is_calibrated = False
        self._init_default_mapping()
        self.logger.info("🔄 Calibration reset")
    
    def save_calibration(self, filepath: str) -> bool:
        """
        Save calibration to file
        
        Args:
            filepath: Path to save calibration
            
        Returns:
            True if successful
        """
        try:
            data = {
                'screen_width': self.screen_width,
                'screen_height': self.screen_height,
                'eye_dominance': self.eye_dominance,
                'transform_matrix': self.transform_matrix.tolist() if self.transform_matrix is not None else None,
                'calibration_points': len(self.calibration_points)
            }
            
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"💾 Calibration saved to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save calibration: {e}")
            return False
    
    def load_calibration(self, filepath: str) -> bool:
        """
        Load calibration from file
        
        Args:
            filepath: Path to calibration file
            
        Returns:
            True if successful
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Verify screen dimensions match
            if (data['screen_width'] != self.screen_width or
                data['screen_height'] != self.screen_height):
                self.logger.warning("⚠️ Screen dimensions don't match calibration")
                return False
            
            if data['transform_matrix'] is not None:
                self.transform_matrix = np.array(data['transform_matrix'])
                self.eye_dominance = data['eye_dominance']
                self.is_calibrated = True
                
                self.logger.info(f"📂 Calibration loaded from {filepath}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load calibration: {e}")
            return False
    
    def get_calibration_quality(self) -> float:
        """
        Estimate calibration quality (0.0 - 1.0)
        
        Returns:
            Quality score
        """
        if not self.is_calibrated or len(self.calibration_points) < 4:
            return 0.0
        
        # Simple quality metric based on number of points and coverage
        point_score = min(len(self.calibration_points) / 9.0, 1.0)
        
        # Could add more sophisticated metrics here (e.g., spatial coverage)
        
        return point_score
    
    def set_calibration_data(self, calibration_data: List[dict]):
        """
        Set calibration data from UI and compute transformation
        
        Args:
            calibration_data: List of calibration points with 'screen_pos', 'left_iris', 'right_iris'
        """
        if len(calibration_data) < 4:
            self.logger.error("❌ Insufficient calibration points (need at least 4)")
            return False
        
        self.logger.info(f"📊 Processing {len(calibration_data)} calibration points...")
        
        # Convert to arrays
        screen_points = []
        gaze_points = []
        
        for point in calibration_data:
            screen_pos = np.array(point['screen_pos'])
            left_iris = np.array(point['left_iris'])
            right_iris = np.array(point['right_iris'])
            
            # Calculate normalized gaze position
            # Average left and right iris positions
            avg_iris_x = (left_iris[0] + right_iris[0]) / 2
            avg_iris_y = (left_iris[1] + right_iris[1]) / 2
            
            # Normalize to [-1, 1] range (assuming 1280x720 frame)
            norm_gaze_x = (avg_iris_x / 640) - 1.0  # Center at 640
            norm_gaze_y = (avg_iris_y / 360) - 1.0  # Center at 360
            
            screen_points.append([screen_pos[0], screen_pos[1]])
            gaze_points.append([norm_gaze_x, norm_gaze_y])
        
        # Convert to numpy arrays
        screen_points = np.array(screen_points)
        gaze_points = np.array(gaze_points)
        
        # Compute transformation matrix using least squares
        try:
            # Add column of ones for affine transformation
            gaze_homogeneous = np.column_stack([gaze_points, np.ones(len(gaze_points))])
            
            # Solve for transformation matrix (separate for x and y)
            transform_x = np.linalg.lstsq(gaze_homogeneous, screen_points[:, 0], rcond=None)[0]
            transform_y = np.linalg.lstsq(gaze_homogeneous, screen_points[:, 1], rcond=None)[0]
            
            self.transform_matrix = np.array([transform_x, transform_y])
            self.is_calibrated = True
            
            self.logger.info("✅ Calibration transformation computed successfully")
            self.logger.info(f"📊 Calibration matrix shape: {self.transform_matrix.shape}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Calibration computation failed: {e}")
            return False
