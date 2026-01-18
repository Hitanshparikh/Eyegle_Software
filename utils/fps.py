"""
FPS Counter and Performance Monitor
Tracks real-time performance metrics
"""

import time
from collections import deque
from typing import Dict


class FPSCounter:
    """Real-time FPS counter with moving average"""
    
    def __init__(self, window_size: int = 30):
        """
        Initialize FPS counter
        
        Args:
            window_size: Number of frames to average over
        """
        self.window_size = window_size
        self.frame_times = deque(maxlen=window_size)
        self.last_time = time.perf_counter()
        self.frame_count = 0
        
    def tick(self) -> float:
        """
        Register a frame and return current FPS
        
        Returns:
            Current FPS (moving average)
        """
        current_time = time.perf_counter()
        delta = current_time - self.last_time
        
        if delta > 0:
            self.frame_times.append(delta)
            self.frame_count += 1
        
        self.last_time = current_time
        
        # Calculate FPS
        if len(self.frame_times) > 0:
            avg_time = sum(self.frame_times) / len(self.frame_times)
            return 1.0 / avg_time if avg_time > 0 else 0.0
        return 0.0
    
    def get_stats(self) -> Dict[str, float]:
        """
        Get detailed performance statistics
        
        Returns:
            Dictionary with FPS, latency, jitter
        """
        if not self.frame_times:
            return {
                'fps': 0.0,
                'latency_ms': 0.0,
                'jitter_ms': 0.0,
                'min_fps': 0.0,
                'max_fps': 0.0
            }
        
        times = list(self.frame_times)
        avg_time = sum(times) / len(times)
        
        # Calculate stats
        fps = 1.0 / avg_time if avg_time > 0 else 0.0
        latency_ms = avg_time * 1000
        
        # Jitter (standard deviation of frame times)
        variance = sum((t - avg_time) ** 2 for t in times) / len(times)
        jitter_ms = (variance ** 0.5) * 1000
        
        # Min/max FPS
        max_time = max(times)
        min_time = min(times)
        min_fps = 1.0 / max_time if max_time > 0 else 0.0
        max_fps = 1.0 / min_time if min_time > 0 else 0.0
        
        return {
            'fps': fps,
            'latency_ms': latency_ms,
            'jitter_ms': jitter_ms,
            'min_fps': min_fps,
            'max_fps': max_fps
        }
    
    def reset(self):
        """Reset counter"""
        self.frame_times.clear()
        self.last_time = time.perf_counter()
        self.frame_count = 0


class PerformanceMonitor:
    """Monitor multiple performance metrics"""
    
    def __init__(self):
        """Initialize performance monitor"""
        self.metrics = {}
        self.counters = {}
        
    def start_timer(self, name: str):
        """Start timing an operation"""
        self.metrics[name] = time.perf_counter()
        
    def end_timer(self, name: str) -> float:
        """
        End timing and return duration
        
        Returns:
            Duration in milliseconds
        """
        if name in self.metrics:
            duration = (time.perf_counter() - self.metrics[name]) * 1000
            
            # Store in history
            if name not in self.counters:
                self.counters[name] = deque(maxlen=100)
            self.counters[name].append(duration)
            
            return duration
        return 0.0
    
    def get_average(self, name: str) -> float:
        """Get average duration for an operation"""
        if name in self.counters and len(self.counters[name]) > 0:
            return sum(self.counters[name]) / len(self.counters[name])
        return 0.0
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get all performance statistics"""
        stats = {}
        for name, times in self.counters.items():
            if times:
                times_list = list(times)
                stats[name] = {
                    'avg_ms': sum(times_list) / len(times_list),
                    'min_ms': min(times_list),
                    'max_ms': max(times_list),
                    'count': len(times_list)
                }
        return stats
