"""
Safety Manager for Eyegle v1.0
Created by Hivizstudios & Hitansh Parikh
Prevents accidental actions and provides fail-safes
"""

import time
from typing import Dict, Set, Callable
from collections import deque


class SafetyManager:
    """Manages safety features and fail-safes"""
    
    def __init__(self, config: Dict):
        """
        Initialize safety manager
        
        Args:
            config: Safety configuration dictionary
        """
        self.config = config
        self.enabled = True
        self.paused = False
        
        # Click rate limiting
        self.click_times = deque(maxlen=10)
        self.max_clicks_per_second = config.get('max_clicks_per_second', 3)
        
        # Face detection tracking
        self.last_face_time = time.time()
        self.no_face_timeout = config.get('auto_pause_no_face_ms', 2000) / 1000.0
        
        # Action cooldowns
        self.action_cooldowns: Dict[str, float] = {}
        self.cooldown_times: Dict[str, float] = {
            'click': 0.2,
            'scroll': 0.1,
            'key': 0.3
        }
        
        # Confirmation required actions
        self.require_confirmation: Set[str] = set(config.get('require_confirmation', []))
        self.pending_confirmations: Dict[str, float] = {}
        
        # Emergency callback
        self.emergency_callback: Callable = None
        
    def update_face_detection(self, face_detected: bool):
        """
        Update face detection status
        
        Args:
            face_detected: Whether face is currently detected
        """
        if face_detected:
            self.last_face_time = time.time()
            if self.paused and self.enabled:
                self.paused = False
        else:
            # Check if we should auto-pause
            time_since_face = time.time() - self.last_face_time
            if time_since_face > self.no_face_timeout:
                self.paused = True
    
    def can_perform_action(self, action_type: str) -> bool:
        """
        Check if an action can be performed safely
        
        Args:
            action_type: Type of action (click, scroll, key)
            
        Returns:
            True if action is safe to perform
        """
        if not self.enabled or self.paused:
            return False
        
        # Check cooldown
        if action_type in self.action_cooldowns:
            time_since = time.time() - self.action_cooldowns[action_type]
            if time_since < self.cooldown_times.get(action_type, 0):
                return False
        
        # Check click rate limiting
        if action_type == 'click':
            if not self._check_click_rate():
                return False
        
        return True
    
    def _check_click_rate(self) -> bool:
        """
        Check if click rate is within limits
        
        Returns:
            True if click rate is acceptable
        """
        current_time = time.time()
        
        # Remove old clicks
        while self.click_times and current_time - self.click_times[0] > 1.0:
            self.click_times.popleft()
        
        # Check rate
        return len(self.click_times) < self.max_clicks_per_second
    
    def register_action(self, action_type: str):
        """
        Register that an action was performed
        
        Args:
            action_type: Type of action performed
        """
        self.action_cooldowns[action_type] = time.time()
        
        if action_type == 'click':
            self.click_times.append(time.time())
    
    def needs_confirmation(self, action: str) -> bool:
        """
        Check if action needs confirmation
        
        Args:
            action: Action name
            
        Returns:
            True if confirmation is required
        """
        return action in self.require_confirmation
    
    def request_confirmation(self, action: str, timeout: float = 3.0):
        """
        Request confirmation for an action
        
        Args:
            action: Action to confirm
            timeout: Confirmation timeout in seconds
        """
        self.pending_confirmations[action] = time.time() + timeout
    
    def confirm_action(self, action: str) -> bool:
        """
        Confirm a pending action
        
        Args:
            action: Action to confirm
            
        Returns:
            True if confirmation was successful
        """
        if action in self.pending_confirmations:
            if time.time() < self.pending_confirmations[action]:
                del self.pending_confirmations[action]
                return True
            else:
                # Timeout expired
                del self.pending_confirmations[action]
        return False
    
    def emergency_stop(self):
        """Trigger emergency stop"""
        self.enabled = False
        self.paused = True
        if self.emergency_callback:
            self.emergency_callback()
    
    def resume(self):
        """Resume normal operation"""
        self.enabled = True
        self.paused = False
        self.click_times.clear()
        self.action_cooldowns.clear()
    
    def is_active(self) -> bool:
        """Check if system is active"""
        return self.enabled and not self.paused
    
    def get_status(self) -> Dict:
        """Get current safety status"""
        return {
            'enabled': self.enabled,
            'paused': self.paused,
            'clicks_last_second': len(self.click_times),
            'pending_confirmations': len(self.pending_confirmations),
            'time_since_face': time.time() - self.last_face_time
        }
