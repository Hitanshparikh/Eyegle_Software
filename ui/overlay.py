"""
Cursor Overlay - Visual feedback for eye-controlled cursor
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPainter, QColor, QPen, QRadialGradient
import numpy as np


class CursorOverlay(QWidget):
    """Floating cursor overlay with smooth animations"""
    
    def __init__(self, config: dict):
        """
        Initialize cursor overlay
        
        Args:
            config: UI configuration dictionary
        """
        super().__init__()
        
        self.config = config
        
        # Window settings
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        # Overlay properties
        self.overlay_size = config.get('overlay_size', 20)
        self.overlay_color = QColor(config.get('overlay_color', '#00FF88'))
        self.opacity_value = config.get('opacity', 0.95)
        
        # Animation
        self._pulse_phase = 0.0
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self._update_pulse)
        self.pulse_timer.start(16)  # 60fps
        
        # Visibility
        self.overlay_enabled = config.get('show_overlay', True)
        
        # Size
        self.resize(self.overlay_size * 3, self.overlay_size * 3)
        
        # State
        self.is_clicking = False
        
    def set_position(self, x: int, y: int):
        """
        Move overlay to position
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        # Center overlay on cursor
        offset = self.overlay_size * 1.5
        self.move(int(x - offset), int(y - offset))
    
    def _update_pulse(self):
        """Update pulse animation"""
        self._pulse_phase += 0.1
        if self._pulse_phase > 2 * np.pi:
            self._pulse_phase = 0.0
        self.update()
    
    def paintEvent(self, event):
        """Draw overlay"""
        if not self.overlay_enabled:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        # Pulse effect
        pulse = np.sin(self._pulse_phase) * 0.2 + 1.0
        radius = self.overlay_size * pulse
        
        # Glow effect
        gradient = QRadialGradient(center_x, center_y, radius * 1.5)
        color = self.overlay_color
        
        if self.is_clicking:
            # Brighten when clicking
            color = QColor(255, 100, 100)
        
        gradient.setColorAt(0.0, QColor(color.red(), color.green(), color.blue(), int(200 * self.opacity_value)))
        gradient.setColorAt(0.5, QColor(color.red(), color.green(), color.blue(), int(100 * self.opacity_value)))
        gradient.setColorAt(1.0, QColor(color.red(), color.green(), color.blue(), 0))
        
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(center_x - radius * 1.5),
                           int(center_y - radius * 1.5),
                           int(radius * 3),
                           int(radius * 3))
        
        # Center dot
        painter.setBrush(color)
        pen = QPen(QColor(255, 255, 255, int(150 * self.opacity_value)))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawEllipse(int(center_x - radius * 0.3),
                           int(center_y - radius * 0.3),
                           int(radius * 0.6),
                           int(radius * 0.6))
    
    def set_clicking(self, clicking: bool):
        """Set clicking state for visual feedback"""
        self.is_clicking = clicking
        self.update()
    
    def set_enabled(self, enabled: bool):
        """Enable/disable overlay"""
        self.overlay_enabled = enabled
        self.setVisible(enabled)
    
    def set_color(self, color: str):
        """Change overlay color"""
        self.overlay_color = QColor(color)
        self.update()
