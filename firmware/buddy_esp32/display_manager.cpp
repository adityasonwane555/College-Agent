/*
 * =====================================================================================
 * BUDDY AI — ST7789 Display Manager Implementation
 * Exact Visual Mirror of Browser Kiosk Robot Face
 * 
 * Hardware & Performance Upgrades:
 *   - 40 MHz Hardware SPI Bus on ESP32-S3 (25x faster than bit-banged software SPI)
 *   - Off-screen Micro-Canvas Double Buffering (RAM to Screen, ZERO flicker, ZERO tearing)
 *   - Independent Zonal Rendering: Only eyes update during blinks!
 *   - Cheeks and mouth remain static and glowing, completely unaffected by blinks.
 *   - Eliminates scanline artifact ("line going from top to bottom").
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
  : _tft(&SPI, PIN_TFT_CS, PIN_TFT_DC, PIN_TFT_RST),
    _eyeCanvas(nullptr),
    _mouthCanvas(nullptr),
    _haloCanvas(nullptr),
    _currentState(STATE_BOOTING),
    _lastDrawnState(STATE_BOOTING),
    _lastAnimUpdate(0),
    _stateStartTime(0),
    _ssid(""),
    _ip(""),
    _messageTitle(""),
    _messageBody(""),
    _lastMessageTitle(""),
    _audioLevel(0.0f),
    _nextBlinkTime(2500),
    _isBlinking(false),
    _blinkStartTime(0),
    _blinkDuration(170),
    _lastEyeH(-1),
    _nextGazeTime(3000),
    _targetGazeX(0),
    _targetGazeY(0),
    _currentGazeX(0.0f),
    _currentGazeY(0.0f),
    _lastGazeX(-99),
    _lastGazeY(-99),
    _lastEyeY(-1),
    _forceFullClear(false),
    _hadHalo(false),
    _mouthAnimated(false),
    _mouthStateDrawn((BuddyState)-1) {}

DisplayManager::~DisplayManager() {
  if (_eyeCanvas)   { delete _eyeCanvas;   _eyeCanvas = nullptr; }
  if (_mouthCanvas) { delete _mouthCanvas; _mouthCanvas = nullptr; }
  if (_haloCanvas)  { delete _haloCanvas;  _haloCanvas = nullptr; }
}

void DisplayManager::begin() {
  if (PIN_TFT_BLK >= 0) {
    pinMode(PIN_TFT_BLK, OUTPUT);
    digitalWrite(PIN_TFT_BLK, HIGH); // Backlight ON
  }

  // 1. Initialize Hardware SPI bus with ESP32-S3 pins
  // SCLK=12, MISO=-1, MOSI=11, SS=-1 (CS managed by Adafruit_SPITFT)
  SPI.begin(PIN_TFT_SCLK, -1, PIN_TFT_MOSI, -1);

  // 2. Initialize ST7789 display controller
  _tft.init(TFT_WIDTH, TFT_HEIGHT);
  _tft.setRotation(TFT_ROTATION);
  _tft.setSPISpeed(40000000); // 40 MHz high-speed Hardware SPI!
  _tft.invertDisplay(TFT_INVERT_COLORS); // Fix inverted colors: forces ST77XX_INVOFF so 0x0000 is pure pitch black!

  // 3. Allocate off-screen micro-canvases in RAM for flicker-free double buffering
  if (!_eyeCanvas) {
    _eyeCanvas = new GFXcanvas16(EYE_CANVAS_W, EYE_CANVAS_H);
  }
  if (!_mouthCanvas) {
    _mouthCanvas = new GFXcanvas16(MOUTH_CANVAS_W, MOUTH_CANVAS_H);
  }
  if (!_haloCanvas) {
    _haloCanvas = new GFXcanvas16(HALO_CANVAS_W, HALO_CANVAS_H);
  }

  // 4. Initial screen clear & draw static cheeks
  _tft.fillScreen(COLOR_BG);
  drawStaticFace();

  _stateStartTime = millis();
  _nextBlinkTime = _stateStartTime + 2000;
  _nextGazeTime = _stateStartTime + 3000;
  _forceFullClear = false;
  _hadHalo = false;
  _lastEyeH = -1;
  _mouthStateDrawn = (BuddyState)-1;

  LOG_PRINTLN("[Display] ST7789 Hardware SPI @ 40MHz initialized: Flicker-free Dual-Buffer Active.");
}

void DisplayManager::setState(BuddyState state) {
  if (_currentState != state) {
    _currentState = state;
    _stateStartTime = millis();
    _lastEyeH = -1; // Force immediate eye redraw with new state color
    _lastAnimUpdate = 0; // Force immediate redraw on the very next update() call
    _mouthStateDrawn = (BuddyState)-1; // Force immediate mouth redraw on state change
  }
}

void DisplayManager::setWifiInfo(const String& ssid, const String& ip) {
  _ssid = ssid;
  _ip = ip;
}

void DisplayManager::setMessage(const String& title, const String& body) {
  if (_messageTitle != title || _messageBody != body) {
    _messageTitle = title;
    _messageBody = body;
    _forceFullClear = true;
  }
}

void DisplayManager::setAudioLevel(float level) {
  _audioLevel = constrain(level, 0.0f, 1.0f);
}

void DisplayManager::drawEyeCapsule(Adafruit_GFX* gfx, int cx, int cy, int w, int h, int r, uint16_t color, int gazeX, int gazeY) {
  if (!gfx || w <= 0 || h <= 0) return;

  r = min(r, min(w / 2, h / 2));
  int x = cx - w / 2;
  int y = cy - h / 2;

  // Main glowing eye capsule
  gfx->fillRoundRect(x, y, w, h, r, color);

  // When open (>18px), draw the dual white pupil specular glints
  if (h > 18) {
    int glintX = cx - 9 + gazeX;
    int glintY = cy - h / 4 + gazeY;

    // Primary bright white reflection highlight (r=4)
    gfx->fillCircle(glintX, glintY, 4, COLOR_WHITE);

    // Secondary cute mini-glint (r=2)
    if (h > 32) {
      gfx->fillCircle(glintX + 8, glintY + 9, 2, COLOR_WHITE);
    }
  }
}

void DisplayManager::drawSmilingEye(Adafruit_GFX* gfx, int cx, int cy, int w, int h, uint16_t color) {
  if (!gfx) return;
  int r = w / 2;
  int topY = cy - 4;

  // Draw thick upward curved arc
  for (int t = 0; t < 6; t++) {
    gfx->drawCircle(cx, topY + r + t, r, color);
  }
  // Mask out lower half with pure black
  gfx->fillRect(cx - r - 4, topY + r, w + 8, r + 12, COLOR_BG);
}

void DisplayManager::drawWaveformBars(Adafruit_GFX* gfx, int cx, int cy, unsigned long now) {
  if (!gfx) return;
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
    gfx->fillRoundRect(bx, cy - h / 2, barWidth, h, 2, COLOR_CYAN);
  }
}

void DisplayManager::drawThinkingHalo(Adafruit_GFX* gfx, int cx, int cy, unsigned long now) {
  if (!gfx) return;
  int haloW = 92;
  int haloH = 14;
  int hx = cx - haloW / 2;
  int hy = cy - haloH / 2;

  // Outer glowing violet oval
  gfx->fillRoundRect(hx, hy, haloW, haloH, 7, COLOR_VIOLET);
  // Inner black cut-out to form hollow glowing ring
  gfx->fillRoundRect(hx + 3, hy + 3, haloW - 6, haloH - 6, 5, COLOR_BG);

  // Orbiting celestial glint sparkle
  float angle = (float)now * 0.005f;
  int glintX = cx + (int)(cosf(angle) * (haloW / 2 - 8));
  int glintY = cy + (int)(sinf(angle) * (haloH / 2 - 4));
  gfx->fillCircle(glintX, glintY, 2, COLOR_WHITE);
}

void DisplayManager::drawStaticFace() {
  int screenW = _tft.width();
  int screenH = _tft.height();
  int cx = screenW / 2;               // 120
  int eyeY = (screenH * 40) / 100;    // 128
  int cheekY = eyeY + 48;             // 176

  // 1. Draw Blushing Cheek LEDs (Static, NEVER redrawn during eye blinks!)
  uint16_t cheekColor = (_currentState == STATE_BOOTING) ? COLOR_CHEEK_HAPPY : COLOR_CHEEK_IDLE;
  int cheekW = 20;
  int cheekH = 9;
  _tft.fillRoundRect(cx - 58 - cheekW / 2, cheekY - cheekH / 2, cheekW, cheekH, 4, cheekColor);
  _tft.fillRoundRect(cx + 58 - cheekW / 2, cheekY - cheekH / 2, cheekW, cheekH, 4, cheekColor);
}

void DisplayManager::updateEyes(unsigned long now) {
  int screenW = _tft.width();
  int screenH = _tft.height();
  int cx = screenW / 2;               // 120
  int eyeY = (screenH * 40) / 100;    // 128
  int eyeSpacing = 48;

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

  // 1. Natural Blinking Animation
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

  // 2. Eye Gaze & Saccades
  int currentEyeY = eyeY;
  if (_currentState == STATE_THINKING) {
    // Look upward towards thinking halo
    _targetGazeY = -8;
    _targetGazeX = (int)(sinf((float)now * 0.003f) * 6.0f);
    currentEyeY -= 6; // Move eye assembly up slightly
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
  _currentGazeX += ((float)_targetGazeX - _currentGazeX) * 0.3f;
  _currentGazeY += ((float)_targetGazeY - _currentGazeY) * 0.3f;

  int roundedGazeX = (int)roundf(_currentGazeX);
  int roundedGazeY = (int)roundf(_currentGazeY);

  // Check if eyes actually changed to avoid wasteful redraws
  bool eyesChanged = (eyeH != _lastEyeH) ||
                     (roundedGazeX != _lastGazeX) ||
                     (roundedGazeY != _lastGazeY) ||
                     (currentEyeY != _lastEyeY) ||
                     (_currentState != _lastDrawnState) ||
                     (_messageTitle != _lastMessageTitle);

  if (!eyesChanged) {
    return; // Eyes unchanged — zero SPI traffic, zero flicker!
  }

  _lastEyeH = eyeH;
  _lastGazeX = roundedGazeX;
  _lastGazeY = roundedGazeY;
  _lastEyeY = currentEyeY;

  // Render into off-screen eye micro-canvas (160 x 84 px)
  if (_eyeCanvas) {
    _eyeCanvas->fillScreen(COLOR_BG);

    // Local coordinates inside canvas:
    // Canvas is at (EYE_CANVAS_X = cx - 80 = 40, EYE_CANVAS_Y = eyeY - 42 = 86)
    int localLeftEyeX = (cx - eyeSpacing) - EYE_CANVAS_X;   // 72 - 40 = 32
    int localRightEyeX = (cx + eyeSpacing) - EYE_CANVAS_X; // 168 - 40 = 128
    int localEyeCenterY = currentEyeY - EYE_CANVAS_Y;      // e.g. 128 - 86 = 42

    if (_currentState == STATE_BOOTING || (_currentState == STATE_IDLE && _messageTitle == "happy")) {
      drawSmilingEye(_eyeCanvas, localLeftEyeX, localEyeCenterY, baseW, baseH, faceColor);
      drawSmilingEye(_eyeCanvas, localRightEyeX, localEyeCenterY, baseW, baseH, faceColor);
    } else {
      int r = (eyeH <= 12) ? (eyeH / 2) : baseR;
      drawEyeCapsule(_eyeCanvas, localLeftEyeX, localEyeCenterY, baseW, eyeH, r, faceColor, roundedGazeX, roundedGazeY);
      drawEyeCapsule(_eyeCanvas, localRightEyeX, localEyeCenterY, baseW, eyeH, r, faceColor, roundedGazeX, roundedGazeY);
    }

    // Direct, atomic push over 40MHz Hardware SPI (takes only ~5ms, zero intermediate black clear!)
    _tft.drawRGBBitmap(EYE_CANVAS_X, EYE_CANVAS_Y, _eyeCanvas->getBuffer(), EYE_CANVAS_W, EYE_CANVAS_H);
  }
}

void DisplayManager::updateMouth(unsigned long now) {
  if (!_mouthCanvas) return;

  unsigned long elapsed = now - _stateStartTime;

  if (_currentState == STATE_LISTENING) {
    _mouthAnimated = true;
    _mouthCanvas->fillScreen(COLOR_BG);
    drawWaveformBars(_mouthCanvas, MOUTH_CANVAS_W / 2, MOUTH_CANVAS_H / 2, now);
    _tft.drawRGBBitmap(MOUTH_CANVAS_X, MOUTH_CANVAS_Y, _mouthCanvas->getBuffer(), MOUTH_CANVAS_W, MOUTH_CANVAS_H);
  } else if (_currentState == STATE_SPEAKING) {
    _mouthAnimated = true;
    _mouthCanvas->fillScreen(COLOR_BG);
    float osc = 0.5f + 0.5f * sinf((float)elapsed * 0.022f);
    int mouthH = 8 + (int)(16.0f * osc);
    if (_audioLevel > 0.05f) {
      mouthH = 8 + (int)(_audioLevel * 28.0f);
    }
    mouthH = constrain(mouthH, 8, 30);
    int mouthW = 34 + (int)(12.0f * osc);

    int localCx = MOUTH_CANVAS_W / 2;
    int localCy = MOUTH_CANVAS_H / 2;
    _mouthCanvas->fillRoundRect(localCx - mouthW / 2, localCy - mouthH / 2, mouthW, mouthH, mouthH / 2, COLOR_MAGENTA);
    if (mouthH > 14) {
      int inW = mouthW - 10;
      int inH = mouthH - 6;
      _mouthCanvas->fillRoundRect(localCx - inW / 2, localCy - inH / 2, inW, inH, inH / 2, COLOR_BG);
    }
    _tft.drawRGBBitmap(MOUTH_CANVAS_X, MOUTH_CANVAS_Y, _mouthCanvas->getBuffer(), MOUTH_CANVAS_W, MOUTH_CANVAS_H);
  } else {
    // Non-animated states (IDLE, THINKING, ERROR, BOOTING):
    // Only re-render when state changes to avoid wasteful SPI traffic
    if (_mouthAnimated || _mouthStateDrawn != _currentState) {
      _mouthAnimated = false;
      _mouthStateDrawn = _currentState;
      _mouthCanvas->fillScreen(COLOR_BG);

      int localCx = MOUTH_CANVAS_W / 2; // 40
      int localCy = MOUTH_CANVAS_H / 2; // 18

      if (_currentState == STATE_IDLE) {
        // Cyan rounded pill mouth matching frontend CSS
        _mouthCanvas->fillRoundRect(localCx - 22, localCy - 4, 44, 8, 4, COLOR_CYAN);
      } else if (_currentState == STATE_THINKING) {
        // Small focused violet mouth
        _mouthCanvas->fillRoundRect(localCx - 12, localCy - 3, 24, 6, 3, COLOR_VIOLET);
      } else if (_currentState == STATE_BOOTING) {
        _mouthCanvas->fillRoundRect(localCx - 22, localCy - 4, 44, 8, 4, COLOR_SKYBLUE);
      } else if (_currentState == STATE_ERROR) {
        for (int t = 0; t < 3; t++) {
          _mouthCanvas->drawCircle(localCx, localCy + 8 + t, 14, COLOR_CORAL);
        }
        _mouthCanvas->fillRect(localCx - 18, localCy + 4, 36, 18, COLOR_BG);
      }

      _tft.drawRGBBitmap(MOUTH_CANVAS_X, MOUTH_CANVAS_Y, _mouthCanvas->getBuffer(), MOUTH_CANVAS_W, MOUTH_CANVAS_H);
    }
  }
}

void DisplayManager::updateHalo(unsigned long now) {
  if (_currentState == STATE_THINKING) {
    _hadHalo = true;
    if (_haloCanvas) {
      _haloCanvas->fillScreen(COLOR_BG);
      drawThinkingHalo(_haloCanvas, HALO_CANVAS_W / 2, HALO_CANVAS_H / 2, now);
      _tft.drawRGBBitmap(HALO_CANVAS_X, HALO_CANVAS_Y, _haloCanvas->getBuffer(), HALO_CANVAS_W, HALO_CANVAS_H);
    }
  } else if (_hadHalo) {
    // Clear halo region once after leaving THINKING state
    _tft.fillRect(HALO_CANVAS_X, HALO_CANVAS_Y, HALO_CANVAS_W, HALO_CANVAS_H, COLOR_BG);
    _hadHalo = false;
  }
}

void DisplayManager::update() {
  unsigned long now = millis();
  // Smooth 40-50 FPS animation loop (every 22ms)
  if (now - _lastAnimUpdate < 22) {
    return;
  }
  _lastAnimUpdate = now;

  // Clean, zero-flicker independent zonal updates via off-screen micro-canvases
  updateHalo(now);
  updateEyes(now);
  updateMouth(now);

  _lastDrawnState = _currentState;
}
