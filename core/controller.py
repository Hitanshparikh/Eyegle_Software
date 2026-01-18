"""
System Controller - Executes mouse and keyboard actions
Integrates with OS-level input control
"""

import pyautogui
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController
import time
from typing import Optional, Tuple
from utils.logger import setup_logger
from utils.safety import SafetyManager


class SystemController:
    """Controls mouse and keyboard based on eye tracking and expressions"""
    
    def __init__(self, config: dict, safety_manager: SafetyManager):
        """
        Initialize system controller
        
        Args:
            config: Configuration dictionary
            safety_manager: Safety manager instance
        """
        self.logger = setup_logger("Controller")
        self.config = config
        self.safety = safety_manager
        
        # Initialize controllers
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        
        # Configure PyAutoGUI
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort
        pyautogui.PAUSE = 0.01  # Minimal delay between actions
        
        # Get screen size
        self.screen_width, self.screen_height = pyautogui.size()
        self.logger.info(f"🖥️ Screen: {self.screen_width}x{self.screen_height}")
        
        # State
        self.cursor_enabled = True
        self.keyboard_mode = False
        self.last_action_time = 0.0
        
    def move_cursor(self, x: float, y: float, smooth: bool = True):
        """
        Move cursor to position
        
        Args:
            x: X coordinate
            y: Y coordinate
            smooth: Use smooth movement
        """
        # Debug logging
        self.logger.debug(f"🎯 Move cursor request: ({x:.1f}, {y:.1f})")
        self.logger.debug(f"🎯 Cursor enabled: {self.cursor_enabled}")
        self.logger.debug(f"🎯 Safety active: {self.safety.is_active()}")
        
        if not self.cursor_enabled:
            self.logger.debug("❌ Cursor movement disabled")
            return
            
        if not self.safety.is_active():
            self.logger.debug("❌ Safety manager not active")
            return
        
        # Clamp to screen bounds
        x = max(0, min(int(x), self.screen_width - 1))
        y = max(0, min(int(y), self.screen_height - 1))
        
        try:
            if smooth:
                # Use pynput for instant positioning (no animation)
                self.mouse.position = (x, y)
                self.logger.debug(f"✅ Cursor moved to ({x}, {y})")
            else:
                pyautogui.moveTo(x, y)
                self.logger.debug(f"✅ Cursor moved to ({x}, {y}) via PyAutoGUI")
        except Exception as e:
            self.logger.error(f"❌ Cursor move error: {e}")
    
    def get_cursor_position(self) -> Tuple[int, int]:
        """
        Get current cursor position
        
        Returns:
            (x, y) cursor position
        """
        return pyautogui.position()
    
    def click(self, button: str = 'left', double: bool = False):
        """
        Perform mouse click
        
        Args:
            button: 'left', 'right', or 'middle'
            double: Perform double click
        """
        if not self.safety.can_perform_action('click'):
            self.logger.debug("🛡️ Click blocked by safety")
            return
        
        try:
            if button == 'left':
                btn = Button.left
            elif button == 'right':
                btn = Button.right
            else:
                btn = Button.middle
            
            if double:
                self.mouse.click(btn, 2)
                self.logger.info("🖱️ Double click")
            else:
                self.mouse.click(btn, 1)
                self.logger.info("🖱️ Click")
            
            self.safety.register_action('click')
            
        except Exception as e:
            self.logger.error(f"❌ Click error: {e}")
    
    def scroll(self, direction: str, amount: int = 3):
        """
        Perform scroll action
        
        Args:
            direction: 'up' or 'down'
            amount: Scroll amount (lines)
        """
        if not self.safety.can_perform_action('scroll'):
            return
        
        try:
            scroll_amount = amount if direction == 'up' else -amount
            self.mouse.scroll(0, scroll_amount)
            
            self.logger.debug(f"📜 Scroll {direction}")
            self.safety.register_action('scroll')
            
        except Exception as e:
            self.logger.error(f"❌ Scroll error: {e}")
    
    def key_press(self, key: str):
        """
        Press a key
        
        Args:
            key: Key name (see pynput.keyboard.Key)
        """
        if not self.safety.can_perform_action('key'):
            return
        
        try:
            # Check if it's a special key
            if hasattr(Key, key):
                self.keyboard.press(getattr(Key, key))
                self.keyboard.release(getattr(Key, key))
            else:
                # Regular character
                self.keyboard.press(key)
                self.keyboard.release(key)
            
            self.logger.debug(f"⌨️ Key: {key}")
            self.safety.register_action('key')
            
        except Exception as e:
            self.logger.error(f"❌ Key press error: {e}")
    
    def execute_action(self, action: str):
        """
        Execute a named action
        
        Args:
            action: Action name from config
        """
        current_time = time.time()
        
        # Debounce rapid actions
        if current_time - self.last_action_time < 0.1:
            return
        
        self.logger.info(f"⚡ Action: {action}")
        
        # Execute based on action type
        if action == 'left_click':
            self.click('left')
        
        elif action == 'right_click':
            self.click('right')
        
        elif action == 'double_click':
            self.click('left', double=True)
        
        elif action == 'back':
            self.key_press('left')  # or browser back
        
        elif action == 'forward':
            self.key_press('right')  # or browser forward
        
        elif action == 'scroll_up':
            self.scroll('up')
        
        elif action == 'scroll_down':
            self.scroll('down')
        
        elif action == 'enter':
            self.key_press('enter')
        
        elif action == 'toggle_keyboard':
            self.keyboard_mode = not self.keyboard_mode
            self.logger.info(f"⌨️ Keyboard mode: {self.keyboard_mode}")
        
        elif action == 'volume_up':
            self.key_press('volume_up')
        
        elif action == 'volume_down':
            self.key_press('volume_down')
        
        elif action == 'play_pause':
            self.key_press('media_play_pause')
        
        elif action == 'cancel':
            self.key_press('esc')
        
        else:
            self.logger.warning(f"⚠️ Unknown action: {action}")
        
        self.last_action_time = current_time
    
    def toggle_cursor(self, enabled: bool):
        """Enable/disable cursor control"""
        self.cursor_enabled = enabled
        self.logger.info(f"🖱️ Cursor control: {'enabled' if enabled else 'disabled'}")
    
    def emergency_stop(self):
        """Emergency stop all actions"""
        self.cursor_enabled = False
        self.keyboard_mode = False
        self.logger.warning("🛑 EMERGENCY STOP")
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Get screen dimensions"""
        return (self.screen_width, self.screen_height)
