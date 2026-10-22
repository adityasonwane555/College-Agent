/*
 * =====================================================================================
 * BUDDY AI — INMP441 I²S Microphone Manager
 * Hardware: INMP441 (SCK=GPIO 4, WS=GPIO 5, SD=GPIO 6, L/R=GND)
 * Controller: ESP32-S3 I²S0 (RX Mode)
 * =====================================================================================
 */

#pragma once

#include "config.h"
#include <driver/i2s.h>

class MicrophoneManager {
public:
  MicrophoneManager();

  bool begin();
  void stop();

  // Reads a batch of 16-bit PCM samples into destination buffer
  // Returns number of samples actually read
  size_t readSamples(int16_t* outBuffer, size_t maxSamples);

  // Calculates and returns current audio energy / RMS level (0.0 to 1.0)
  float getRecentEnergy() const { return _recentEnergy; }

  bool isRecording() const { return _isInitialized; }

private:
  bool _isInitialized;
  float _recentEnergy;
  int32_t _rawBuffer[MIC_BUFFER_SIZE];
};

extern MicrophoneManager microphoneManager;
