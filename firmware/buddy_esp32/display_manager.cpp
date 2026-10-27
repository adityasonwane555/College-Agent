/*
 * =====================================================================================
 * BUDDY AI — ST7789 Display Manager Implementation
 * Exact Visual Mirror of Browser Kiosk Robot Face
 * Features:
 *   - Pure OLED-Black Visor Canvas
 *   - Electric Cyan Capsule Eyes with Dual Pupil Specular Glints
 *   - Smooth Natural Periodic Blinking
 *   - Blushing Cheek LEDs
 *   - 7-Bar Dynamic Dancing Audio Waveform (LISTENING)
 *   - Animated Oscillating Talking Mouth (SPEAKING)
 *   - Celestial Glowing Halo Ring & Contemplative Upward Gaze (THINKING)
 *   - Arched Crescent Smiling Eyes (HAPPY)
 * =====================================================================================
 */

#include "display_manager.h"
#include <math.h>

// Exact Color Palette matching frontend robot.css (RGB565 format)
#define COLOR_BG          0x0000  // Pure pitch black visor
#define COLOR_CYAN        0x07FF  // Electric cyan (#00f0ff - IDLE & LISTENING)
#define COLOR_SKYBLUE     0x3DFE  // Bright sky blue (#38bdf8 - HAPPY)
#define COLOR_VIOLET      0xC43F  // Celestial violet/purple (#c084fc - THINKING)
#define COLOR_MAGENTA     0xF81F  // Speaking magenta (#f43f5e / #e879f9)
#define COLOR_CORAL       0xFA08  // Error rose/coral (#f87171)
#define COLOR_WHITE       0xFFFF  // Pure specular reflection glint
#define COLOR_CHEEK_IDLE  0x8186  // Subtle soft blush (#f43f5e 30%)
#define COLOR_CHEEK_HAPPY 0xF990  // Glowing cheerful blush (#f43f5e 90%)

DisplayManager displayManager;

DisplayManager::DisplayManager()
  : _tft(PIN_TFT_CS, PIN_TFT_DC, PIN_TFT_MOSI, PIN_TFT_SCLK, PIN_TFT_RST),
    _currentState(STATE_BOOTING),
    _lastAnimUpdate(0),
    _stateStartTime(0),
    _ssid(""),
    _ip(""),
    _messageTitle(""),
    _messageBody(""),
    _audioLevel(0.0f),
    _nextBlinkTime(2500),
    _isBlinking(false),
    _blinkStartTime(0),
    _blinkDuration(170),
    _nextGazeTime(3000),
    _targetGazeX(0),
    _targetGazeY(0),
    _currentGazeX(0),
    _currentGazeY(0),
    _forceFullClear(true),
    _hadHalo(false) {}

void DisplayManager::begin() {
  if (PIN_TFT_BLK >= 0) {
    pinMode(PIN_TFT_BLK, OUTPUT);
    digitalWrite(PIN_TFT_BLK, HIGH); // Backlight ON
  }

  _tft.init(TFT_WIDTH, TFT_HEIGHT);
  _tft.setRotation(TFT_ROTATION);
  _tft.fillScreen(COLOR_BG);

  _stateStartTime = millis();
  _nextBlinkTime = _stateStartTime + 2000;
  _nextGazeTime = _stateStartTime + 3000;
  _forceFullClear = true;
  _hadHalo = false;

  LOG_PRINTLN("[Display] ST7789 initialized: 1-to-1 Web Kiosk Robot Face active.");
}

void DisplayManager::setState(BuddyState state) {
  if (_currentState != state) {
    _currentState = state;
    _stateStartTime = millis();
    _forceFullClear = true; // Clean reset on state change
  }
}

void DisplayManager::setWifiInfo(const String& ssid, const String& ip) {
  _ssid = ssid;
  _ip = ip;
}

void DisplayManager::setMessage(const String& title, const String& body) {
  _messageTitle = title;
  _messageBody = body;
}

void DisplayManager::setAudioLevel(float level) {
  _audioLevel = constrain(level, 0.0f, 1.0f);
}

