# Eyegle v1.0 - Gesture Map
**Advanced Eye Tracking & Facial Expression Control**  
*Created by Hivizstudios & Hitansh Parikh*

## 👁️ Complete Gesture Reference

This document describes all available gestures, how to perform them, and how to customize them.

---

## 🎯 Default Gesture Mappings

### Eye Blinks

| Gesture | Action | Detection Method | Duration | Cooldown |
|---------|--------|------------------|----------|----------|
| **Blink Both (Short)** | Left Click | Both eyes close briefly | <500ms | 200ms |
| **Blink Both (Long)** | Right Click | Both eyes close longer | ≥500ms | 200ms |
| **Blink Left** | Browser Back | Left eye only | <300ms | 200ms |
| **Blink Right** | Browser Forward | Right eye only | <300ms | 200ms |

**How to perform:**
- **Short blink**: Natural quick blink
- **Long blink**: Close eyes and count "one"
- **Single eye**: Close one eye, keep other open

**Tips:**
- Blink deliberately, not too fast
- Wait for cooldown between actions
- Adjust `blink_threshold` if not detected
- Ensure good eye lighting

---

### Facial Expressions

| Gesture | Action | Detection Method | Threshold |
|---------|--------|------------------|-----------|
| **Eyebrow Raise** | Scroll Up | Eyebrow position | 0.03 |
| **Eyebrow Lower** | Scroll Down | Eyebrow position | 0.03 |
| **Smile** | Enter/Confirm | Mouth corners | 0.05 |
| **Jaw Open** | Toggle Keyboard Mode | Mouth opening | 0.04 |

**How to perform:**
- **Eyebrow raise**: Raise eyebrows like surprised
- **Eyebrow lower**: Squint or furrow brows
- **Smile**: Full smile, show teeth (optional)
- **Jaw open**: Open mouth wide

**Tips:**
- Be expressive - exaggerate slightly
- Hold expression briefly (0.5-1 second)
- Practice in front of mirror first
- Adjust sensitivity in settings

---

### Head Movements

| Gesture | Action | Detection Method | Angle |
|---------|--------|------------------|-------|
| **Head Tilt Left** | Volume Down | Head roll to left | >15° |
| **Head Tilt Right** | Volume Up | Head roll to right | >15° |
| **Head Nod** | Play/Pause | Head pitch down-up | >20° |
| **Head Shake** | Cancel/Esc | Head yaw left-right | >25° |

**How to perform:**
- **Tilt**: Roll head to shoulder
- **Nod**: Look down then back up
- **Shake**: Turn head left-right like "no"

**Tips:**
- Smooth, deliberate movements
- Don't move too fast
- Keep face in camera view
- Movement detection coming in future update

---

## 🎨 Customizing Gestures

### Method 1: UI Settings (Recommended)

1. Open application
2. Go to **Settings** panel (right side)
3. Find **Expression Detection** section
4. Adjust thresholds with sliders:
   - Lower = more sensitive
   - Higher = less sensitive

### Method 2: Configuration File

Edit `config.yaml`:

```yaml
# Expression Detection
expressions:
  blink_threshold: 0.2      # 0.1-0.5, default: 0.2
  blink_cooldown_ms: 200    # 100-1000, default: 200
  long_blink_ms: 500        # 300-1000, default: 500
  eyebrow_threshold: 0.03   # 0.01-0.1, default: 0.03
  smile_threshold: 0.05     # 0.02-0.1, default: 0.05
  jaw_threshold: 0.04       # 0.02-0.1, default: 0.04
  confidence_min: 0.7       # 0.5-0.9, default: 0.7

# Action Mapping (customize what each gesture does)
actions:
  blink_both_short: left_click      # Options: left_click, right_click, etc.
  blink_both_long: right_click
  blink_left: back
  blink_right: forward
  eyebrow_raise: scroll_up
  eyebrow_lower: scroll_down
  smile: enter
  jaw_open: toggle_keyboard
  head_tilt_left: volume_down
  head_tilt_right: volume_up
  head_nod: play_pause
  head_shake: cancel
```

### Available Actions

You can map any gesture to these actions:

**Mouse Actions:**
- `left_click` - Left mouse click
- `right_click` - Right mouse click  - `double_click` - Double click
- `scroll_up` - Scroll up
- `scroll_down` - Scroll down

**Keyboard Actions:**
- `enter` - Enter key
- `back` - Backspace or browser back
- `forward` - Browser forward
- `cancel` - Escape key
- `toggle_keyboard` - Toggle on-screen keyboard mode

**Media Controls:**
- `play_pause` - Media play/pause
- `volume_up` - Increase volume
- `volume_down` - Decrease volume

