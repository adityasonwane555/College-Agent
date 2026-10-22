/*
 * =====================================================================================
 * BUDDY AI — Onboard WS2812 RGB LED Manager
 * Pin: GPIO 48
 * Non-blocking millis()-based animation engine
 * =====================================================================================
 */

#pragma once

#include "config.h"

class RgbManager {
public:
  RgbManager();

  void begin();
  void setState(BuddyState state);
  void setAudioLevels(float amplitude, float bass = 0.0f, float mid = 0.0f, float treble = 0.0f);
  void update(); // Called in loop()

  BuddyState getState() const { return _currentState; }

private:
  BuddyState _currentState;
  BuddyState _targetState;
  
  unsigned long _lastUpdate;
  unsigned long _stateStartTime;
  
  float _amplitude;
  float _bass;
  float _mid;
  float _treble;

  void applyColor(uint8_t r, uint8_t g, uint8_t b);
  void renderIdle(unsigned long elapsed);
  void renderListening(unsigned long elapsed);
  void renderThinking(unsigned long elapsed);
  void renderSpeaking(unsigned long elapsed);
  void renderError(unsigned long elapsed);
  void renderBooting(unsigned long elapsed);
};

extern RgbManager rgbManager;
