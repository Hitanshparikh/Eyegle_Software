"""
Eyegle v1.0 - Main UI Application
Premium interface with real-time camera feed and controls

Created by Hivizstudios & Hitansh Parikh
Advanced Eye Tracking & Facial Expression Control
"""

import sys
import cv2
import numpy as np
import time
from pathlib import Path

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QPushButton, QGroupBox,
                               QStatusBar, QSplitter, QFrame, QComboBox)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QImage, QPixmap, QKeySequence, QShortcut
from typing import List

# Import core modules
from core.camera import Camera
from core.tracker import FaceTracker, EyeData
from core.gaze_mapper import GazeMapper
from core.smoother import CursorSmoother
from core.expression_engine import ExpressionEngine, Expression
from core.controller import SystemController
from calibration.calibrator import Calibrator, CalibrationState
from utils.logger import setup_logger
from utils.fps import FPSCounter
from utils.safety import SafetyManager
from ui.settings import SettingsPanel
from ui.overlay import CursorOverlay

import yaml


class ProcessingThread(QThread):
    """Background thread for eye tracking processing"""
    
    # Signals
    frame_processed = Signal(np.ndarray, EyeData, float, float)  # frame, eye_data, gaze_x, gaze_y
    expression_detected = Signal(str)  # expression name
    fps_updated = Signal(float)  # current FPS
    
    def __init__(self, camera, tracker, gaze_mapper, smoother, expression_engine, config):
        super().__init__()
        self.camera = camera
        self.tracker = tracker
        self.gaze_mapper = gaze_mapper
        self.smoother = smoother
        self.expression_engine = expression_engine
        self.config = config
        
        self.running = False
        self.fps_counter = FPSCounter()
        
    def run(self):
        """Main processing loop"""
        self.running = True
        
        while self.running:
            # Get frame from camera
            frame = self.camera.get_frame()
            if frame is None:
                time.sleep(0.01)
                continue
            
            # Track face and eyes
            eye_data = self.tracker.process_frame(frame)
            
            # Estimate gaze
            if eye_data.face_detected:
                h, w = frame.shape[:2]
                
                # Convert iris centers to numpy arrays for gaze mapper
                left_iris = np.array(eye_data.left_iris_center) if eye_data.left_iris_center else None
                right_iris = np.array(eye_data.right_iris_center) if eye_data.right_iris_center else None
                
                gaze = self.gaze_mapper.estimate_gaze(
                    left_iris,
                    right_iris,
                    w, h
                )
                
                if gaze is not None:
                    screen_pos = self.gaze_mapper.gaze_to_screen(gaze)
                    screen_size = self.gaze_mapper.screen_width, self.gaze_mapper.screen_height
                    smoothed_pos = self.smoother.smooth(screen_pos, screen_size)
                    
                    # Detect expressions
                    expr_state = self.expression_engine.detect_expression(eye_data)
                    if expr_state.expression != Expression.NONE:
                        self.expression_detected.emit(expr_state.expression.value)
                    
                    # Emit results
                    self.frame_processed.emit(
                        frame, eye_data,
                        smoothed_pos[0], smoothed_pos[1]
                    )
                else:
                    # Gaze estimation failed
                    self.frame_processed.emit(frame, eye_data, -1, -1)
            else:
                # No face detected
                self.frame_processed.emit(frame, eye_data, -1, -1)
            
            # Update FPS
            fps = self.fps_counter.tick()
            self.fps_updated.emit(fps)
            
            # Small sleep to prevent CPU overload
            time.sleep(0.001)
    
    def stop(self):
        """Stop processing thread"""
        self.running = False


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, config: dict):
        """
        Initialize main window
        
        Args:
            config: Application configuration
        """
        super().__init__()
        
        self.logger = setup_logger("MainUI")
        self.config = config
        
        # Initialize components
        self._init_core_systems()
        self._init_ui()
        self._load_theme()
        self._setup_shortcuts()
        
        # Initialize camera selection after UI is ready
        self._refresh_cameras()
        
        # Start systems
        self._start_camera()
        
        self.logger.info("✅ Application initialized")
    
    def _init_core_systems(self):
        """Initialize core eye tracking systems"""
        self.logger.info("🔧 Initializing core systems...")
        
        # Camera
        self.camera = Camera(self.config['camera'])
        
        # Tracker
        self.tracker = FaceTracker(self.config)
        
        # Get screen size
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        screen_width = screen.width()
        screen_height = screen.height()
        
        # Gaze mapper
        self.gaze_mapper = GazeMapper(
            self.config,
            screen_width,
            screen_height
        )
        
        # Smoother
        self.smoother = CursorSmoother(self.config['gaze'])
        
        # Expression engine
        self.expression_engine = ExpressionEngine(self.config['expressions'])
        
        # Safety manager
        self.safety_manager = SafetyManager(self.config['safety'])
        
        # Controller
        self.controller = SystemController(self.config, self.safety_manager)
        
        # Calibrator
        self.calibrator = Calibrator(
            self.config['calibration'],
            screen_width,
            screen_height
        )
        
        # Cursor overlay
        self.cursor_overlay = CursorOverlay(self.config['ui'])
        
        # Processing thread
        self.processing_thread = None
        
        # State
        self.is_running = False
        self.is_calibrating = False
        self.current_fps = 0.0
        
    def _refresh_cameras(self):
        """Refresh available cameras list"""
        # Safety check - only proceed if UI is initialized
        if not hasattr(self, 'camera_combo'):
            return
        
        self.logger.info("🔄 Refreshing camera list...")
        self.camera_combo.clear()
        
        # Clear the camera cache to force re-detection
        self.camera._available_cameras = None
        
        # Show loading indicator
        self.camera_combo.addItem("🔍 Scanning cameras...", -1)
        self.camera_combo.setEnabled(False)
        
        # Get fresh camera list
        try:
            available_cameras = self.camera.get_available_cameras()
            self.camera_combo.clear()  # Remove loading indicator
            
            if available_cameras:
                self.logger.info(f"📹 Found {len(available_cameras)} cameras")
                for device_id, device_name in available_cameras:
                    self.camera_combo.addItem(device_name, device_id)
                    self.logger.info(f"  - {device_name}")
                
                # Select current camera if it's in the list
                current_index = -1
                for i in range(self.camera_combo.count()):
                    if self.camera_combo.itemData(i) == self.camera.device_id:
                        current_index = i
                        break
                        
                if current_index >= 0:
                    self.camera_combo.setCurrentIndex(current_index)
                else:
                    # Current camera not found, select first available
                    if self.camera_combo.count() > 0:
                        self.camera_combo.setCurrentIndex(0)
            else:
                self.logger.warning("⚠️ No cameras found")
                self.camera_combo.addItem("❌ No cameras found", -1)
                
        except Exception as e:
            self.logger.error(f"❌ Camera detection failed: {e}")
            self.camera_combo.clear()
            self.camera_combo.addItem("❌ Detection failed", -1)
            
        finally:
            self.camera_combo.setEnabled(True)
            
    def _on_camera_changed(self, index: int):
        """Handle camera selection change"""
        if index < 0:
            return
            
        device_id = self.camera_combo.itemData(index)
        if device_id is None or device_id < 0:
            return
            
        if device_id != self.camera.device_id:
            self.logger.info(f"📷 Switching to camera {device_id}")
            
            # Stop processing if running
            was_running = self.is_running
            if was_running:
                self._stop_processing()
                
            # Change camera
            success = self.camera.set_device(device_id)
            
            if success:
                self.logger.info(f"✅ Camera switched to device {device_id}")
                # Restart if was running
                if was_running:
                    self._start_processing()
            else:
                self.logger.error(f"❌ Failed to switch to camera {device_id}")
                
    def _start_processing(self):
        """Start eye tracking processing"""
        self._start_tracking()
        
    def _stop_processing(self):
        """Stop eye tracking processing"""
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.stop()
            self.processing_thread.wait(1000)
            self.processing_thread = None
        self.is_running = False
                
    def _create_right_panel(self) -> QWidget:
        """Create right status panel"""
        from PySide6.QtWidgets import QVBoxLayout
        
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.addStretch()
        
        return panel
        
    def _init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("Eyegle v1.0 - Advanced Eye Tracking")
        self.setMinimumSize(1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Left panel - Camera and controls
        left_panel = self._create_left_panel()
        main_layout.addWidget(left_panel, stretch=1)
        
        # Right panel - Status and settings
        right_panel = self._create_right_panel()
        main_layout.addWidget(right_panel, stretch=1)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_status)
        self.update_timer.start(100)  # 10Hz UI update
        
    def _create_camera_selection_group(self) -> QGroupBox:
        """Create camera selection group"""
        from PySide6.QtWidgets import QVBoxLayout, QGroupBox, QComboBox, QPushButton, QLabel, QHBoxLayout
        
        group = QGroupBox("📹 Camera Selection")
        layout = QVBoxLayout(group)
        
        # Camera selector row
        camera_select_layout = QHBoxLayout()
        camera_select_layout.addWidget(QLabel("Camera:"))
        
        self.camera_combo = QComboBox()
        self.camera_combo.currentIndexChanged.connect(self._on_camera_changed)
        camera_select_layout.addWidget(self.camera_combo)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._refresh_cameras)
        camera_select_layout.addWidget(refresh_btn)
        
        layout.addLayout(camera_select_layout)
        return group
    
    def _create_left_panel(self) -> QWidget:
        """Create left panel with camera feed"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("👁️ Eyegle v1.0")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Camera selection
        camera_selection_group = self._create_camera_selection_group()
        layout.addWidget(camera_selection_group)
        
        # Camera feed
        camera_group = QGroupBox("📷 Camera Feed")
        camera_layout = QVBoxLayout()
        
        self.camera_label = QLabel()
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setStyleSheet("background-color: #1a1a1a; border-radius: 10px;")
        self.camera_label.setText("Camera initializing...")
        camera_layout.addWidget(self.camera_label)
        
        camera_group.setLayout(camera_layout)
        layout.addWidget(camera_group)
        
        # Controls
        controls_group = self._create_controls_group()
        layout.addWidget(controls_group)
        
        # Stats
        stats_group = self._create_stats_group()
        layout.addWidget(stats_group)
        
        return panel
    
    def _create_controls_group(self) -> QGroupBox:
        """Create control buttons group"""
        group = QGroupBox("🎮 Controls")
        layout = QVBoxLayout()
        
        # Row 1: Start/Stop
        row1 = QHBoxLayout()
        
        self.start_button = QPushButton("▶️ Start Tracking")
        self.start_button.setObjectName("primaryButton")
        self.start_button.clicked.connect(self._start_tracking)
        row1.addWidget(self.start_button)
        
        self.stop_button = QPushButton("⏸️ Stop")
        self.stop_button.setObjectName("dangerButton")
        self.stop_button.clicked.connect(self._stop_tracking)
        self.stop_button.setEnabled(False)
        row1.addWidget(self.stop_button)
        
        layout.addLayout(row1)
        
        # Row 2: Calibration
        row2 = QHBoxLayout()
        
        self.calibrate_button = QPushButton("🎯 Calibrate")
        self.calibrate_button.clicked.connect(self._start_calibration)
        row2.addWidget(self.calibrate_button)
        
        self.reset_calib_button = QPushButton("🔄 Reset Calibration")
        self.reset_calib_button.clicked.connect(self._reset_calibration)
        row2.addWidget(self.reset_calib_button)
        
        layout.addLayout(row2)
        
        # Emergency stop
        self.emergency_button = QPushButton("🛑 EMERGENCY STOP (ESC)")
        self.emergency_button.setObjectName("dangerButton")
        self.emergency_button.clicked.connect(self._emergency_stop)
        layout.addWidget(self.emergency_button)
        
        group.setLayout(layout)
        return group
    
    def _create_stats_group(self) -> QGroupBox:
        """Create statistics display group"""
        group = QGroupBox("📊 Statistics")
        layout = QVBoxLayout()
        
        self.fps_label = QLabel("FPS: --")
        self.fps_label.setObjectName("statusLabel")
        layout.addWidget(self.fps_label)
        
        self.status_label = QLabel("Status: Idle")
        layout.addWidget(self.status_label)
        
        self.face_label = QLabel("Face: Not detected")
        layout.addWidget(self.face_label)
        
        self.gaze_label = QLabel("Gaze: (---, ---)")
        layout.addWidget(self.gaze_label)
        
        self.calibration_label = QLabel("Calibration: Not calibrated")
        layout.addWidget(self.calibration_label)
        
        group.setLayout(layout)
        return group
    
    def _create_right_panel(self) -> QWidget:
        """Create right panel with settings"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Settings panel
        self.settings_panel = SettingsPanel(self.config)
        self.settings_panel.setting_changed.connect(self._on_setting_changed)
        layout.addWidget(self.settings_panel)
        
        return panel
    
    def _load_theme(self):
        """Load application theme"""
        theme_path = Path("ui/theme.qss")
        if theme_path.exists():
            with open(theme_path, 'r') as f:
                self.setStyleSheet(f.read())
            self.logger.info("🎨 Theme loaded")
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Emergency stop
        esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        esc_shortcut.activated.connect(self._emergency_stop)
        
        # Quick calibration
        calib_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        calib_shortcut.activated.connect(self._start_calibration)
    
    def _start_camera(self):
        """Start camera system"""
        if self.camera.start():
            self.logger.info("✅ Camera started")
            
            # Start camera feed update
            self.camera_timer = QTimer()
            self.camera_timer.timeout.connect(self._update_camera_feed)
            self.camera_timer.start(33)  # 30fps
        else:
            self.logger.error("❌ Failed to start camera")
            self.statusBar().showMessage("ERROR: Camera failed to start")
    
    def _update_camera_feed(self):
        """Update camera feed display"""
        frame = self.camera.get_frame()
        if frame is not None:
            # Convert to Qt format
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            
            # Scale to fit
            scaled_pixmap = pixmap.scaled(
                self.camera_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.camera_label.setPixmap(scaled_pixmap)
    
    def _start_tracking(self):
        """Start eye tracking"""
        if self.is_running:
            return
        
        self.logger.info("▶️ Starting tracking...")
        
        # Create and start processing thread
        self.processing_thread = ProcessingThread(
            self.camera,
            self.tracker,
            self.gaze_mapper,
            self.smoother,
            self.expression_engine,
            self.config
        )
        
        self.processing_thread.frame_processed.connect(self._on_frame_processed)
        self.processing_thread.expression_detected.connect(self._on_expression_detected)
        self.processing_thread.fps_updated.connect(self._on_fps_updated)
        
        self.processing_thread.start()
        
        # Show cursor overlay
        self.cursor_overlay.show()
        
        self.is_running = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        self.statusBar().showMessage("Tracking active")
    
    def _stop_tracking(self):
        """Stop eye tracking"""
        if not self.is_running:
            return
        
        self.logger.info("⏸️ Stopping tracking...")
        
        # Stop processing thread
        if self.processing_thread:
            self.processing_thread.stop()
            self.processing_thread.wait()
            self.processing_thread = None
        
        # Hide cursor overlay
        self.cursor_overlay.hide()
        
        self.is_running = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        self.statusBar().showMessage("Tracking stopped")
    
    def _on_frame_processed(self, frame, eye_data, gaze_x, gaze_y):
        """Handle processed frame"""
        # Debug logging
        if eye_data.face_detected:
            self.logger.debug(f"👁️ Frame processed: face={eye_data.face_detected}, gaze=({gaze_x:.1f}, {gaze_y:.1f})")
        
        # Update cursor position
        if gaze_x >= 0 and gaze_y >= 0 and eye_data.face_detected:
            self.logger.debug(f"🎯 Moving cursor to ({gaze_x:.1f}, {gaze_y:.1f})")
            self.controller.move_cursor(gaze_x, gaze_y)
            self.cursor_overlay.set_position(int(gaze_x), int(gaze_y))
            
            # Update safety
            self.safety_manager.update_face_detection(True)
        else:
            self.logger.debug(f"❌ No cursor movement: gaze=({gaze_x:.1f}, {gaze_y:.1f}), face={eye_data.face_detected}")
            self.safety_manager.update_face_detection(False)
        
        # Update face detection status
        if eye_data.face_detected:
            self.face_label.setText("✅ Face: Detected")
            self.gaze_label.setText(f"👁️ Gaze: ({int(gaze_x)}, {int(gaze_y)})")
        else:
            self.face_label.setText("❌ Face: Not detected")
            self.gaze_label.setText("👁️ Gaze: ---")
    
    def _on_expression_detected(self, expression: str):
        """Handle detected expression"""
        self.logger.info(f"😊 Expression: {expression}")
        
        # Get action for expression
        action = self.config['actions'].get(expression)
        if action:
            self.controller.execute_action(action)
    
    def _on_fps_updated(self, fps: float):
        """Handle FPS update"""
        self.current_fps = fps
    
    def _update_status(self):
        """Update status displays"""
        if self.config['ui']['show_fps']:
            self.fps_label.setText(f"FPS: {self.current_fps:.1f}")
        
        # Update calibration status
        if self.gaze_mapper.is_calibrated:
            quality = self.gaze_mapper.get_calibration_quality()
            self.calibration_label.setText(f"✅ Calibrated ({quality*100:.0f}%)")
        else:
            self.calibration_label.setText("⚠️ Not calibrated")
        
        # Update safety status
        safety_status = self.safety_manager.get_status()
        if not safety_status['enabled']:
            self.status_label.setText("🛑 Status: STOPPED")
        elif safety_status['paused']:
            self.status_label.setText("⏸️ Status: PAUSED")
        elif self.is_running:
            self.status_label.setText("✅ Status: ACTIVE")
        else:
            self.status_label.setText("⏸️ Status: Idle")
    
    def _start_calibration(self):
        """Start calibration process"""
        self.logger.info("🎯 Starting calibration...")
        
        if not self.is_running:
            self.statusBar().showMessage("❌ Start tracking first before calibrating")
            return
        
        # Stop current processing during calibration
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.stop()
            self.processing_thread.wait(1000)
        
        # Start calibration dialog
        self._run_calibration_sequence()
        
    def _run_calibration_sequence(self):
        """Run the calibration sequence"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar
        from PySide6.QtCore import QTimer, Qt
        from PySide6.QtGui import QFont
        
        # Create calibration dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Eyegle v1.0 - Calibration")
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        dialog.showFullScreen()
        dialog.setStyleSheet("background-color: black; color: white;")
        
        layout = QVBoxLayout(dialog)
        
        # Instructions
        instructions = QLabel("Look at the GREEN DOT and press SPACE when ready")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(24)
        instructions.setFont(font)
        layout.addWidget(instructions)
        
        # Target dot
        target = QLabel("●")
        target.setAlignment(Qt.AlignmentFlag.AlignCenter)
        target.setStyleSheet("color: lime; font-size: 60px;")
        layout.addWidget(target)
        
        # Progress
        progress = QProgressBar()
        progress.setMaximum(9)  # 9 calibration points
        progress.setValue(0)
        layout.addWidget(progress)
        
        # Skip button
        skip_btn = QPushButton("SKIP CALIBRATION (ESC)")
        skip_btn.clicked.connect(lambda: self._finish_calibration(dialog, False))
        layout.addWidget(skip_btn)
        
        # Calibration points (3x3 grid)
        points = [
            (0.1, 0.1), (0.5, 0.1), (0.9, 0.1),  # Top row
            (0.1, 0.5), (0.5, 0.5), (0.9, 0.5),  # Middle row
            (0.1, 0.9), (0.5, 0.9), (0.9, 0.9)   # Bottom row
        ]
        
        self.calibration_data = []
        self.current_point = 0
        
        def next_point():
            if self.current_point >= len(points):
                self._finish_calibration(dialog, True)
                return
                
            # Move to next calibration point
            point_x, point_y = points[self.current_point]
            screen_x = int(point_x * self.width())
            screen_y = int(point_y * self.height())
            
            # Update UI
            instructions.setText(f"Look at the GREEN DOT ({self.current_point + 1}/9)")
            progress.setValue(self.current_point + 1)
            
            # Collect calibration data
            self._collect_calibration_point(screen_x, screen_y)
            
            self.current_point += 1
            
        def keyPressEvent(event):
            if event.key() == Qt.Key.Key_Space:
                next_point()
            elif event.key() == Qt.Key.Key_Escape:
                self._finish_calibration(dialog, False)
        
        dialog.keyPressEvent = keyPressEvent
        
        # Start calibration
        next_point()
        dialog.exec()
        
    def _collect_calibration_point(self, screen_x: int, screen_y: int):
        """Collect calibration data for a specific point"""
        # Get current eye data from camera
        frame = self.camera.get_frame()
        if frame is not None:
            eye_data = self.tracker.process_frame(frame)
            if eye_data.face_detected and eye_data.left_iris_center and eye_data.right_iris_center:
                self.calibration_data.append({
                    'screen_pos': (screen_x, screen_y),
                    'left_iris': eye_data.left_iris_center,
                    'right_iris': eye_data.right_iris_center
                })
                self.logger.info(f"📍 Calibration point collected: ({screen_x}, {screen_y})")
        
    def _finish_calibration(self, dialog, success: bool):
        """Finish calibration process"""
        dialog.close()
        
        if success and len(self.calibration_data) >= 4:  # Need at least 4 points
            # Apply calibration data to gaze mapper
            self.gaze_mapper.set_calibration_data(self.calibration_data)
            self.statusBar().showMessage("✅ Calibration completed successfully!")
            self.logger.info("✅ Calibration completed successfully")
        else:
            self.statusBar().showMessage("⚠️ Calibration skipped or insufficient data")
            self.logger.warning("⚠️ Calibration skipped or failed")
        
        # Restart processing
        self._start_processing()
    
    
    def _reset_calibration(self):
        """Reset calibration"""
        self.gaze_mapper.reset_calibration()
        self.smoother.reset()
        self.logger.info("🔄 Calibration reset")
        self.statusBar().showMessage("Calibration reset")
    
    def _on_setting_changed(self, setting_name: str, value):
        """Handle setting change"""
        self.logger.info(f"⚙️ Setting changed: {setting_name} = {value}")
        
        # Update config
        keys = setting_name.split('.')
        config_section = self.config
        for key in keys[:-1]:
            config_section = config_section[key]
        config_section[keys[-1]] = value
        
        # Apply changes
        if setting_name.startswith('ui.show_overlay'):
            self.cursor_overlay.set_enabled(value)
    
    def _emergency_stop(self):
        """Emergency stop all actions"""
        self.logger.warning("🛑 EMERGENCY STOP")
        self._stop_tracking()
        self.controller.emergency_stop()
        self.safety_manager.emergency_stop()
        self.statusBar().showMessage("EMERGENCY STOP ACTIVATED")
    
    def closeEvent(self, event):
        """Handle window close"""
        self.logger.info("Shutting down...")
        
        # Stop tracking
        self._stop_tracking()
        
        # Stop camera
        self.camera.stop()
        
        # Cleanup
        self.tracker.cleanup()
        
        # Hide overlay
        self.cursor_overlay.close()
        
        event.accept()