void DisplayManager::drawEyeCapsule(int cx, int cy, int w, int h, int r, uint16_t color, int gazeX, int gazeY) {
  if (w <= 0 || h <= 0) return;

  r = min(r, min(w / 2, h / 2));
  int x = cx - w / 2;
  int y = cy - h / 2;

  // Main glowing eye capsule
  _tft.fillRoundRect(x, y, w, h, r, color);

  // When open (>16px), draw the dual white pupil specular glints
  if (h > 18) {
    int glintX = cx - 9 + gazeX;
    int glintY = cy - h / 4 + gazeY;

    // Primary bright white reflection highlight (r=4)
    _tft.fillCircle(glintX, glintY, 4, COLOR_WHITE);

    // Secondary cute mini-glint (r=2)
    if (h > 32) {
      _tft.fillCircle(glintX + 8, glintY + 9, 2, COLOR_WHITE);
    }
  }
}

void DisplayManager::drawSmilingEye(int cx, int cy, int w, int h, uint16_t color) {
  // Arched crescent smiling eyes (^_^) matching .robot-head-wrapper.happy .robot-eye
  int r = w / 2;
  int topY = cy - 4;

  // Draw thick upward curved arc
  for (int t = 0; t < 6; t++) {
    _tft.drawCircle(cx, topY + r + t, r, color);
  }
  // Mask out lower half with pure black
  _tft.fillRect(cx - r - 4, topY + r, w + 8, r + 12, COLOR_BG);
}

void DisplayManager::drawWaveformBars(int cx, int cy, unsigned long now) {
  // 7 animated dancing audio waveform bars matching .waveform-bars in robot.css
  const int numBars = 7;
  const int barWidth = 4;
  const int gap = 4;
  const int totalW = (numBars * barWidth) + ((numBars - 1) * gap); // 52px
  int startX = cx - totalW / 2;

  float t = (float)now * 0.008f;
  float levels[7] = {
    8.0f  + sinf(t * 1.5f + 0.2f) * 5.0f  + _audioLevel * 10.0f,
    18.0f + sinf(t * 1.8f + 0.8f) * 9.0f  + _audioLevel * 18.0f,
    13.0f + sinf(t * 1.2f + 1.5f) * 7.0f  + _audioLevel * 14.0f,
    24.0f + sinf(t * 2.1f + 2.3f) * 11.0f + _audioLevel * 22.0f,
    12.0f + sinf(t * 1.4f + 3.1f) * 6.0f  + _audioLevel * 14.0f,
    17.0f + sinf(t * 1.9f + 3.9f) * 8.0f  + _audioLevel * 17.0f,
    7.0f  + sinf(t * 1.3f + 4.6f) * 4.0f  + _audioLevel * 8.0f
  };

  for (int i = 0; i < numBars; i++) {
    int h = constrain((int)levels[i], 4, 30);
    int bx = startX + i * (barWidth + gap);
    _tft.fillRoundRect(bx, cy - h / 2, barWidth, h, 2, COLOR_CYAN);
  }
}

void DisplayManager::drawThinkingHalo(int cx, int cy, unsigned long now) {
  // Celestial halo ring matching .thinking-halo in robot.css
  int haloW = 92;
  int haloH = 14;
  int hx = cx - haloW / 2;
  int hy = cy - haloH / 2;

  // Outer glowing violet oval
  _tft.fillRoundRect(hx, hy, haloW, haloH, 7, COLOR_VIOLET);
  // Inner black cut-out to form hollow glowing ring
  _tft.fillRoundRect(hx + 3, hy + 3, haloW - 6, haloH - 6, 5, COLOR_BG);

  // Orbiting celestial glint sparkle
  float angle = (float)now * 0.005f;
  int glintX = cx + (int)(cosf(angle) * (haloW / 2 - 8));
  int glintY = cy + (int)(sinf(angle) * (haloH / 2 - 4));
  _tft.fillCircle(glintX, glintY, 2, COLOR_WHITE);
}

