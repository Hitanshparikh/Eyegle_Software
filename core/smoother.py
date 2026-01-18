"""
Cursor Smoothing Engine
Implements EMA and Kalman filtering for jitter-free cursor movement
"""

import numpy as np
from typing import Tuple, Optional
from collections import deque


class EMAFilter:
    """Exponential Moving Average filter for smooth cursor movement"""
    
    def __init__(self, alpha: float = 0.3):
        """
        Initialize EMA filter
        
        Args:
            alpha: Smoothing factor (0.0 - 1.0)
                  Lower = smoother but slower
                  Higher = faster but less smooth
        """
        self.alpha = alpha
        self.value: Optional[np.ndarray] = None
        
    def update(self, new_value: np.ndarray) -> np.ndarray:
        """
        Update filter with new value
        
        Args:
            new_value: New position [x, y]
            
        Returns:
            Smoothed position
        """
        if self.value is None:
            self.value = new_value.copy()
        else:
            self.value = self.alpha * new_value + (1 - self.alpha) * self.value
        
        return self.value
    
    def reset(self):
        """Reset filter"""
        self.value = None


class KalmanFilter:
    """Kalman filter for optimal cursor prediction and smoothing"""
    
    def __init__(self, process_noise: float = 0.01, measurement_noise: float = 0.1):
        """
        Initialize Kalman filter
        
        Args:
            process_noise: Process noise covariance (Q)
            measurement_noise: Measurement noise covariance (R)
        """
        # State: [x, y, vx, vy] (position and velocity)
        self.state = np.zeros(4)
        
        # Covariance matrix
        self.P = np.eye(4) * 1000
        
        # State transition matrix (constant velocity model)
        self.F = np.array([
            [1, 0, 1, 0],  # x = x + vx
            [0, 1, 0, 1],  # y = y + vy
            [0, 0, 1, 0],  # vx = vx
            [0, 0, 0, 1]   # vy = vy
        ])
        
        # Measurement matrix (we only measure position)
        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ])
        
        # Process noise covariance
        self.Q = np.eye(4) * process_noise
        
        # Measurement noise covariance
        self.R = np.eye(2) * measurement_noise
        
        self.initialized = False
    
    def predict(self) -> np.ndarray:
        """
        Predict next state
        
        Returns:
            Predicted position [x, y]
        """
        # State prediction
        self.state = self.F @ self.state
        
        # Covariance prediction
        self.P = self.F @ self.P @ self.F.T + self.Q
        
        return self.state[:2]
    
    def update(self, measurement: np.ndarray) -> np.ndarray:
        """
        Update filter with measurement
        
        Args:
            measurement: Measured position [x, y]
            
        Returns:
            Filtered position
        """
        if not self.initialized:
            # Initialize state with first measurement
            self.state[:2] = measurement
            self.initialized = True
            return measurement
        
        # Predict
        self.predict()
        
        # Innovation
        y = measurement - (self.H @ self.state)
        
        # Innovation covariance
        S = self.H @ self.P @ self.H.T + self.R
        
        # Kalman gain
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # State update
        self.state = self.state + K @ y
        
        # Covariance update
        self.P = (np.eye(4) - K @ self.H) @ self.P
        
        return self.state[:2]
    
    def reset(self):
        """Reset filter"""
        self.state = np.zeros(4)
        self.P = np.eye(4) * 1000
        self.initialized = False


class VelocityBasedSmoother:
    """Velocity-based smoothing with acceleration curves"""
    
    def __init__(self, dead_zone: float = 15, acceleration: float = 1.5):
        """
        Initialize velocity-based smoother
        
        Args:
            dead_zone: Dead zone radius (pixels)
            acceleration: Acceleration factor at edges
        """
        self.dead_zone = dead_zone
        self.acceleration = acceleration
        self.center: Optional[np.ndarray] = None
        self.velocity_history = deque(maxlen=5)
        
    def apply(self, position: np.ndarray, screen_size: Tuple[int, int]) -> np.ndarray:
        """
        Apply velocity-based smoothing
        
        Args:
            position: Current cursor position [x, y]
            screen_size: Screen dimensions (width, height)
            
        Returns:
            Smoothed position with acceleration
        """
        # Calculate screen center
        if self.center is None:
            self.center = np.array([screen_size[0] / 2, screen_size[1] / 2])
        
        # Calculate distance from center
        diff = position - self.center
        distance = np.linalg.norm(diff)
        
        # Apply dead zone
        if distance < self.dead_zone:
            return self.center.copy()
        
        # Calculate velocity
        if len(self.velocity_history) > 0:
            velocity = np.linalg.norm(position - self.velocity_history[-1])
        else:
            velocity = 0
        
        self.velocity_history.append(position.copy())
        
        # Apply acceleration curve based on distance from center
        screen_diagonal = np.linalg.norm([screen_size[0], screen_size[1]])
        distance_ratio = distance / (screen_diagonal / 2)
        
        # Acceleration increases away from center
        accel_factor = 1.0 + (distance_ratio ** self.acceleration)
        
        # Apply acceleration
        result = self.center + diff * accel_factor
        
        # Clamp to screen bounds
        result[0] = np.clip(result[0], 0, screen_size[0])
        result[1] = np.clip(result[1], 0, screen_size[1])
        
        return result
    
    def reset(self):
        """Reset smoother"""
        self.center = None
        self.velocity_history.clear()


class CursorSmoother:
    """Combined smoothing pipeline for optimal cursor control"""
    
    def __init__(self, config: dict):
        """
        Initialize cursor smoother
        
        Args:
            config: Gaze configuration dictionary
        """
        self.config = config
        
        # Initialize filters
        self.ema = EMAFilter(alpha=config.get('smoothing_factor', 0.3))
        
        self.use_kalman = config.get('use_kalman', True)
        if self.use_kalman:
            self.kalman = KalmanFilter()
        
        self.velocity_smoother = VelocityBasedSmoother(
            dead_zone=config.get('dead_zone_radius', 15),
            acceleration=config.get('acceleration_curve', 1.5)
        )
        
        self.last_position: Optional[np.ndarray] = None
        
    def smooth(self, raw_position: np.ndarray, screen_size: Tuple[int, int]) -> np.ndarray:
        """
        Apply full smoothing pipeline
        
        Args:
            raw_position: Raw cursor position [x, y]
            screen_size: Screen dimensions (width, height)
            
        Returns:
            Fully smoothed cursor position
        """
        position = raw_position.copy()
        
        # Stage 1: EMA smoothing (fast, reduces jitter)
        position = self.ema.update(position)
        
        # Stage 2: Kalman filtering (optimal prediction)
        if self.use_kalman:
            position = self.kalman.update(position)
        
        # Stage 3: Velocity-based acceleration and dead zone
        position = self.velocity_smoother.apply(position, screen_size)
        
        # Sanity check
        position[0] = np.clip(position[0], 0, screen_size[0])
        position[1] = np.clip(position[1], 0, screen_size[1])
        
        self.last_position = position.copy()
        return position
    
    def reset(self):
        """Reset all smoothing filters"""
        self.ema.reset()
        if self.use_kalman:
            self.kalman.reset()
        self.velocity_smoother.reset()
        self.last_position = None
    
    def get_velocity(self) -> float:
        """Get current cursor velocity"""
        if len(self.velocity_smoother.velocity_history) >= 2:
            recent = list(self.velocity_smoother.velocity_history)
            return np.linalg.norm(recent[-1] - recent[-2])
        return 0.0
