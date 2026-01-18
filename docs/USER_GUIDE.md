# Eyegle v1.0 - User Guide
**Advanced Eye Tracking & Facial Expression Control**  
*Created by Hivizstudios & Hitansh Parikh*

## 📖 Table of Contents
- [Installation](#installation)
- [First-Time Setup](#first-time-setup)
- [Calibration](#calibration)
- [Daily Usage](#daily-usage)
- [Gesture Controls](#gesture-controls)
- [Troubleshooting](#troubleshooting)
- [Advanced Settings](#advanced-settings)

---

## 🚀 Installation

### System Requirements
- **OS**: Windows 10/11 (64-bit)
- **Python**: 3.11 or higher
- **Webcam**: Any standard webcam
- **RAM**: 4GB minimum, 8GB recommended
- **Lighting**: Normal indoor lighting

### Installation Steps

1. **Install Python 3.11+**
   - Download from [python.org](https://www.python.org/downloads/)
   - ✅ Check "Add Python to PATH" during installation

2. **Open Command Prompt** in the project folder
   ```cmd
   cd C:\xampp\htdocs\eye
   ```

3. **Create Virtual Environment** (recommended)
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

4. **Install Dependencies**
   ```cmd
   pip install -r requirements.txt
   ```

5. **Run the Application**
   ```cmd
   python main.py
   ```

---

## 🎯 First-Time Setup

### 1. Camera Positioning
- Place webcam at **eye level**
- Distance: **50-70 cm** from your face
- Lighting: Face should be **evenly lit** (avoid backlight)
- Room: **Normal indoor lighting** works best

### 2. Initial Launch
1. Run `python main.py`
2. Application window will open
3. Camera feed should appear within 5 seconds
4. **Do NOT start tracking yet** - calibrate first!

### 3. Calibration (IMPORTANT!)
⚠️ **You MUST calibrate before first use**

1. Click **"🎯 Calibrate"** button
2. Follow on-screen instructions
3. Look at each calibration point for 2 seconds
4. Keep head still, move only your eyes
5. Blink normally during calibration
6. Complete all 9 points

**Calibration Tips:**
- Sit in your normal working position
- Good lighting is crucial
- Remove glasses if they cause glare
- Repeat if accuracy is poor

---

## 🎮 Daily Usage

### Starting the System

1. **Launch Application**
   ```cmd
   python main.py
   ```

2. **Check Camera Feed**
   - Your face should be visible
   - Green overlay indicates face detection

3. **Click "▶️ Start Tracking"**
   - Cursor overlay will appear
   - Your eyes now control the cursor

4. **Use Facial Gestures** to interact
   - See [Gesture Controls](#gesture-controls) below

### Stopping the System

- Click **"⏸️ Stop"** button
- Or press **ESC** for emergency stop
- Or close the application window

---

## 😊 Gesture Controls

### Default Gesture Mapping

| Gesture | Action | How to Perform |
|---------|--------|----------------|
| **Blink Both (Short)** | Left Click | Quick blink with both eyes |
| **Blink Both (Long)** | Right Click | Hold eyes closed for 0.5s |
| **Blink Left** | Back | Quick left eye wink |
| **Blink Right** | Forward | Quick right eye wink |
| **Eyebrow Raise** | Scroll Up | Raise eyebrows |
| **Eyebrow Lower** | Scroll Down | Lower eyebrows (squint) |
| **Smile** | Enter/Confirm | Big smile |
| **Jaw Open** | Toggle Keyboard | Open mouth |

### Gesture Tips

**For Accurate Detection:**
- Perform gestures **deliberately**
- Wait 200ms between gestures (cooldown)
- Keep face in camera view
- Good lighting helps recognition

**Single Eye Blinks:**
- Ensure other eye stays open
- Practice a few times to get timing right
- Adjust sensitivity in settings if needed

**Expressions:**
- Be **expressive** - exaggerate slightly
- Smile fully to trigger smile action
- Open jaw wide for jaw detection

---

## 🔧 Troubleshooting

### Camera Issues

**Camera not detected:**
- Check if camera is connected
- Close other apps using camera (Zoom, Skype, etc.)
- Try different `device_id` in `config.yaml`
- Restart application

**Poor video quality:**
- Clean camera lens
- Improve lighting
- Adjust camera angle

### Tracking Issues

**Face not detected:**
- Ensure face is in camera view
- Improve lighting (face should be lit)
- Remove sunglasses
- Keep 50-70cm distance

**Cursor is jittery:**
- Recalibrate
- Increase smoothing in settings
- Check lighting (avoid flickering lights)
- Ensure stable seating position

**Cursor doesn't move smoothly:**
- Lower `smoothing_factor` (0.2-0.4 works best)
- Enable Kalman filter
- Reduce `dead_zone_radius`

**Accidental clicks:**
- Increase `blink_cooldown_ms`
- Adjust `blink_threshold` (higher = less sensitive)
- Enable safety features

### Expression Issues

**Blinks not detected:**
- Lower `blink_threshold` (more sensitive)
- Ensure good lighting on eyes
- Wait for baseline calibration (30 frames)
- Try blinking more deliberately

**False detections:**
- Increase `blink_threshold`
- Increase `blink_cooldown_ms`
- Check lighting (avoid shadows)

---

## ⚙️ Advanced Settings

### Configuration File: `config.yaml`

**Camera Settings:**
```yaml
camera:
  device_id: 0      # 0 = default webcam, 1 = second camera
  width: 640        # Higher = better quality, slower
  height: 480
  fps: 30          # 30 is recommended
```

**Gaze Tracking:**
```yaml
gaze:
  smoothing_factor: 0.3    # 0.2-0.4 recommended
  use_kalman: true         # Better smoothing
  dead_zone_radius: 15     # Pixels, prevents micro-jitter
  acceleration_curve: 1.5  # Speed at screen edges
```

**Expression Detection:**
```yaml
expressions:
  blink_threshold: 0.2     # Lower = more sensitive
  blink_cooldown_ms: 200   # Minimum time between blinks
  long_blink_ms: 500       # Duration for long blink
```

**Safety:**
```yaml
safety:
  max_clicks_per_second: 3         # Prevent rapid clicking
  auto_pause_no_face_ms: 2000     # Auto-pause if face lost
```

**UI:**
```yaml
ui:
  show_overlay: true      # Cursor overlay
  overlay_color: "#00FF88"  # Neon green
  show_fps: true          # FPS counter
  show_debug: false       # Debug info (advanced)
```

### Keyboard Shortcuts

- **ESC** - Emergency stop
- **Ctrl+C** - Quick calibration
- **Alt+F4** - Close application

---

## 💡 Pro Tips

### For Best Accuracy:
1. **Calibrate regularly** (once per session)
2. **Consistent setup** (same position, lighting)
3. **Take breaks** (every 30 minutes)
4. **Adjust settings** to your preference

### For Comfort:
1. Reduce **cursor speed** if too fast
2. Increase **dead zone** for stability
3. Enable **auto-pause** when looking away
4. Use **keyboard shortcuts** for quick actions

### For Performance:
1. Close unnecessary applications
2. Ensure good lighting (reduces processing)
3. Lower camera resolution if laggy
4. Enable GPU acceleration (future update)

---

## 🆘 Getting Help

**Application not working?**
1. Check `logs/` folder for error messages
2. Verify all dependencies installed: `pip list`
3. Try with default `config.yaml`
4. Restart your computer

**Need more assistance?**
- Check logs in `logs/eye_control_*.log`
- Review error messages in console
- Ensure Python 3.11+ is installed
- Verify webcam works in other apps

---

## 📝 Notes

- **Privacy**: All processing is local, no data is sent online
- **Accessibility**: Designed for assistive technology use
- **Performance**: Target <20ms latency, typically achieves 15-18ms
- **Compatibility**: Works with most standard webcams

---

**Version**: 1.0.0  
**Last Updated**: January 2026

*For detailed gesture mapping, see `GESTURE_MAP.md`*
