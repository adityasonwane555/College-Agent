/*
 * =====================================================================================
 * BUDDY AI — ST7789 2.8-inch SPI TFT LCD Display Manager
 * Exact Mirror of Web Kiosk Robot Face (Visor, Eyes, Cheeks, Waveform & Halo)
 * Resolution: 240 x 320 Portrait
 * Hardware: ST7789 (SCL=12, SDA=11, CS=10, DC=9, RST=13, BLK=14)
 * =====================================================================================
 */

#pragma once

#include "config.h"
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>

class DisplayManager {
public:
  DisplayManager();

  void begin();
  void setState(BuddyState state);
  void setWifiInfo(const String& ssid, const String& ip);
  void setMessage(const String& title, const String& body);
  void setAudioLevel(float level);
  void update(); // Called in loop()

private:
  Adafruit_ST7789 _tft;
  BuddyState _currentState;
  unsigned long _lastAnimUpdate;
  unsigned long _stateStartTime;
  
  String _ssid;
  String _ip;
  String _messageTitle;
  String _messageBody;
  float _audioLevel;
  
  // Natural Periodic Blinking State
  unsigned long _nextBlinkTime;
  bool _isBlinking;
  unsigned long _blinkStartTime;
  int _blinkDuration;
  
  // Gaze Saccade Tracking
  unsigned long _nextGazeTime;
  int _targetGazeX;
  int _targetGazeY;
  int _currentGazeX;
  int _currentGazeY;
  
  // Dirty redraw flags
  bool _forceFullClear;
  bool _hadHalo;

  void drawFaceFrame(unsigned long now);
  void drawEyeCapsule(int cx, int cy, int w, int h, int r, uint16_t color, int gazeX, int gazeY);
  void drawSmilingEye(int cx, int cy, int w, int h, uint16_t color);
  void drawWaveformBars(int cx, int cy, unsigned long now);
  void drawThinkingHalo(int cx, int cy, unsigned long now);
};

extern DisplayManager displayManager;
