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

  /**
   * Initializes the WS2812 RGB LED peripheral on GPIO 48.
   * Sets initial booting state and applies warm amber diagnostic glow.
   */
  void begin();

  /**
   * Transitions the LED engine to a new BuddyState (IDLE, LISTENING, THINKING, SPEAKING, ERROR).
   * Resets animation phase timer while preserving smooth visual continuity.
   *
   * @param state Target robot state enumeration.
   */
  void setState(BuddyState state);

  /**
   * Ingests real-time audio visualization metrics from PC audio playback stream.
   * Values are clamped to [0.0, 1.0] and modulate LED intensity/hue during STATE_SPEAKING.
   *
   * @param amplitude Overall normalized signal volume envelope (0.0 to 1.0).
   * @param bass Low-frequency energy weight (0.0 to 1.0).
   * @param mid Vocal midrange frequency energy weight (0.0 to 1.0).
   * @param treble High-frequency cadence weight (0.0 to 1.0).
   */
  void setAudioLevels(float amplitude, float bass = 0.0f, float mid = 0.0f, float treble = 0.0f);

  /**
   * Main non-blocking animation render tick.
   * Computes mathematical color frames and updates WS2812 output at ~30-50 FPS.
   * Must be called continuously in Arduino loop().
   */
  void update();

  /**
   * Returns the current active hardware visualization state.
   */
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
