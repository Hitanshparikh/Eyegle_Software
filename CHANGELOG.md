# Changelog

All notable changes to Eyegle will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-18

### 🎉 Initial Release - Eyegle v1.0

**Advanced Eye Tracking & Facial Expression Control Software**  
*Created by Hivizstudios & Hitansh Parikh*

### ✨ Added

#### Core Eye Tracking
- **Real-time face detection** using MediaPipe
- **High-precision iris tracking** with sub-20ms latency
- **Advanced gaze estimation** with screen coordinate mapping
- **Multi-stage smoothing** (EMA + Kalman filtering)
- **Adaptive calibration system** for personalized accuracy

#### Expression Recognition
- **Comprehensive blink detection** (left/right/both/long)
- **Facial expression recognition** (smile, jaw, eyebrows)
- **Head pose tracking** (tilt, nod, shake gestures)
- **Baseline calibration** for individual user adaptation
- **Configurable thresholds** and cooldown timers

#### System Control
- **Smooth cursor movement** with acceleration curves
- **Mouse click simulation** (left/right/double clicks)
- **Keyboard input generation** with key mapping
- **Customizable gesture mapping** through configuration
- **Context-aware actions** with intelligent debouncing

#### User Interface
- **Modern glassmorphism design** with premium dark theme
- **Real-time camera preview** with overlay indicators
- **Floating cursor visualization** with smooth animations
- **Comprehensive settings panel** for easy customization
- **Live performance monitoring** with FPS counter

#### Safety & Reliability
- **Emergency stop mechanism** (ESC key override)
- **Auto-pause on face loss** for safety
- **Click rate limiting** to prevent accidental actions
- **Comprehensive logging system** for troubleshooting
- **Error handling and recovery** mechanisms

#### Performance
- **Multithreaded architecture** for optimal performance
- **Ring buffer implementation** for efficient frame handling
- **Intelligent frame skipping** when system is overloaded
- **GPU acceleration support** (auto-detection)
- **Real-time performance metrics** and profiling

#### Configuration
- **YAML-based configuration** system
- **Hot-reloading** of settings without restart
- **User profile management** with multiple calibrations
- **Gesture customization** through intuitive interface
- **Performance tuning** options for different hardware

#### Documentation
- **Comprehensive README** with quick start guide
- **Detailed user guide** with step-by-step instructions
- **Complete gesture mapping** reference
- **Developer documentation** for contributions
- **Installation and setup** guides

### 🔧 Technical Details

- **Python 3.11+** requirement for optimal performance
- **MediaPipe 0.10.30+** for robust face tracking
- **OpenCV 4.8.0+** for computer vision processing
- **PySide6 6.6.0+** for modern Qt-based interface
- **Cross-platform support** (Windows primary, Linux/macOS planned)

### 📊 Performance Benchmarks

- **Latency**: 15-18ms typical, <20ms guaranteed
- **Accuracy**: 95%+ cursor precision after calibration
- **CPU Usage**: 15-25% on modern processors
- **Memory Usage**: ~200MB RAM footprint
- **Frame Rate**: 30-60 FPS depending on camera and system

### 🚀 Release Highlights

This initial release represents a complete, production-ready eye tracking solution with:

- **Professional-grade accuracy** suitable for daily computer use
- **Intuitive user experience** designed for accessibility
- **Extensible architecture** for future enhancements
- **Comprehensive safety measures** for reliable operation
- **Modern development practices** with clean, maintainable code

---

### 🙏 Credits

**Primary Development**: [Hitansh Parikh](https://github.com/hitanshparikh)  
**Organization**: [Hivizstudios](https://github.com/hivizstudios)  

**Technology Stack**: MediaPipe, OpenCV, PySide6, Python  
**Special Thanks**: The open-source computer vision community

---

**Download**: [Release v1.0.0](https://github.com/hivizstudios/eyegle/releases/tag/v1.0.0)  
**Documentation**: [User Guide](docs/USER_GUIDE.md)  
**Support**: [GitHub Issues](https://github.com/hivizstudios/eyegle/issues)

*Empowering accessibility through advanced computer vision technology* ✨