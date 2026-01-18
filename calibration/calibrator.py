"""
Calibration System
Guides user through calibration process for accurate gaze mapping
"""

import numpy as np
import time
from typing import List, Tuple, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from utils.logger import setup_logger


class CalibrationState(Enum):
    """Calibration workflow states"""
    IDLE = "idle"
    INTRO = "intro"
    POSITIONING = "positioning"
    COLLECTING = "collecting"
    COMPUTING = "computing"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class CalibrationTarget:
    """Single calibration target"""
    position: np.ndarray  # Screen position [x, y]
    duration_ms: int      # Collection duration
    samples_collected: int = 0
    completed: bool = False


class Calibrator:
    """Manages calibration workflow and data collection"""
    
    def __init__(self, config: dict, screen_width: int, screen_height: int):
        """
        Initialize calibrator
        
        Args:
            config: Calibration configuration
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.logger = setup_logger("Calibrator")
        self.config = config
        
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Calibration parameters
        self.num_points = config.get('points', 9)
        self.duration_per_point = config.get('duration_per_point_ms', 2000)
        
        # State
        self.state = CalibrationState.IDLE
        self.current_target_index = 0
        self.targets: List[CalibrationTarget] = []
        
        # Callbacks
        self.on_target_complete: Optional[Callable] = None
        self.on_calibration_complete: Optional[Callable] = None
        
        # Timing
        self.target_start_time = 0.0
        
    def start(self) -> bool:
        """
        Start calibration process
        
        Returns:
            True if started successfully
        """
        try:
            self.logger.info("🎯 Starting calibration")
            
            # Generate calibration points
            self.targets = self._generate_calibration_points()
            
            self.state = CalibrationState.INTRO
            self.current_target_index = 0
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start calibration: {e}")
            self.state = CalibrationState.FAILED
            return False
    
    def _generate_calibration_points(self) -> List[CalibrationTarget]:
        """
        Generate calibration target positions
        
        Returns:
            List of calibration targets
        """
        targets = []
        
        # Margins from screen edge
        margin_x = self.screen_width * 0.1
        margin_y = self.screen_height * 0.1
        
        if self.num_points == 9:
            # 3x3 grid
            rows = 3
            cols = 3
        elif self.num_points == 5:
            # 5-point (center + corners)
            rows = 3
            cols = 3
            # We'll filter to just corners + center
        else:
            # Default to 9-point
            rows = 3
            cols = 3
        
        # Generate grid points
        for row in range(rows):
            for col in range(cols):
                x = margin_x + col * (self.screen_width - 2 * margin_x) / (cols - 1)
                y = margin_y + row * (self.screen_height - 2 * margin_y) / (rows - 1)
                
                target = CalibrationTarget(
                    position=np.array([x, y]),
                    duration_ms=self.duration_per_point
                )
                targets.append(target)
        
        # If 5-point, keep only corners and center
        if self.num_points == 5:
            indices = [0, 2, 4, 6, 8]  # Corners + center
            targets = [targets[i] for i in indices]
        
        self.logger.info(f"✓ Generated {len(targets)} calibration points")
        return targets
    
    def next_target(self) -> Optional[CalibrationTarget]:
        """
        Move to next calibration target
        
        Returns:
            Next target or None if complete
        """
        if self.current_target_index >= len(self.targets):
            self.state = CalibrationState.COMPUTING
            return None
        
        target = self.targets[self.current_target_index]
        self.state = CalibrationState.COLLECTING
        self.target_start_time = time.time()
        
        self.logger.info(f"🎯 Target {self.current_target_index + 1}/{len(self.targets)}: "
                        f"({target.position[0]:.0f}, {target.position[1]:.0f})")
        
        return target
    
    def collect_sample(self, left_iris: Optional[np.ndarray],
                      right_iris: Optional[np.ndarray],
                      frame_width: int, frame_height: int) -> bool:
        """
        Collect calibration sample for current target
        
        Args:
            left_iris: Left iris position
            right_iris: Right iris position
            frame_width: Frame width
            frame_height: Frame height
            
        Returns:
            True if target is complete
        """
        if self.state != CalibrationState.COLLECTING:
            return False
        
        if self.current_target_index >= len(self.targets):
            return False
        
        target = self.targets[self.current_target_index]
        
        # Check if we have valid iris data
        if left_iris is None or right_iris is None:
            return False
        
        # Add sample to target
        target.samples_collected += 1
        
        # Check if target duration elapsed
        elapsed_ms = (time.time() - self.target_start_time) * 1000
        
        if elapsed_ms >= target.duration_ms:
            target.completed = True
            self.logger.info(f"✓ Target {self.current_target_index + 1} complete "
                           f"({target.samples_collected} samples)")
            
            # Callback
            if self.on_target_complete:
                self.on_target_complete(self.current_target_index, target)
            
            # Move to next target
            self.current_target_index += 1
            
            # Check if all targets complete
            if self.current_target_index >= len(self.targets):
                self.state = CalibrationState.COMPUTING
                return True
            
            # Auto-start next target
            self.next_target()
        
        return False
    
    def compute_calibration(self) -> bool:
        """
        Compute calibration from collected samples
        
        Returns:
            True if successful
        """
        if self.state != CalibrationState.COMPUTING:
            return False
        
        # Check if all targets completed
        completed = sum(1 for t in self.targets if t.completed)
        
        if completed < len(self.targets):
            self.logger.warning(f"⚠️ Only {completed}/{len(self.targets)} targets completed")
            self.state = CalibrationState.FAILED
            return False
        
        # Calibration will be computed by GazeMapper
        # This just verifies we have enough data
        self.state = CalibrationState.COMPLETE
        self.logger.info("✅ Calibration data ready")
        
        if self.on_calibration_complete:
            self.on_calibration_complete()
        
        return True
    
    def get_current_target(self) -> Optional[CalibrationTarget]:
        """Get current calibration target"""
        if 0 <= self.current_target_index < len(self.targets):
            return self.targets[self.current_target_index]
        return None
    
    def get_progress(self) -> Tuple[int, int]:
        """
        Get calibration progress
        
        Returns:
            (completed_targets, total_targets)
        """
        completed = sum(1 for t in self.targets if t.completed)
        return (completed, len(self.targets))
    
    def get_progress_percent(self) -> float:
        """Get calibration progress as percentage"""
        completed, total = self.get_progress()
        return (completed / total * 100) if total > 0 else 0.0
    
    def get_target_progress(self) -> float:
        """Get current target progress (0.0 - 1.0)"""
        if self.state != CalibrationState.COLLECTING:
            return 0.0
        
        elapsed_ms = (time.time() - self.target_start_time) * 1000
        target = self.get_current_target()
        
        if target:
            return min(elapsed_ms / target.duration_ms, 1.0)
        return 0.0
    
    def reset(self):
        """Reset calibration"""
        self.state = CalibrationState.IDLE
        self.current_target_index = 0
        self.targets.clear()
        self.logger.info("🔄 Calibration reset")
    
    def is_complete(self) -> bool:
        """Check if calibration is complete"""
        return self.state == CalibrationState.COMPLETE
    
    def has_failed(self) -> bool:
        """Check if calibration has failed"""
        return self.state == CalibrationState.FAILED


class ProfileManager:
    """Manages user calibration profiles"""
    
    def __init__(self, profiles_dir: str = "calibration/profiles"):
        """
        Initialize profile manager
        
        Args:
            profiles_dir: Directory for calibration profiles
        """
        self.logger = setup_logger("ProfileManager")
        self.profiles_dir = profiles_dir
        
        # Create profiles directory
        from pathlib import Path
        Path(profiles_dir).mkdir(parents=True, exist_ok=True)
        
    def save_profile(self, name: str, data: dict) -> bool:
        """
        Save calibration profile
        
        Args:
            name: Profile name
            data: Profile data
            
        Returns:
            True if successful
        """
        try:
            import json
            from pathlib import Path
            
            filepath = Path(self.profiles_dir) / f"{name}.json"
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"💾 Profile saved: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save profile: {e}")
            return False
    
    def load_profile(self, name: str) -> Optional[dict]:
        """
        Load calibration profile
        
        Args:
            name: Profile name
            
        Returns:
            Profile data or None
        """
        try:
            import json
            from pathlib import Path
            
            filepath = Path(self.profiles_dir) / f"{name}.json"
            
            if not filepath.exists():
                self.logger.warning(f"⚠️ Profile not found: {name}")
                return None
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.logger.info(f"📂 Profile loaded: {name}")
            return data
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load profile: {e}")
            return None
    
    def list_profiles(self) -> List[str]:
        """
        List available profiles
        
        Returns:
            List of profile names
        """
        try:
            from pathlib import Path
            
            profiles_path = Path(self.profiles_dir)
            profiles = [p.stem for p in profiles_path.glob("*.json")]
            
            return sorted(profiles)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to list profiles: {e}")
            return []
    
    def delete_profile(self, name: str) -> bool:
        """
        Delete calibration profile
        
        Args:
            name: Profile name
            
        Returns:
            True if successful
        """
        try:
            from pathlib import Path
            
            filepath = Path(self.profiles_dir) / f"{name}.json"
            
            if filepath.exists():
                filepath.unlink()
                self.logger.info(f"🗑️ Profile deleted: {name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Failed to delete profile: {e}")
            return False
