/*
 * =====================================================================================
 * BUDDY AI — Onboard WS2812 RGB LED Manager Implementation
 * Hardware Peripheral: Onboard Addressable WS2812 RGB LED on GPIO 48
 *
 * Lighting Architecture & Visual Feedback:
 *   - Non-Blocking 50 Hz Update Loop: Renders state-dependent light patterns every 20ms
 *     without blocking the main FreeRTOS loop, SPI display updates, or audio streaming.
 *   - Global Brightness Limiting: Scales all color channels through `RGB_MAX_BRIGHTNESS`
 *     to prevent excessive current draw and heat dissipation on the ESP32-S3 3.3V rail.
 *   - Parametric Sinusoidal Waveforms: Uses continuous trigonometric phase functions
 *     for natural organic breathing across IDLE (3.0s cyan), LISTENING (1.2s blue),
 *     THINKING (800ms amber), and ERROR (1.0s crimson).
 *   - Audio-Reactive 3-Band Equalizer: Real-time dynamic spectral color blending during
 *     STATE_SPEAKING, mapping Bass to Red (chest resonance), Mid to Green (vocal formants),
 *     and Treble to Blue (sibilance/consonants), falling back to purple breath between phrases.
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

/**
 * Initializes the WS2812 RGB LED driver.
 * Sets the power-on color to warm amber and starts the state timer.
 */
void RgbManager::begin() {
  _stateStartTime = millis();
  applyColor(40, 20, 0); // Warm amber on initial boot
  LOG_PRINTLN("[RGB] Manager initialized on GPIO 48.");
}

/**
 * Transitions the RGB lighting engine to a new robot state.
 * Resets state start timestamp so periodic animations begin smoothly from phase 0.
 *
 * @param state The target BuddyState enum value.
 */
void RgbManager::setState(BuddyState state) {
  if (_currentState != state) {
    _currentState = state;
    _stateStartTime = millis();
    LOG_PRINTF("[RGB] State transitioned to: %s\n", buddyStateToString(state));
  }
}

/**
 * Updates dynamic audio spectral levels for speech-reactive lighting.
 * Clamps all input bands within unit range [0.0, 1.0].
 *
 * @param amplitude Overall normalized audio RMS volume [0.0 - 1.0].
 * @param bass Low-frequency energy [80-250 Hz] mapped to red channel.
 * @param mid Mid-frequency speech formants [500-2000 Hz] mapped to green channel.
 * @param treble High-frequency consonants/sibilance [3000-8000 Hz] mapped to blue channel.
 */
void RgbManager::setAudioLevels(float amplitude, float bass, float mid, float treble) {
  _amplitude = constrain(amplitude, 0.0f, 1.0f);
  _bass      = constrain(bass, 0.0f, 1.0f);
  _mid       = constrain(mid, 0.0f, 1.0f);
  _treble    = constrain(treble, 0.0f, 1.0f);
}

/**
 * Applies 8-bit RGB color values to the onboard WS2812 LED on GPIO 48.
 * Scales each channel through RGB_MAX_BRIGHTNESS to prevent power rail brownouts.
 *
 * @param r Red component [0 - 255].
 * @param g Green component [0 - 255].
 * @param b Blue component [0 - 255].
 */
void RgbManager::applyColor(uint8_t r, uint8_t g, uint8_t b) {
  uint8_t scaledR = (uint8_t)(((uint16_t)r * RGB_MAX_BRIGHTNESS) / 255);
  uint8_t scaledG = (uint8_t)(((uint16_t)g * RGB_MAX_BRIGHTNESS) / 255);
  uint8_t scaledB = (uint8_t)(((uint16_t)b * RGB_MAX_BRIGHTNESS) / 255);
  rgbLedWrite(PIN_RGB_LED, scaledR, scaledG, scaledB);
}

/**
 * Non-blocking 50 Hz animation tick (20ms interval).
 * Dispatches to state-specific rendering routines based on _currentState.
 */
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

/**
 * Renders IDLE state: Soft cyan breathing (calm, ready for user interaction).
 * Uses a 3.0-second sinusoidal brightness wave (15-80 intensity) to create a relaxed standby presence.
 *
 * @param elapsed Milliseconds elapsed since entering IDLE state.
 */
void RgbManager::renderIdle(unsigned long elapsed) {
  float wave = (sin((elapsed / 3000.0f) * 2.0f * PI) + 1.0f) * 0.5f; // 3 sec cycle
  uint8_t brightness = (uint8_t)(15 + wave * 65);
  applyColor(0, brightness, (uint8_t)(brightness * 1.2f));
}

/**
 * Renders LISTENING state: Electric blue pulsing (signals active attention to user voice).
 * 1.2-second sine wave alerting user that the INMP441 microphone DMA is recording.
 *
 * @param elapsed Milliseconds elapsed since entering LISTENING state.
 */
void RgbManager::renderListening(unsigned long elapsed) {
  float wave = (sin((elapsed / 1200.0f) * 2.0f * PI) + 1.0f) * 0.5f; // 1.2 sec cycle
  uint8_t val = (uint8_t)(40 + wave * 180);
  applyColor(0, (uint8_t)(val * 0.35f), val);
}

/**
 * Renders THINKING state: Warm amber pulse (signals LLM / search reasoning in progress).
 * Brisk 800ms sine modulation indicating active backend orchestrator computation.
 *
 * @param elapsed Milliseconds elapsed since entering THINKING state.
 */
void RgbManager::renderThinking(unsigned long elapsed) {
  float wave = (sin((elapsed / 800.0f) * 2.0f * PI) + 1.0f) * 0.5f; // 800ms brisk pulse
  uint8_t val = (uint8_t)(40 + wave * 180);
  applyColor(val, (uint8_t)(val * 0.45f), 0);
}

/**
 * Renders SPEAKING state: Smooth reactive purple reacting to speech volume and frequency bands.
 * Real-time 3-band equalizer:
 *   - Red channel: low-frequency speech chest resonance (Bass: 80-250 Hz).
 *   - Green channel: vocal clarity and formants (Mid: 500-2000 Hz).
 *   - Blue channel: sibilance and breath consonants (Treble: 3000-8000 Hz).
 * Falls back to gentle 1.5s purple breathing during silence between sentences.
 *
 * @param elapsed Milliseconds elapsed since entering SPEAKING state.
 */
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

/**
 * Renders ERROR state: Pulsing crimson red (1000ms period) indicating network or hardware fault.
 *
 * @param elapsed Milliseconds elapsed since entering ERROR state.
 */
void RgbManager::renderError(unsigned long elapsed) {
  float wave = (sin((elapsed / 1000.0f) * 2.0f * PI) + 1.0f) * 0.5f;
  uint8_t val = (uint8_t)(50 + wave * 160);
  applyColor(val, 0, 0);
}

/**
 * Renders BOOTING state: Soft amber/orange warm glow during power-on self test.
 *
 * @param elapsed Milliseconds elapsed since power on.
 */
void RgbManager::renderBooting(unsigned long elapsed) {
  float wave = (sin((elapsed / 1500.0f) * 2.0f * PI) + 1.0f) * 0.5f;
  uint8_t val = (uint8_t)(40 + wave * 80);
  applyColor(val, (uint8_t)(val * 0.3f), 0);
}
