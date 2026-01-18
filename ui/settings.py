"""
Settings Panel - Control panel for configuration
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QLabel, QSlider, QCheckBox, QComboBox, QPushButton,
                               QSpinBox, QDoubleSpinBox, QScrollArea)
from PySide6.QtCore import Qt, Signal
from typing import Dict, Any


class SettingsPanel(QScrollArea):
    """Settings and controls panel"""
    
    # Signals for settings changes
    setting_changed = Signal(str, object)  # (setting_name, value)
    
    def __init__(self, config: Dict):
        """
        Initialize settings panel
        
        Args:
            config: Configuration dictionary
        """
        super().__init__()
        
        self.config = config
        
        # Setup scroll area
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Create main widget
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Add setting groups
        main_layout.addWidget(self._create_gaze_settings())
        main_layout.addWidget(self._create_expression_settings())
        main_layout.addWidget(self._create_safety_settings())
        main_layout.addWidget(self._create_ui_settings())
        main_layout.addWidget(self._create_calibration_controls())
        
        main_layout.addStretch()
        
        self.setWidget(main_widget)
        
    def _create_gaze_settings(self) -> QGroupBox:
        """Create gaze tracking settings"""
        group = QGroupBox("👁️ Gaze Tracking")
        layout = QVBoxLayout()
        
        # Smoothing
        smoothing_layout = QHBoxLayout()
        smoothing_layout.addWidget(QLabel("Smoothing:"))
        smoothing_slider = QSlider(Qt.Orientation.Horizontal)
        smoothing_slider.setRange(0, 100)
        smoothing_slider.setValue(int(self.config['gaze']['smoothing_factor'] * 100))
        smoothing_slider.valueChanged.connect(
            lambda v: self.setting_changed.emit('gaze.smoothing_factor', v / 100.0)
        )
        smoothing_layout.addWidget(smoothing_slider)
        smoothing_label = QLabel(f"{smoothing_slider.value()}%")
        smoothing_slider.valueChanged.connect(lambda v: smoothing_label.setText(f"{v}%"))
        smoothing_layout.addWidget(smoothing_label)
        layout.addLayout(smoothing_layout)
        
        # Dead zone
        deadzone_layout = QHBoxLayout()
        deadzone_layout.addWidget(QLabel("Dead Zone:"))
        deadzone_spin = QSpinBox()
        deadzone_spin.setRange(0, 50)
        deadzone_spin.setValue(self.config['gaze']['dead_zone_radius'])
        deadzone_spin.valueChanged.connect(
            lambda v: self.setting_changed.emit('gaze.dead_zone_radius', v)
        )
        deadzone_layout.addWidget(deadzone_spin)
        deadzone_layout.addWidget(QLabel("px"))
        deadzone_layout.addStretch()
        layout.addLayout(deadzone_layout)
        
        # Acceleration
        accel_layout = QHBoxLayout()
        accel_layout.addWidget(QLabel("Acceleration:"))
        accel_spin = QDoubleSpinBox()
        accel_spin.setRange(1.0, 3.0)
        accel_spin.setSingleStep(0.1)
        accel_spin.setValue(self.config['gaze']['acceleration_curve'])
        accel_spin.valueChanged.connect(
            lambda v: self.setting_changed.emit('gaze.acceleration_curve', v)
        )
        accel_layout.addWidget(accel_spin)
        accel_layout.addStretch()
        layout.addLayout(accel_layout)
        
        # Kalman filter
        kalman_check = QCheckBox("Use Kalman Filter")
        kalman_check.setChecked(self.config['gaze']['use_kalman'])
        kalman_check.toggled.connect(
            lambda v: self.setting_changed.emit('gaze.use_kalman', v)
        )
        layout.addWidget(kalman_check)
        
        group.setLayout(layout)
        return group
    
    def _create_expression_settings(self) -> QGroupBox:
        """Create expression detection settings"""
        group = QGroupBox("😊 Expression Detection")
        layout = QVBoxLayout()
        
        # Blink threshold
        blink_layout = QHBoxLayout()
        blink_layout.addWidget(QLabel("Blink Sensitivity:"))
        blink_slider = QSlider(Qt.Orientation.Horizontal)
        blink_slider.setRange(10, 50)
        blink_slider.setValue(int(self.config['expressions']['blink_threshold'] * 100))
        blink_slider.valueChanged.connect(
            lambda v: self.setting_changed.emit('expressions.blink_threshold', v / 100.0)
        )
        blink_layout.addWidget(blink_slider)
        blink_label = QLabel(f"{blink_slider.value()}%")
        blink_slider.valueChanged.connect(lambda v: blink_label.setText(f"{v}%"))
        blink_layout.addWidget(blink_label)
        layout.addLayout(blink_layout)
        
        # Cooldown
        cooldown_layout = QHBoxLayout()
        cooldown_layout.addWidget(QLabel("Cooldown:"))
        cooldown_spin = QSpinBox()
        cooldown_spin.setRange(100, 1000)
        cooldown_spin.setSingleStep(50)
        cooldown_spin.setValue(self.config['expressions']['blink_cooldown_ms'])
        cooldown_spin.valueChanged.connect(
            lambda v: self.setting_changed.emit('expressions.blink_cooldown_ms', v)
        )
        cooldown_layout.addWidget(cooldown_spin)
        cooldown_layout.addWidget(QLabel("ms"))
        cooldown_layout.addStretch()
        layout.addLayout(cooldown_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_safety_settings(self) -> QGroupBox:
        """Create safety settings"""
        group = QGroupBox("🛡️ Safety")
        layout = QVBoxLayout()
        
        # Max clicks per second
        clicks_layout = QHBoxLayout()
        clicks_layout.addWidget(QLabel("Max Clicks/Sec:"))
        clicks_spin = QSpinBox()
        clicks_spin.setRange(1, 10)
        clicks_spin.setValue(self.config['safety']['max_clicks_per_second'])
        clicks_spin.valueChanged.connect(
            lambda v: self.setting_changed.emit('safety.max_clicks_per_second', v)
        )
        clicks_layout.addWidget(clicks_spin)
        clicks_layout.addStretch()
        layout.addLayout(clicks_layout)
        
        # Auto-pause
        pause_check = QCheckBox("Auto-pause when face lost")
        pause_check.setChecked(self.config['safety'].get('auto_pause_no_face_ms', 2000) > 0)
        pause_check.toggled.connect(
            lambda v: self.setting_changed.emit('safety.auto_pause', v)
        )
        layout.addWidget(pause_check)
        
        group.setLayout(layout)
        return group
    
    def _create_ui_settings(self) -> QGroupBox:
        """Create UI settings"""
        group = QGroupBox("🎨 Interface")
        layout = QVBoxLayout()
        
        # Show overlay
        overlay_check = QCheckBox("Show Cursor Overlay")
        overlay_check.setChecked(self.config['ui']['show_overlay'])
        overlay_check.toggled.connect(
            lambda v: self.setting_changed.emit('ui.show_overlay', v)
        )
        layout.addWidget(overlay_check)
        
        # Show FPS
        fps_check = QCheckBox("Show FPS Counter")
        fps_check.setChecked(self.config['ui']['show_fps'])
        fps_check.toggled.connect(
            lambda v: self.setting_changed.emit('ui.show_fps', v)
        )
        layout.addWidget(fps_check)
        
        # Show debug
        debug_check = QCheckBox("Show Debug Info")
        debug_check.setChecked(self.config['ui']['show_debug'])
        debug_check.toggled.connect(
            lambda v: self.setting_changed.emit('ui.show_debug', v)
        )
        layout.addWidget(debug_check)
        
        group.setLayout(layout)
        return group
    
    def _create_calibration_controls(self) -> QGroupBox:
        """Create calibration controls"""
        group = QGroupBox("🎯 Calibration")
        layout = QVBoxLayout()
        
        # Eye dominance
        dominance_layout = QHBoxLayout()
        dominance_layout.addWidget(QLabel("Eye Dominance:"))
        dominance_combo = QComboBox()
        dominance_combo.addItems(["Left", "Right", "Both"])
        current_dominance = self.config['user'].get('eye_dominance', 'right')
        dominance_combo.setCurrentText(current_dominance.capitalize())
        dominance_combo.currentTextChanged.connect(
            lambda v: self.setting_changed.emit('user.eye_dominance', v.lower())
        )
        dominance_layout.addWidget(dominance_combo)
        dominance_layout.addStretch()
        layout.addLayout(dominance_layout)
        
        # Calibration points
        points_layout = QHBoxLayout()
        points_layout.addWidget(QLabel("Calibration Points:"))
        points_combo = QComboBox()
        points_combo.addItems(["5 points", "9 points"])
        current_points = self.config['calibration'].get('points', 9)
        points_combo.setCurrentText(f"{current_points} points")
        points_combo.currentTextChanged.connect(
            lambda v: self.setting_changed.emit('calibration.points', int(v.split()[0]))
        )
        points_layout.addWidget(points_combo)
        points_layout.addStretch()
        layout.addLayout(points_layout)
        
        # Auto-adjust drift
        drift_check = QCheckBox("Auto-adjust drift")
        drift_check.setChecked(self.config['calibration'].get('auto_adjust_drift', True))
        drift_check.toggled.connect(
            lambda v: self.setting_changed.emit('calibration.auto_adjust_drift', v)
        )
        layout.addWidget(drift_check)
        
        group.setLayout(layout)
        return group