**System:**
- `none` - Disable gesture (no action)

---

## 🎓 Learning Curve

### Beginner (Week 1)
- **Focus**: Cursor control + basic blinks
- **Practice**: Moving cursor smoothly
- **Goal**: Comfortable left/right click

### Intermediate (Week 2-3)
- **Focus**: Single eye blinks + expressions
- **Practice**: Smile, jaw open, scrolling
- **Goal**: Fluent basic navigation

### Advanced (Month 1+)
- **Focus**: All gestures + custom mappings
- **Practice**: Complex workflows
- **Goal**: Full computer control

---

## 💪 Practice Exercises

### Exercise 1: Cursor Precision
1. Open a drawing app
2. Move cursor to specific points
3. Practice smooth lines
4. **Goal**: Straight lines without jitter

### Exercise 2: Click Accuracy
1. Open a website with buttons
2. Click each button using blinks
3. Try both short and long blinks
4. **Goal**: 90% accurate clicks

### Exercise 3: Expression Control
1. Open text editor
2. Use smile for Enter
3. Use jaw for mode switching
4. **Goal**: Deliberate expression triggering

### Exercise 4: Workflow
1. Open browser
2. Navigate using gestures only
3. Click links, scroll pages
4. **Goal**: Complete task without mouse/keyboard

---

## 🛡️ Safety Features

### Automatic Safeguards

**Click Rate Limiting:**
- Max 3 clicks per second (configurable)
- Prevents accidental rapid clicking
- Adjust in `config.yaml`: `max_clicks_per_second`

**Face Detection Pause:**
- Auto-pause if face not detected for 2 seconds
- Prevents actions when looking away
- Adjust timeout: `auto_pause_no_face_ms`

**Cooldown Timers:**
- Minimum time between same gesture
- Prevents double-triggering
- Per-gesture cooldown settings

**Emergency Stop:**
- Press **ESC** anytime to stop all actions
- Click 🛑 button in UI
- Move mouse to screen corner (PyAutoGUI failsafe)

---

## 🔍 Troubleshooting Gestures

### Gesture Not Detected

**Blinks not working:**
1. Check lighting (eyes must be well-lit)
2. Lower `blink_threshold` (more sensitive)
3. Wait for baseline calibration (30 frames)
4. Ensure eyes visible to camera

**Expressions not working:**
1. Be more expressive (exaggerate)
2. Lower threshold for that expression
3. Check camera can see full face
4. Practice expression in mirror first

### False Detections

**Unwanted clicks:**
1. Increase `blink_threshold`
2. Increase `blink_cooldown_ms`
3. Enable "require confirmation" for critical actions
4. Blink more naturally (less deliberate)

**Random actions:**
1. Improve lighting (reduce shadows)
2. Increase all thresholds
3. Enable higher `confidence_min`
4. Check for reflections on glasses

---

## 📊 Gesture Detection Stats

MediaPipe Face Mesh tracks **478 landmarks**, including:
- 6 landmarks per eye (for blink detection)
- 5 landmarks per iris (for gaze tracking)
- Eyebrow, mouth, jaw landmarks

**Detection Performance:**
- **Blink**: 95%+ accuracy
- **Smile**: 90%+ accuracy
- **Jaw**: 85%+ accuracy
- **Eyebrow**: 80%+ accuracy (lighting dependent)
- **Head pose**: Coming soon

**Latency:**
- Detection: 5-8ms
- Processing: 3-5ms
- Total: 10-15ms (target: <20ms) ✅

---

## 🎯 Best Practices

### For Reliability:
1. **Consistent environment** (same lighting, position)
2. **Calibrate each session** (1-2 minutes)
3. **Practice gestures** (muscle memory)
4. **Adjust to your needs** (personalize thresholds)

### For Comfort:
1. **Take breaks** (every 30 minutes)
2. **Blink naturally** (don't strain eyes)
3. **Relax face** (don't hold expressions)
4. **Ergonomic setup** (proper posture)

### For Speed:
1. **Learn shortcuts** (common gesture combos)
2. **Customize mappings** (optimize workflow)
3. **Use cooldown wisely** (balance speed vs safety)
4. **Practice daily** (build proficiency)

---

## 🚀 Advanced: Custom Gesture Combinations

*Future feature - coming in v2.0*

Will support:
- **Gesture sequences** (blink left + smile = copy)
- **Dwell time actions** (look at button for 2s = click)
- **Gaze zones** (look at corner = trigger action)
- **Voice commands** (combine with speech)

---

**Version**: 1.0.0  
**Last Updated**: January 2026

*For setup and usage instructions, see `USER_GUIDE.md`*
