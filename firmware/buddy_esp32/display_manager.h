/*
 * =====================================================================================
 * BUDDY AI — ST7789 2.8-inch SPI TFT LCD Display Manager
 * Exact Mirror of Web Kiosk Robot Face (Visor, Eyes, Cheeks, Waveform & Halo)
 * Resolution: 240 x 320 Portrait
 * Hardware: ST7789 (SCL=12, SDA=11, CS=10, DC=9, RST=13, BLK=14)
 * Optimizations:
 *   - 40 MHz Hardware SPI Bus on ESP32-S3
 *   - Off-screen Micro-Canvas Double Buffering (Zero Screen Tearing & Zero Flicker)
 *   - Differential Zonal Rendering (Only Eyes Blink, Cheeks & Mouth Isolated)
 * =====================================================================================
 */

#pragma once

#include "config.h"
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>

// Micro-canvas dimensions for flicker-free double buffering
#define EYE_CANVAS_W      160
#define EYE_CANVAS_H      84
#define EYE_CANVAS_X      40   // cx - 80 = 120 - 80 = 40
#define EYE_CANVAS_Y      86   // eyeY - 42 = 128 - 42 = 86

#define MOUTH_CANVAS_W    80
#define MOUTH_CANVAS_H    36
#define MOUTH_CANVAS_X    80   // cx - 40 = 120 - 40 = 80
#define MOUTH_CANVAS_Y    212  // mouthY - 18 = 230 - 18 = 212

#define HALO_CANVAS_W     96
#define HALO_CANVAS_H     18
#define HALO_CANVAS_X     72   // cx - 48 = 120 - 48 = 72
#define HALO_CANVAS_Y     23   // haloY - 9 = 32 - 9 = 23

class DisplayManager {
public:
  DisplayManager();
  ~DisplayManager();

  void begin();
  void setState(BuddyState state);
  void setWifiInfo(const String& ssid, const String& ip);
  void setMessage(const String& title, const String& body);
  void setAudioLevel(float level);
  void update(); // Called in loop()

private:
  Adafruit_ST7789 _tft;
  GFXcanvas16* _eyeCanvas;
  GFXcanvas16* _mouthCanvas;
  GFXcanvas16* _haloCanvas;

  BuddyState _currentState;
  BuddyState _lastDrawnState;
  unsigned long _lastAnimUpdate;
  unsigned long _stateStartTime;
  
  String _ssid;
  String _ip;
  String _messageTitle;
  String _messageBody;
  String _lastMessageTitle;
  float _audioLevel;
  
  // Natural Periodic Blinking State
  unsigned long _nextBlinkTime;
  bool _isBlinking;
  unsigned long _blinkStartTime;
  int _blinkDuration;
  int _lastEyeH;
  
  // Gaze Saccade Tracking
  unsigned long _nextGazeTime;
  int _targetGazeX;
  int _targetGazeY;
  float _currentGazeX;
  float _currentGazeY;
  int _lastGazeX;
  int _lastGazeY;
  int _lastEyeY;
  
  // Redraw flags
  bool _forceFullClear;
  bool _hadHalo;
  bool _mouthAnimated;
  BuddyState _mouthStateDrawn;

  void drawStaticFace();
  void updateEyes(unsigned long now);
  void updateMouth(unsigned long now);
  void updateHalo(unsigned long now);

  void drawEyeCapsule(Adafruit_GFX* gfx, int cx, int cy, int w, int h, int r, uint16_t color, int gazeX, int gazeY);
  void drawSmilingEye(Adafruit_GFX* gfx, int cx, int cy, int w, int h, uint16_t color);
  void drawWaveformBars(Adafruit_GFX* gfx, int cx, int cy, unsigned long now);
  void drawThinkingHalo(Adafruit_GFX* gfx, int cx, int cy, unsigned long now);
};

extern DisplayManager displayManager;
