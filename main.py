"""
Eyegle v1.0 - Main Entry Point
Advanced Eye Tracking & Facial Expression Control Software

Created by Hivizstudios & Hitansh Parikh
Professional-grade assistive technology for computer control
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from ui.app import MainWindow
from utils.logger import setup_logger
import yaml


def load_config(config_path: str = "config.yaml") -> dict:
    """
    Load application configuration
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    # Setup logger
    logger = setup_logger("Main", level=10)  # DEBUG level
    
    logger.info("=" * 60)
    logger.info("👁️  EYEGLE v1.0")
    logger.info("Advanced Eye Tracking by Hivizstudios")
    logger.info("Created by Hitansh Parikh")
    logger.info("=" * 60)
    
    # Load configuration
    logger.info("📋 Loading configuration...")
    config = load_config()
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Eyegle")
    app.setOrganizationName("Hivizstudios")
    
    # Create main window
    logger.info("🚀 Launching application...")
    window = MainWindow(config)
    window.show()
    
    logger.info("✅ Application ready")
    logger.info("ℹ️  Press ESC for emergency stop")
    logger.info("ℹ️  Press Ctrl+C to calibrate")
    
    # Run application
    exit_code = app.exec()
    
    logger.info("👋 Application closed")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
