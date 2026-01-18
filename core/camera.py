"""
Camera Handler with Threading and Frame Management
Handles webcam input with optimized performance
"""

import cv2
import numpy as np
import threading
import time
from queue import Queue, Empty
from typing import Optional, Tuple, List
from utils.logger import setup_logger
from utils.fps import FPSCounter


def get_camera_name_windows(device_id: int) -> Optional[str]:
    """
    Try to get actual camera name on Windows using WMI
    
    Args:
        device_id: Camera device ID
        
    Returns:
        Camera name if found, None otherwise
    """
    try:
        import subprocess
        import json
        
        # Try using PowerShell to get camera names
        cmd = 'Get-CimInstance Win32_PnPEntity | Where-Object {$_.Service -eq "usbvideo" -or $_.PNPClass -eq "Camera" -or $_.Name -like "*camera*" -or $_.Name -like "*webcam*"} | Select-Object Name, DeviceID | ConvertTo-Json'
        result = subprocess.run(['powershell', '-Command', cmd], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and result.stdout.strip():
            try:
                devices = json.loads(result.stdout)
                if isinstance(devices, dict):
                    devices = [devices]  # Single device case
                
                if device_id < len(devices):
                    return devices[device_id].get('Name', None)
            except:
                pass
    except:
        pass
    return None


def list_available_cameras(max_test: int = 15) -> List[Tuple[int, str]]:
    """
    Comprehensive camera detection using multiple methods
    
    Args:
        max_test: Maximum number of camera indices to test
        
    Returns:
        List of (device_id, device_name) tuples
    """
    available_cameras = []
    logger = setup_logger("CameraDetection")
    
    logger.info(f"🔍 Scanning for cameras (0-{max_test-1})...")
    
    # Test different backends for better compatibility
    backends = [
        cv2.CAP_DSHOW,    # DirectShow (Windows)
        cv2.CAP_MSMF,     # Microsoft Media Foundation
        cv2.CAP_ANY       # Default backend
    ]
    
    for device_id in range(max_test):
        camera_found = False
        best_camera_info = None
        
        for backend in backends:
            if camera_found:
                break
                
            try:
                logger.debug(f"Testing camera {device_id} with backend {backend}")
                cap = cv2.VideoCapture(device_id, backend)
                
                if cap.isOpened():
                    # Try to read a frame to confirm camera works
                    ret, frame = cap.read()
                    if ret and frame is not None and frame.size > 0:
                        # Get camera properties
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = int(cap.get(cv2.CAP_PROP_FPS))
                        
                        # Try to get actual camera name
                        camera_name = get_camera_name_windows(device_id)
                        
                        if camera_name:
                            device_name = f"{camera_name} - {device_id} ({width}x{height})"
                        else:
                            device_name = f"Camera {device_id} ({width}x{height}@{fps}fps)"
                        
                        best_camera_info = (device_id, device_name)
                        camera_found = True
                        logger.info(f"✓ Found: {device_name}")
                        
                cap.release()
                
            except Exception as e:
                logger.debug(f"Backend {backend} failed for camera {device_id}: {e}")
                continue
        
        if best_camera_info:
            available_cameras.append(best_camera_info)
    
    # Also try alternative detection methods
    try:
        # Try using different device indices that might work on some systems
        alternative_indices = [700, 701, 702]  # Some cameras use high indices
        for alt_id in alternative_indices:
            try:
                cap = cv2.VideoCapture(alt_id, cv2.CAP_DSHOW)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        device_name = f"Camera {alt_id} ({width}x{height})"
                        available_cameras.append((alt_id, device_name))
                        logger.info(f"✓ Found alternative: {device_name}")
                cap.release()
            except:
                pass
    except:
        pass
    
    logger.info(f"📹 Found {len(available_cameras)} cameras total")
    return available_cameras


class CameraThread(threading.Thread):
    """Background thread for camera capture"""
    
    def __init__(self, device_id: int, width: int, height: int, fps: int):
        """
        Initialize camera thread
        
        Args:
            device_id: Camera device ID
            width: Frame width
            height: Frame height
            fps: Target FPS
        """
        super().__init__(daemon=True)
        self.logger = setup_logger("Camera")
        
        self.device_id = device_id
        self.width = width
        self.height = height
        self.target_fps = fps
        
        self.frame_queue = Queue(maxsize=2)  # Small buffer to stay current
        self.running = False
        self.cap: Optional[cv2.VideoCapture] = None
        
        self.fps_counter = FPSCounter()
        
    def run(self):
        """Main camera loop (runs in background thread)"""
        self.logger.info(f"🎥 Starting camera {self.device_id}")
        
        # Initialize camera
        self.cap = cv2.VideoCapture(self.device_id, cv2.CAP_DSHOW)  # DirectShow for Windows
        
        if not self.cap.isOpened():
            self.logger.error("❌ Failed to open camera")
            return
        
        # Configure camera
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer delay
        
        # Verify settings
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        
        self.logger.info(f"📷 Camera initialized: {actual_width}x{actual_height} @ {actual_fps}fps")
        
        self.running = True
        frame_time = 1.0 / self.target_fps
        consecutive_failures = 0
        max_failures = 30  # Allow 30 consecutive failures before giving up
        
        while self.running:
            start_time = time.perf_counter()
            
            try:
                # Capture frame
                ret, frame = self.cap.read()
                
                if not ret or frame is None:
                    consecutive_failures += 1
                    if consecutive_failures > max_failures:
                        self.logger.error("❌ Too many consecutive frame failures, stopping camera")
                        break
                    # Wait a bit before retrying
                    time.sleep(0.01)
                    continue
                
                # Reset failure counter on successful read
                consecutive_failures = 0
                
                # Validate frame
                if frame.size == 0:
                    self.logger.warning("⚠️ Empty frame received")
                    continue
            
                # Flip horizontally for mirror effect (more intuitive)
                frame = cv2.flip(frame, 1)
                
                # Update FPS
                self.fps_counter.tick()
                
                # Put frame in queue (non-blocking, drop old frames)
                try:
                    if self.frame_queue.full():
                        try:
                            self.frame_queue.get_nowait()  # Remove old frame
                        except Empty:
                            pass
                    self.frame_queue.put_nowait(frame)
                except Exception as e:
                    self.logger.debug(f"Queue error: {e}")
                    pass
                
            except Exception as e:
                consecutive_failures += 1
                self.logger.warning(f"⚠️ Frame capture error: {e}")
                if consecutive_failures > max_failures:
                    self.logger.error("❌ Too many errors, stopping camera")
                    break
                time.sleep(0.01)
                continue
            
            # Maintain target FPS
            elapsed = time.perf_counter() - start_time
            sleep_time = frame_time - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        # Cleanup
        if self.cap:
            self.cap.release()
        self.logger.info("🎥 Camera stopped")
    
    def stop(self):
        """Stop camera thread"""
        self.running = False


class Camera:
    """High-level camera interface with optimization"""
    
    def __init__(self, config: dict, device_id: Optional[int] = None):
        """
        Initialize camera
        
        Args:
            config: Camera configuration dictionary
            device_id: Optional specific camera device ID to use
        """
        self.logger = setup_logger("Camera")
        self.config = config
        
        # Use provided device_id or fallback to config
        self.device_id = device_id if device_id is not None else config.get('device_id', 0)
        self.width = config.get('width', 640)
        self.height = config.get('height', 480)
        self.fps = config.get('fps', 30)
        
        self.thread: Optional[CameraThread] = None
        self.latest_frame: Optional[np.ndarray] = None
        
        # Performance tracking
        self.frames_processed = 0
        self.frames_dropped = 0
        
        # Cache for available cameras
        self._available_cameras = None
        
    def get_available_cameras(self) -> List[Tuple[int, str]]:
        """Get list of available cameras"""
        if self._available_cameras is None:
            self._available_cameras = list_available_cameras()
        return self._available_cameras
        
    def set_device(self, device_id: int) -> bool:
        """
        Change camera device (restart required if running)
        
        Args:
            device_id: New camera device ID
            
        Returns:
            True if device change was successful
        """
        was_running = self.thread is not None and self.thread.running
        
        if was_running:
            self.stop()
            
        self.device_id = device_id
        self.logger.info(f"📷 Switching to camera {device_id}")
        
        if was_running:
            return self.start()
        
        return True
        
    def start(self) -> bool:
        """
        Start camera capture
        
        Returns:
            True if camera started successfully
        """
        try:
            self.thread = CameraThread(
                self.device_id,
                self.width,
                self.height,
                self.fps
            )
            self.thread.start()
            
            # Wait for first frame
            timeout = 5.0
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.get_frame() is not None:
                    self.logger.info("✅ Camera ready")
                    return True
                time.sleep(0.1)
            
            self.logger.error("❌ Camera timeout")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Camera error: {e}")
            return False
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get latest frame (non-blocking)
        
        Returns:
            Latest frame or None if not available
        """
        if not self.thread or not self.thread.running:
            return None
        
        try:
            # Get latest frame from queue
            while not self.thread.frame_queue.empty():
                try:
                    self.latest_frame = self.thread.frame_queue.get_nowait()
                    self.frames_processed += 1
                except Empty:
                    break
        except:
            pass
        
        return self.latest_frame
    
    def get_frame_rgb(self) -> Optional[np.ndarray]:
        """
        Get latest frame in RGB format
        
        Returns:
            Frame in RGB or None
        """
        frame = self.get_frame()
        if frame is not None:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return None
    
    def get_frame_gray(self) -> Optional[np.ndarray]:
        """
        Get latest frame in grayscale (optimized for processing)
        
        Returns:
            Grayscale frame or None
        """
        frame = self.get_frame()
        if frame is not None:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return None
    
    def get_fps(self) -> float:
        """Get current camera FPS"""
        if self.thread:
            return self.thread.fps_counter.get_stats()['fps']
        return 0.0
    
    def get_stats(self) -> dict:
        """Get camera statistics"""
        stats = {
            'running': self.thread is not None and self.thread.running,
            'frames_processed': self.frames_processed,
            'frames_dropped': self.frames_dropped,
            'fps': self.get_fps()
        }
        
        if self.thread:
            stats.update(self.thread.fps_counter.get_stats())
        
        return stats
    
    def stop(self):
        """Stop camera capture"""
        if self.thread:
            self.thread.stop()
            self.thread.join(timeout=2.0)
            self.thread = None
        self.logger.info("🎥 Camera stopped")
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
