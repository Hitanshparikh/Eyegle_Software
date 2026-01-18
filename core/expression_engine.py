"""
Expression Detection Engine
Detects facial expressions and gestures for control actions
"""

import numpy as np
import time
from typing import Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from core.tracker import EyeData
from utils.logger import setup_logger


class Expression(Enum):
    """Detected expression types"""
    NONE = "none"
    BLINK_LEFT = "blink_left"
    BLINK_RIGHT = "blink_right"
    BLINK_BOTH = "blink_both"
    BLINK_BOTH_LONG = "blink_both_long"
    EYEBROW_RAISE = "eyebrow_raise"
    EYEBROW_LOWER = "eyebrow_lower"
    SMILE = "smile"
    JAW_OPEN = "jaw_open"
    HEAD_TILT_LEFT = "head_tilt_left"
    HEAD_TILT_RIGHT = "head_tilt_right"
    HEAD_NOD = "head_nod"
    HEAD_SHAKE = "head_shake"


@dataclass
class ExpressionState:
    """Current expression state"""
    expression: Expression = Expression.NONE
    confidence: float = 0.0
    duration: float = 0.0
    start_time: float = 0.0


class ExpressionEngine:
    """Detects and classifies facial expressions"""
    
    def __init__(self, config: dict):
        """
        Initialize expression engine
        
        Args:
            config: Expression configuration dictionary
        """
        self.logger = setup_logger("ExpressionEngine")
        self.config = config
        
        # Thresholds
        self.blink_threshold = config.get('blink_threshold', 0.2)
        self.long_blink_duration = config.get('long_blink_ms', 500) / 1000.0
        self.blink_cooldown = config.get('blink_cooldown_ms', 200) / 1000.0
        
        # State tracking
        self.current_state = ExpressionState()
        self.last_blink_time = 0.0
        
        # Baseline values (for relative detection)
        self.baseline_left_ear = 0.3
        self.baseline_right_ear = 0.3
        self.baseline_samples = []
        self.baseline_initialized = False
        
        # Blink detection state
        self.left_eye_closed = False
        self.right_eye_closed = False
        self.both_eyes_closed = False
        self.blink_start_time = 0.0
        
    def update_baseline(self, eye_data: EyeData):
        """
        Update baseline EAR values during normal operation
        
        Args:
            eye_data: Current eye tracking data
        """
        if not eye_data.face_detected:
            return
        
        # Collect samples for baseline
        if len(self.baseline_samples) < 30:  # 1 second at 30fps
            self.baseline_samples.append({
                'left_ear': eye_data.left_eye_aspect_ratio,
                'right_ear': eye_data.right_eye_aspect_ratio
            })
        else:
            # Calculate baseline from samples
            left_ears = [s['left_ear'] for s in self.baseline_samples]
            right_ears = [s['right_ear'] for s in self.baseline_samples]
            
            self.baseline_left_ear = np.mean(left_ears)
            self.baseline_right_ear = np.mean(right_ears)
            
            self.baseline_initialized = True
            self.logger.info(f"✓ Baseline: L={self.baseline_left_ear:.3f}, R={self.baseline_right_ear:.3f}")
    
    def detect_expression(self, eye_data: EyeData) -> ExpressionState:
        """
        Detect current facial expression
        
        Args:
            eye_data: Current eye tracking data
            
        Returns:
            Current expression state
        """
        current_time = time.time()
        
        # If no face, return none
        if not eye_data.face_detected:
            self.current_state = ExpressionState(Expression.NONE)
            return self.current_state
        
        # Update baseline if not initialized
        if not self.baseline_initialized:
            self.update_baseline(eye_data)
            return self.current_state
        
        # Check cooldown
        if current_time - self.last_blink_time < self.blink_cooldown:
            return self.current_state
        
        # Detect blinks
        expression = self._detect_blink(eye_data, current_time)
        
        if expression != Expression.NONE:
            self.current_state = ExpressionState(
                expression=expression,
                confidence=eye_data.confidence,
                duration=current_time - self.blink_start_time if self.blink_start_time > 0 else 0.0,
                start_time=current_time
            )
            self.last_blink_time = current_time
            self.logger.debug(f"👁️ Detected: {expression.value}")
        
        return self.current_state
    
    def _detect_blink(self, eye_data: EyeData, current_time: float) -> Expression:
        """
        Detect blink patterns
        
        Args:
            eye_data: Eye tracking data
            current_time: Current timestamp
            
        Returns:
            Detected expression
        """
        left_ear = eye_data.left_eye_aspect_ratio
        right_ear = eye_data.right_eye_aspect_ratio
        
        # Determine if eyes are closed (relative to baseline)
        left_closed = left_ear < (self.baseline_left_ear * self.blink_threshold)
        right_closed = right_ear < (self.baseline_right_ear * self.blink_threshold)
        both_closed = left_closed and right_closed
        
        # Detect blink start
        if both_closed and not self.both_eyes_closed:
            self.both_eyes_closed = True
            self.blink_start_time = current_time
        
        # Detect blink end (both eyes)
        if self.both_eyes_closed and not both_closed:
            blink_duration = current_time - self.blink_start_time
            self.both_eyes_closed = False
            self.blink_start_time = 0.0
            
            # Classify blink duration
            if blink_duration >= self.long_blink_duration:
                return Expression.BLINK_BOTH_LONG
            else:
                return Expression.BLINK_BOTH
        
        # Detect single eye blinks (only if other eye is open)
        if left_closed and not self.left_eye_closed and not right_closed:
            self.left_eye_closed = True
            self.blink_start_time = current_time
        
        if self.left_eye_closed and not left_closed:
            self.left_eye_closed = False
            blink_duration = current_time - self.blink_start_time
            self.blink_start_time = 0.0
            
            if blink_duration < 0.3:  # Quick blink
                return Expression.BLINK_LEFT
        
        if right_closed and not self.right_eye_closed and not left_closed:
            self.right_eye_closed = True
            self.blink_start_time = current_time
        
        if self.right_eye_closed and not right_closed:
            self.right_eye_closed = False
            blink_duration = current_time - self.blink_start_time
            self.blink_start_time = 0.0
            
            if blink_duration < 0.3:  # Quick blink
                return Expression.BLINK_RIGHT
        
        return Expression.NONE
    
    def get_action_for_expression(self, expression: Expression) -> Optional[str]:
        """
        Get mapped action for expression
        
        Args:
            expression: Detected expression
            
        Returns:
            Action name or None
        """
        action_map = {
            Expression.BLINK_BOTH: 'blink_both_short',
            Expression.BLINK_BOTH_LONG: 'blink_both_long',
            Expression.BLINK_LEFT: 'blink_left',
            Expression.BLINK_RIGHT: 'blink_right',
            Expression.EYEBROW_RAISE: 'eyebrow_raise',
            Expression.EYEBROW_LOWER: 'eyebrow_lower',
            Expression.SMILE: 'smile',
            Expression.JAW_OPEN: 'jaw_open',
            Expression.HEAD_TILT_LEFT: 'head_tilt_left',
            Expression.HEAD_TILT_RIGHT: 'head_tilt_right',
            Expression.HEAD_NOD: 'head_nod',
            Expression.HEAD_SHAKE: 'head_shake'
        }
        
        action_key = action_map.get(expression)
        if action_key:
            return self.config.get('actions', {}).get(action_key)
        
        return None
    
    def reset(self):
        """Reset expression detection state"""
        self.current_state = ExpressionState(Expression.NONE)
        self.left_eye_closed = False
        self.right_eye_closed = False
        self.both_eyes_closed = False
        self.blink_start_time = 0.0
        self.baseline_samples.clear()
        self.baseline_initialized = False
