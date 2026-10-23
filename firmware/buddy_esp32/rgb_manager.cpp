/*
 * =====================================================================================
 * BUDDY AI — Onboard WS2812 RGB LED Manager Implementation
 * =====================================================================================
 */

#include "rgb_manager.h"
#include <math.h>

RgbManager rgbManager;

RgbManager::RgbManager()
  : _currentState(STATE_BOOTING),
    _targetState(STATE_BOOTING),
    _lastUpdate(0),
    _stateStartTime(0),
    _amplitude(0.0f),
    _bass(0.0f),
    _mid(0.0f),
    _treble(0.0f) {}

void RgbManager::begin() {
  _stateStartTime = millis();
  applyColor(40, 20, 0); // Warm amber on initial boot
  LOG_PRINTLN("[RGB] Manager initialized on GPIO 48.");
}

void RgbManager::setState(BuddyState state) {
  if (_currentState != state) {
    _currentState = state;
    _stateStartTime = millis();
    LOG_PRINTF("[RGB] State transitioned to: %s\n", buddyStateToString(state));
  }
}

void RgbManager::setAudioLevels(float amplitude, float bass, float mid, float treble) {
  _amplitude = constrain(amplitude, 0.0f, 1.0f);
  _bass      = constrain(bass, 0.0f, 1.0f);
  _mid       = constrain(mid, 0.0f, 1.0f);
  _treble    = constrain(treble, 0.0f, 1.0f);
}

void RgbManager::applyColor(uint8_t r, uint8_t g, uint8_t b) {
  uint8_t scaledR = (uint8_t)(((uint16_t)r * RGB_MAX_BRIGHTNESS) / 255);
  uint8_t scaledG = (uint8_t)(((uint16_t)g * RGB_MAX_BRIGHTNESS) / 255);
  uint8_t scaledB = (uint8_t)(((uint16_t)b * RGB_MAX_BRIGHTNESS) / 255);
  rgbLedWrite(PIN_RGB_LED, scaledR, scaledG, scaledB);
}

void RgbManager::update() {
  unsigned long now = millis();
  if (now - _lastUpdate < 20) { // 50 Hz smooth refresh
    return;
  }
  _lastUpdate = now;
  unsigned long elapsed = now - _stateStartTime;

  switch (_currentState) {
    case STATE_BOOTING:     renderBooting(elapsed);   break;
    case STATE_IDLE:        renderIdle(elapsed);      break;
    case STATE_LISTENING:   renderListening(elapsed); break;
    case STATE_THINKING:    renderThinking(elapsed);  break;
    case STATE_SPEAKING:    renderSpeaking(elapsed);  break;
    case STATE_ERROR:       renderError(elapsed);     break;
    case STATE_INTERRUPTED: applyColor(180, 40, 0);   break;
    default:                applyColor(0, 0, 0);      break;
  }
}

// IDLE: Soft cyan breathing (calm, ready for user interaction)
// Uses a 3.0-second sinusoidal brightness wave (15-80 intensity) to create a relaxed standby presence.
void RgbManager::renderIdle(unsigned long elapsed) {
  float wave = (sin((elapsed / 3000.0f) * 2.0f * PI) + 1.0f) * 0.5f; // 3 sec cycle
  uint8_t brightness = (uint8_t)(15 + wave * 65);
  applyColor(0, brightness, (uint8_t)(brightness * 1.2f));
}

// LISTENING: Electric blue pulsing (signals active attention to user voice)
// Faster 1.2-second sine wave alerting user that the INMP441 microphone DMA is recording.
void RgbManager::renderListening(unsigned long elapsed) {
  float wave = (sin((elapsed / 1200.0f) * 2.0f * PI) + 1.0f) * 0.5f; // 1.2 sec cycle
  uint8_t val = (uint8_t)(40 + wave * 180);
  applyColor(0, (uint8_t)(val * 0.35f), val);
}

// THINKING: Warm amber pulse (signals LLM / search reasoning in progress)
// Brisk 800ms sine modulation indicating active backend orchestrator computation.
void RgbManager::renderThinking(unsigned long elapsed) {
  float wave = (sin((elapsed / 800.0f) * 2.0f * PI) + 1.0f) * 0.5f; // 800ms brisk pulse
  uint8_t val = (uint8_t)(40 + wave * 180);
  applyColor(val, (uint8_t)(val * 0.45f), 0);
}

// SPEAKING: Smooth reactive purple reacting to speech volume / frequencies
// Dynamic multi-band equalizer:
// - Red channel maps to low-frequency speech chest resonance (Bass: 80-250 Hz).
// - Green channel maps to vocal clarity / formants (Mid: 500-2000 Hz).
// - Blue channel maps to sibilance and breath consonants (Treble: 3000-8000 Hz).
void RgbManager::renderSpeaking(unsigned long elapsed) {
  if (_amplitude > 0.05f) {
    // Reactive modulation based on volume and frequency bands
    uint8_t r = (uint8_t)constrain(60 + _bass * 160.0f + _amplitude * 35.0f, 0.0f, 255.0f);
    uint8_t g = (uint8_t)constrain(_mid * 90.0f, 0.0f, 255.0f);
    uint8_t b = (uint8_t)constrain(100 + _treble * 130.0f + _amplitude * 25.0f, 0.0f, 255.0f);
    applyColor(r, g, b);
  } else {
    // Gentle purple breathing between sentences to maintain visual warmth
    float wave = (sin((elapsed / 1500.0f) * 2.0f * PI) + 1.0f) * 0.5f;
    uint8_t val = (uint8_t)(30 + wave * 100);
    applyColor(val, 0, (uint8_t)(val * 1.4f));
  }
}

// ERROR: Pulsing crimson red (1000ms period) indicating network or hardware fault
void RgbManager::renderError(unsigned long elapsed) {
  float wave = (sin((elapsed / 1000.0f) * 2.0f * PI) + 1.0f) * 0.5f;
  uint8_t val = (uint8_t)(50 + wave * 160);
  applyColor(val, 0, 0);
}

// BOOTING: Soft amber/orange warm glow during power-on self test
void RgbManager::renderBooting(unsigned long elapsed) {
  float wave = (sin((elapsed / 1500.0f) * 2.0f * PI) + 1.0f) * 0.5f;
  uint8_t val = (uint8_t)(40 + wave * 80);
  applyColor(val, (uint8_t)(val * 0.3f), 0);
}
