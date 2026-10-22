/*
 * =====================================================================================
 * BUDDY AI — MAX98357A I²S Amplifier & Speaker Output Manager
 * Hardware: MAX98357A (BCLK=GPIO 15, LRC=GPIO 16, DIN=GPIO 17, VIN=5V)
 * Controller: ESP32-S3 I²S1 (TX Mode)
 * =====================================================================================
 */

#pragma once

#include "config.h"
#include <driver/i2s.h>

class AudioOutput {
public:
  AudioOutput();

  bool begin(uint32_t sampleRate = SPK_SAMPLE_RATE);
  void stop();

  // Plays a self-generated pleasant sine wave test tone (chime)
  void playChime();

  // Writes 16-bit PCM streaming audio chunk to amplifier DMA buffer
  size_t writePcm(const int16_t* samples, size_t sampleCount);

  // Sets digital volume scaling (0.0 to 1.0)
  void setVolume(float volume);
  float getVolume() const { return _volume; }

  bool isReady() const { return _isInitialized; }

private:
  bool _isInitialized;
  float _volume;
  uint32_t _sampleRate;
};

extern AudioOutput audioOutput;