void DisplayManager::drawFaceFrame(unsigned long now) {
  int screenW = _tft.width();
  int screenH = _tft.height();
  int cx = screenW / 2;               // 120
  int eyeY = (screenH * 40) / 100;    // 128
  int cheekY = eyeY + 48;             // 176
  int mouthY = (screenH * 72) / 100;  // 230
  int eyeSpacing = 48;                // Center-to-eye distance

  // Base eye dimensions (52x70px capsule matching 58x72px in web CSS)
  int baseW = 52;
  int baseH = 70;
  int baseR = 26;

  // Color theme matching exact CSS states
  uint16_t faceColor = COLOR_CYAN;
  switch (_currentState) {
    case STATE_BOOTING:   faceColor = COLOR_SKYBLUE;  break;
    case STATE_IDLE:      faceColor = COLOR_CYAN;     break;
    case STATE_LISTENING: faceColor = COLOR_CYAN;     break;
    case STATE_THINKING:  faceColor = COLOR_VIOLET;   break;
    case STATE_SPEAKING:  faceColor = COLOR_MAGENTA;  break;
    case STATE_ERROR:     faceColor = COLOR_CORAL;    break;
    default:              faceColor = COLOR_CYAN;     break;
  }

  // Full clean reset on state transitions
  if (_forceFullClear) {
    _tft.fillScreen(COLOR_BG);
    _forceFullClear = false;
  }

  // 1. Thinking Halo Management
  int haloY = 32;
  if (_currentState == STATE_THINKING) {
    _tft.fillRect(cx - 50, haloY - 10, 100, 22, COLOR_BG);
    drawThinkingHalo(cx, haloY, now);
    _hadHalo = true;
  } else if (_hadHalo) {
    // Clear halo area once after leaving THINKING state
    _tft.fillRect(cx - 50, haloY - 10, 100, 22, COLOR_BG);
    _hadHalo = false;
  }

  // 2. Natural Blinking Animation
  if (!_isBlinking && now >= _nextBlinkTime) {
    _isBlinking = true;
    _blinkStartTime = now;
    _blinkDuration = 170;
  }

  int eyeH = baseH;
  if (_isBlinking) {
    unsigned long blinkElapsed = now - _blinkStartTime;
    if (blinkElapsed >= (unsigned long)_blinkDuration) {
      _isBlinking = false;
      eyeH = baseH;
      _nextBlinkTime = now + 2800 + random(0, 3000); // Next blink in 2.8 - 5.8s
    } else {
      float p = (float)blinkElapsed / (float)_blinkDuration;
      float curve = fabsf(p - 0.5f) * 2.0f; // 1.0 -> 0.0 -> 1.0
      eyeH = 6 + (int)((baseH - 6) * curve);
    }
  }

  // 3. Eye Gaze & Saccades
  int currentEyeY = eyeY;
  if (_currentState == STATE_THINKING) {
    // Look upward towards the thinking halo ring
    _targetGazeY = -8;
    _targetGazeX = (int)(sinf((float)now * 0.003f) * 6.0f);
    currentEyeY -= 6; // Move entire eye assembly up slightly
  } else if (_currentState == STATE_LISTENING) {
    _targetGazeX = 0;
    _targetGazeY = 0;
    eyeH = min(78, eyeH + 4); // Attentive wider eyes
  } else {
    // Natural periodic glance in IDLE
    if (now >= _nextGazeTime) {
      int roll = random(0, 100);
      if (roll < 45) {
        _targetGazeX = 0;
        _targetGazeY = 0;
      } else if (roll < 75) {
        _targetGazeX = random(0, 2) ? 6 : -6;
        _targetGazeY = 0;
      } else {
        _targetGazeX = random(-4, 5);
        _targetGazeY = random(-3, 4);
      }
      _nextGazeTime = now + 2600 + random(0, 3200);
    }
  }

  // Soft easing
  _currentGazeX += (_targetGazeX - _currentGazeX) * 0.3f;
  _currentGazeY += (_targetGazeY - _currentGazeY) * 0.3f;

  // 4. Differential Flicker-Free Clearing
  // Clear eye & cheek region (160 x 115 px)
  _tft.fillRect(cx - 80, eyeY - 44, 160, 120, COLOR_BG);
  // Clear mouth / waveform region (80 x 44 px)
  _tft.fillRect(cx - 40, mouthY - 22, 80, 44, COLOR_BG);

  // 5. Draw Eyes
  int leftEyeX = cx - eyeSpacing;
  int rightEyeX = cx + eyeSpacing;

  if (_currentState == STATE_BOOTING || (_currentState == STATE_IDLE && _messageTitle == "happy")) {
    drawSmilingEye(leftEyeX, currentEyeY, baseW, baseH, faceColor);
    drawSmilingEye(rightEyeX, currentEyeY, baseW, baseH, faceColor);
  } else {
    int r = (eyeH <= 12) ? (eyeH / 2) : baseR;
    drawEyeCapsule(leftEyeX, currentEyeY, baseW, eyeH, r, faceColor, _currentGazeX, _currentGazeY);
    drawEyeCapsule(rightEyeX, currentEyeY, baseW, eyeH, r, faceColor, _currentGazeX, _currentGazeY);
  }

  // 6. Draw Blushing Cheek LEDs (matching .robot-cheek in robot.css)
  uint16_t cheekColor = (_currentState == STATE_BOOTING) ? COLOR_CHEEK_HAPPY : COLOR_CHEEK_IDLE;
  int cheekW = 20;
  int cheekH = 9;
  _tft.fillRoundRect(cx - 58 - cheekW / 2, cheekY - cheekH / 2, cheekW, cheekH, 4, cheekColor);
  _tft.fillRoundRect(cx + 58 - cheekW / 2, cheekY - cheekH / 2, cheekW, cheekH, 4, cheekColor);

  // 7. Draw Mouth or Listening Waveform
  unsigned long elapsed = now - _stateStartTime;

  if (_currentState == STATE_LISTENING) {
    // Exact match for <ListeningWaveform /> in React!
    drawWaveformBars(cx, mouthY, now);
  }
  else if (_currentState == STATE_SPEAKING) {
    // Exact match for @keyframes speaking-mouth in robot.css
    float osc = 0.5f + 0.5f * sinf((float)elapsed * 0.022f);
    int mouthH = 8 + (int)(16.0f * osc);
    if (_audioLevel > 0.05f) {
      mouthH = 8 + (int)(_audioLevel * 28.0f);
    }
    mouthH = constrain(mouthH, 8, 30);
    int mouthW = 34 + (int)(12.0f * osc);

    _tft.fillRoundRect(cx - mouthW / 2, mouthY - mouthH / 2, mouthW, mouthH, mouthH / 2, COLOR_MAGENTA);
    if (mouthH > 14) {
      int inW = mouthW - 10;
      int inH = mouthH - 6;
      _tft.fillRoundRect(cx - inW / 2, mouthY - inH / 2, inW, inH, inH / 2, COLOR_BG);
    }
  }
  else if (_currentState == STATE_THINKING) {
    // Cute small thinking line (matching .robot-head-wrapper.thinking .robot-mouth-line)
    _tft.fillRoundRect(cx - 12, mouthY - 3, 24, 6, 3, COLOR_VIOLET);
  }
  else if (_currentState == STATE_ERROR) {
    // Sympathetic error mouth
    for (int t = 0; t < 3; t++) {
      _tft.drawCircle(cx, mouthY + 18 + t, 18, COLOR_CORAL);
    }
    _tft.fillRect(cx - 22, mouthY + 14, 44, 25, COLOR_BG);
  }
  else {
    // IDLE: Friendly rounded mouth line (matching .robot-mouth-line: 44px x 8px)
    _tft.fillRoundRect(cx - 22, mouthY - 4, 44, 8, 4, COLOR_CYAN);
  }
}

void DisplayManager::update() {
  unsigned long now = millis();
  // Butter-smooth 33 FPS animation loop (every 30ms)
  if (now - _lastAnimUpdate < 30) {
    return;
  }
  _lastAnimUpdate = now;

  drawFaceFrame(now);
}
