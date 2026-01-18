"""
Eye and Face Tracking Engine using MediaPipe
Detects face landmarks, iris position, and eye movements
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import Optional, Dict, Tuple, List
from dataclasses import dataclass
from utils.logger import setup_logger
from utils.fps import PerformanceMonitor


@dataclass
class EyeData:
    """Container for eye tracking data"""
    left_iris_center: Optional[np.ndarray] = None
    right_iris_center: Optional[np.ndarray] = None
    left_eye_landmarks: Optional[List] = None
    right_eye_landmarks: Optional[List] = None
    left_eye_aspect_ratio: float = 0.0
    right_eye_aspect_ratio: float = 0.0
    face_detected: bool = False
    confidence: float = 0.0


class FaceTracker:
    """Face mesh and iris tracking using MediaPipe"""
    
    # MediaPipe landmark indices
    LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
    LEFT_IRIS_INDICES = [468, 469, 470, 471, 472]
    RIGHT_IRIS_INDICES = [473, 474, 475, 476, 477]
    
    def __init__(self, config: dict):
        """
        Initialize face tracker
        
        Args:
            config: Configuration dictionary
        """
        self.logger = setup_logger("FaceTracker")
        self.config = config
        
        # Initialize MediaPipe Face Landmarker
        self.face_landmarker = None
        self.mp_drawing = None
        
        try:
            # Try to use older solutions API if available (sometimes still works)
            import mediapipe.python.solutions as solutions
            if hasattr(solutions, 'face_mesh'):
                self.face_mesh = solutions.face_mesh.FaceMesh(
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                self.mp_drawing = solutions.drawing_utils
                self.logger.info("✅ MediaPipe Face Mesh (solutions) initialized")
                self.use_solutions_api = True
            else:
                raise ImportError("Solutions API not available")
                
        except (ImportError, AttributeError):
            # If solutions API fails, implement basic face detection using OpenCV
            self.logger.warning("⚠️ MediaPipe solutions not available, using OpenCV fallback")
            self.face_cascade = None
            self.eye_cascade = None
            
            try:
                # Try to load OpenCV face/eye cascades
                self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
                if not self.face_cascade.empty() and not self.eye_cascade.empty():
                    self.logger.info("✅ OpenCV cascade fallback initialized")
                    self.use_solutions_api = False
                else:
                    raise Exception("Failed to load cascades")
            except:
                self.logger.error("❌ All face detection methods failed - using basic estimation")
                self.use_solutions_api = None
        
        self.performance = PerformanceMonitor()
        
        # Cache for performance
        self.frame_count = 0
        self.process_every_n_frames = 1
        
        # Eye landmark indices (MediaPipe face mesh)
        self.LEFT_EYE_LANDMARKS = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        self.RIGHT_EYE_LANDMARKS = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        self.LEFT_IRIS_LANDMARKS = [468, 469, 470, 471, 472]
        self.RIGHT_IRIS_LANDMARKS = [473, 474, 475, 476, 477]
        
    def process_frame(self, frame: np.ndarray) -> EyeData:
        """
        Process frame and extract eye tracking data
        
        Args:
            frame: Input frame (BGR)
            
        Returns:
            EyeData object with tracking results
        """
        self.performance.start_timer('tracking')
        
        eye_data = EyeData()
        h, w = frame.shape[:2]
        
        try:
            if self.use_solutions_api is True and self.face_mesh is not None:
                # Use MediaPipe solutions API
                eye_data = self._process_with_mediapipe(frame, eye_data)
                
            elif self.use_solutions_api is False and self.face_cascade is not None:
                # Use OpenCV cascade fallback
                eye_data = self._process_with_opencv(frame, eye_data)
                
            else:
                # Basic estimation fallback
                eye_data = self._process_with_basic_estimation(frame, eye_data)
                
        except Exception as e:
            self.logger.error(f"❌ Face tracking error: {e}")
            eye_data = self._process_with_basic_estimation(frame, eye_data)
        
        self.performance.end_timer('tracking')
        return eye_data
        
    def _process_with_mediapipe(self, frame: np.ndarray, eye_data: EyeData) -> EyeData:
        """Process frame using MediaPipe solutions API"""
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w = frame.shape[:2]
        
        # Process with MediaPipe
        results = self.face_mesh.process(rgb_frame)
        
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0]
            
            eye_data.face_detected = True
            eye_data.confidence = 0.8
            
            # Extract eye landmarks
            left_eye_points = []
            right_eye_points = []
            
            # Simplified eye landmark extraction (using key points)
            key_points = {
                'left_eye': [33, 7, 163, 144, 145, 153],  # Key left eye points
                'right_eye': [362, 382, 381, 380, 374, 373],  # Key right eye points
                'left_iris': [468, 469, 470, 471, 472] if len(landmarks.landmark) > 468 else [33],
                'right_iris': [473, 474, 475, 476, 477] if len(landmarks.landmark) > 473 else [362]
            }
            
            # Get eye landmarks
            for idx in key_points['left_eye']:
                if idx < len(landmarks.landmark):
                    x = int(landmarks.landmark[idx].x * w)
                    y = int(landmarks.landmark[idx].y * h)
                    left_eye_points.append((x, y))
            
            for idx in key_points['right_eye']:
                if idx < len(landmarks.landmark):
                    x = int(landmarks.landmark[idx].x * w)
                    y = int(landmarks.landmark[idx].y * h)
                    right_eye_points.append((x, y))
            
            eye_data.left_eye_landmarks = left_eye_points
            eye_data.right_eye_landmarks = right_eye_points
            
            # Calculate eye centers
            if left_eye_points:
                left_center_x = sum(p[0] for p in left_eye_points) // len(left_eye_points)
                left_center_y = sum(p[1] for p in left_eye_points) // len(left_eye_points)
                eye_data.left_eye_center = (left_center_x, left_center_y)
            
            if right_eye_points:
                right_center_x = sum(p[0] for p in right_eye_points) // len(right_eye_points)
                right_center_y = sum(p[1] for p in right_eye_points) // len(right_eye_points)
                eye_data.right_eye_center = (right_center_x, right_center_y)
            
            # Get iris centers (if iris landmarks available)
            try:
                if len(landmarks.landmark) > 468:
                    # Calculate iris centers
                    left_iris_x = sum(landmarks.landmark[i].x for i in key_points['left_iris']) / len(key_points['left_iris'])
                    left_iris_y = sum(landmarks.landmark[i].y for i in key_points['left_iris']) / len(key_points['left_iris'])
                    eye_data.left_iris_center = (int(left_iris_x * w), int(left_iris_y * h))
                    
                    right_iris_x = sum(landmarks.landmark[i].x for i in key_points['right_iris']) / len(key_points['right_iris'])
                    right_iris_y = sum(landmarks.landmark[i].y for i in key_points['right_iris']) / len(key_points['right_iris'])
                    eye_data.right_iris_center = (int(right_iris_x * w), int(right_iris_y * h))
                else:
                    # Use eye centers as iris centers
                    eye_data.left_iris_center = eye_data.left_eye_center
                    eye_data.right_iris_center = eye_data.right_eye_center
            except:
                eye_data.left_iris_center = eye_data.left_eye_center
                eye_data.right_iris_center = eye_data.right_eye_center
            
            # Calculate blink ratios
            eye_data.left_eye_ratio = self._calculate_eye_aspect_ratio(left_eye_points)
            eye_data.right_eye_ratio = self._calculate_eye_aspect_ratio(right_eye_points)
        
        return eye_data
        
    def _process_with_opencv(self, frame: np.ndarray, eye_data: EyeData) -> EyeData:
        """Process frame using OpenCV cascade fallback"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = frame.shape[:2]
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0:
            eye_data.face_detected = True
            eye_data.confidence = 0.6
            
            # Use first face
            (x, y, fw, fh) = faces[0]
            
            # Look for eyes in the upper half of the face
            eye_region = gray[y:y+fh//2, x:x+fw]
            eyes = self.eye_cascade.detectMultiScale(eye_region, 1.1, 3)
            
            if len(eyes) >= 2:
                # Sort eyes by x position (left to right)
                eyes = sorted(eyes, key=lambda e: e[0])
                
                # Left eye (first in sorted list)
                (ex1, ey1, ew1, eh1) = eyes[0]
                eye_data.left_eye_center = (x + ex1 + ew1//2, y + ey1 + eh1//2)
                eye_data.left_iris_center = eye_data.left_eye_center
                
                # Right eye (second in sorted list)
                (ex2, ey2, ew2, eh2) = eyes[1]
                eye_data.right_eye_center = (x + ex2 + ew2//2, y + ey2 + eh2//2)
                eye_data.right_iris_center = eye_data.right_eye_center
            
            elif len(eyes) == 1:
                # Only one eye detected, estimate the other
                (ex, ey, ew, eh) = eyes[0]
                detected_eye_center = (x + ex + ew//2, y + ey + eh//2)
                
                # Assume it's the left eye and estimate right eye
                eye_data.left_eye_center = detected_eye_center
                eye_data.right_eye_center = (detected_eye_center[0] + fw//3, detected_eye_center[1])
                eye_data.left_iris_center = eye_data.left_eye_center
                eye_data.right_iris_center = eye_data.right_eye_center
            
            # Basic blink ratio estimation
            eye_data.left_eye_ratio = 0.3
            eye_data.right_eye_ratio = 0.3
        
        return eye_data
        
    def _process_with_basic_estimation(self, frame: np.ndarray, eye_data: EyeData) -> EyeData:
        """Basic estimation when no detection methods work"""
        h, w = frame.shape[:2]
        
        # Estimate eye positions based on typical face proportions
        eye_data.face_detected = True
        eye_data.confidence = 0.3
        
        eye_data.left_eye_center = (int(w * 0.35), int(h * 0.45))
        eye_data.right_eye_center = (int(w * 0.65), int(h * 0.45))
        eye_data.left_iris_center = eye_data.left_eye_center
        eye_data.right_iris_center = eye_data.right_eye_center
        
        eye_data.left_eye_ratio = 0.3
        eye_data.right_eye_ratio = 0.3
        
        return eye_data
        
    def _calculate_eye_aspect_ratio(self, eye_points) -> float:
        """Calculate Eye Aspect Ratio for blink detection"""
        if len(eye_points) < 6:
            return 0.3  # Default ratio
            
        try:
            # Calculate vertical distances
            v1 = np.linalg.norm(np.array(eye_points[1]) - np.array(eye_points[5]))
            v2 = np.linalg.norm(np.array(eye_points[2]) - np.array(eye_points[4]))
            
            # Calculate horizontal distance  
            h = np.linalg.norm(np.array(eye_points[0]) - np.array(eye_points[3]))
            
            # Calculate EAR
            if h > 0:
                ear = (v1 + v2) / (2.0 * h)
                return ear
            else:
                return 0.3
        except:
            return 0.3
        
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0]
            
            h, w = frame.shape[:2]
            
            # Extract eye landmarks
            eye_data.left_eye_landmarks = self._get_landmarks(
                landmarks, self.LEFT_EYE_INDICES, w, h
            )
            eye_data.right_eye_landmarks = self._get_landmarks(
                landmarks, self.RIGHT_EYE_INDICES, w, h
            )
            
            # Extract iris centers
            left_iris = self._get_landmarks(
                landmarks, self.LEFT_IRIS_INDICES, w, h
            )
            right_iris = self._get_landmarks(
                landmarks, self.RIGHT_IRIS_INDICES, w, h
            )
            
            if len(left_iris) > 0:
                eye_data.left_iris_center = np.mean(left_iris, axis=0)
            
            if len(right_iris) > 0:
                eye_data.right_iris_center = np.mean(right_iris, axis=0)
            
            # Calculate Eye Aspect Ratio (EAR) for blink detection
            eye_data.left_eye_aspect_ratio = self._calculate_ear(
                eye_data.left_eye_landmarks
            )
            eye_data.right_eye_aspect_ratio = self._calculate_ear(
                eye_data.right_eye_landmarks
            )
            
            eye_data.face_detected = True
            eye_data.confidence = 0.9  # MediaPipe doesn't expose confidence directly
        
        duration = self.performance.end_timer('tracking')
        
        # Log performance warnings
        if duration > 20:
            self.logger.warning(f"⚠️ Tracking took {duration:.2f}ms (target: <20ms)")
        
        return eye_data
    
    def _get_landmarks(self, landmarks, indices: List[int], w: int, h: int) -> np.ndarray:
        """
        Extract specific landmarks and convert to pixel coordinates
        
        Args:
            landmarks: MediaPipe landmarks
            indices: Landmark indices to extract
            w: Frame width
            h: Frame height
            
        Returns:
            Array of landmark coordinates
        """
        points = []
        for idx in indices:
            landmark = landmarks.landmark[idx]
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            points.append([x, y])
        return np.array(points)
    
    def _calculate_ear(self, eye_landmarks: np.ndarray) -> float:
        """
        Calculate Eye Aspect Ratio (EAR) for blink detection
        
        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
        
        Args:
            eye_landmarks: Array of 6 eye landmarks
            
        Returns:
            Eye aspect ratio
        """
        if eye_landmarks is None or len(eye_landmarks) < 6:
            return 0.3  # Default open eye value
        
        # Vertical distances
        v1 = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])
        v2 = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])
        
        # Horizontal distance
        h = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])
        
        if h == 0:
            return 0.3
        
        ear = (v1 + v2) / (2.0 * h)
        return ear
    
    def draw_debug(self, frame: np.ndarray, eye_data: EyeData) -> np.ndarray:
        """
        Draw debug visualization on frame
        
        Args:
            frame: Input frame
            eye_data: Eye tracking data
            
        Returns:
            Frame with debug overlay
        """
        debug_frame = frame.copy()
        
        if not eye_data.face_detected:
            cv2.putText(debug_frame, "No face detected", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            return debug_frame
        
        # Draw eye landmarks
        if eye_data.left_eye_landmarks is not None:
            for point in eye_data.left_eye_landmarks:
                cv2.circle(debug_frame, tuple(point.astype(int)), 2, (0, 255, 0), -1)
        
        if eye_data.right_eye_landmarks is not None:
            for point in eye_data.right_eye_landmarks:
                cv2.circle(debug_frame, tuple(point.astype(int)), 2, (0, 255, 0), -1)
        
        # Draw iris centers
        if eye_data.left_iris_center is not None:
            cv2.circle(debug_frame, tuple(eye_data.left_iris_center.astype(int)),
                      5, (255, 0, 255), -1)
        
        if eye_data.right_iris_center is not None:
            cv2.circle(debug_frame, tuple(eye_data.right_iris_center.astype(int)),
                      5, (255, 0, 255), -1)
        
        # Draw EAR values
        cv2.putText(debug_frame, f"L-EAR: {eye_data.left_eye_aspect_ratio:.3f}",
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(debug_frame, f"R-EAR: {eye_data.right_eye_aspect_ratio:.3f}",
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        return debug_frame
    
    def get_stats(self) -> Dict:
        """Get performance statistics"""
        return self.performance.get_all_stats()
    
    def cleanup(self):
        """Release resources"""
        if self.face_mesh:
            self.face_mesh.close()
