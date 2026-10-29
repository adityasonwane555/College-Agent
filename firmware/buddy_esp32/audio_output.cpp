/*
 * =====================================================================================
 * BUDDY AI — MAX98357A Audio Output Implementation
 * Hardware Peripheral: ESP32-S3 I2S1 Controller (Dedicated TX)
 * Pins: BCLK=GPIO 15, LRC=GPIO 16, DIN=GPIO 17
 * Note: I2S1 is strictly used for DAC playback to prevent resource contention
 *       with the INMP441 microphone operating concurrently on I2S0 RX.
 * =====================================================================================
 */

#include "audio_output.h"
#include <math.h>

AudioOutput audioOutput;

AudioOutput::AudioOutput()
  : _isInitialized(false),
    _volume(SPK_DEFAULT_VOLUME),
    _sampleRate(SPK_SAMPLE_RATE) {}

/**
 * Initializes the MAX98357A I2S audio driver.
 * Configures the I2S1 peripheral in Master TX mode.
 * Supports dynamic sample rate switching (e.g. 16 kHz for TTS speech, 24 kHz for neural voice).
 *
 * @param sampleRate Audio sampling rate in Hertz (typically 16000 or 24000).
 * @return True if I2S driver installed and GPIO pins successfully mapped.
 */
bool AudioOutput::begin(uint32_t sampleRate) {
  if (_isInitialized && _sampleRate == sampleRate) {
    return true;
  }
  if (_isInitialized) {
    stop();
  }

  _sampleRate = sampleRate;

  // I2S Configuration for MAX98357A:
  // - 16-bit signed PCM samples.
  // - Stereo slot format (MAX98357A decodes Left/Right depending on SD_MODE voltage,
  //   requiring standard stereo clock framing).
  // - 6 DMA buffers of 512 samples each to eliminate underrun clicks.
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
    .sample_rate = _sampleRate,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT, // Stereo slot format for standard MAX98357A
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 6,
    .dma_buf_len = 512,
    .use_apll = false,
    .tx_desc_auto_clear = true,
    .fixed_mclk = 0
  };

  i2s_pin_config_t pin_config = {
    .bck_io_num = PIN_AMP_BCLK,
    .ws_io_num = PIN_AMP_LRC,
    .data_out_num = PIN_AMP_DIN,
    .data_in_num = I2S_PIN_NO_CHANGE
  };

  esp_err_t err = i2s_driver_install(I2S_NUM_1, &i2s_config, 0, NULL);
  if (err != ESP_OK) {
    LOG_PRINTF("[AMP Error] i2s_driver_install failed: 0x%x\n", err);
    return false;
  }

  err = i2s_set_pin(I2S_NUM_1, &pin_config);
  if (err != ESP_OK) {
    LOG_PRINTF("[AMP Error] i2s_set_pin failed: 0x%x\n", err);
    i2s_driver_uninstall(I2S_NUM_1);
    return false;
  }

  _isInitialized = true;
  LOG_PRINTF("[AMP] MAX98357A initialized on I2S1 (BCLK=15, LRC=16, DIN=17) @ %u Hz.\n", _sampleRate);
  return true;
}

void AudioOutput::stop() {
  if (_isInitialized) {
    i2s_zero_dma_buffer(I2S_NUM_1);
    LOG_PRINTLN("[AMP] Audio DMA buffer cleared (immediate silence).");
  }
}

void AudioOutput::setVolume(float volume) {
  _volume = constrain(volume, 0.0f, 1.0f);
  LOG_PRINTF("[AMP] Volume set to %.2f\n", _volume);
}

size_t AudioOutput::writePcm(const int16_t* samples, size_t sampleCount) {
  if (!_isInitialized || !samples || sampleCount == 0) {
    return 0;
  }

  // Interleave mono into stereo frames in small chunks (stack-allocated)
  // MAX98357A consumes standard stereo I2S frames (duplicate mono to Left & Right)
  const size_t chunkSize = 256;
  int16_t stereoChunk[chunkSize * 2];
  size_t totalSamplesWritten = 0;

  for (size_t i = 0; i < sampleCount; i += chunkSize) {
    size_t count = (sampleCount - i < chunkSize) ? (sampleCount - i) : chunkSize;
    for (size_t c = 0; c < count; c++) {
      int32_t val32 = (int32_t)(samples[i + c] * _volume);
      if (val32 > 32767) val32 = 32767;
      if (val32 < -32768) val32 = -32768;
      int16_t val = (int16_t)val32;
      stereoChunk[c * 2]     = val; // Left channel
      stereoChunk[c * 2 + 1] = val; // Right channel
    }
    size_t bytesWritten = 0;
    esp_err_t err = i2s_write(
      I2S_NUM_1,
      (const void*)stereoChunk,
      count * 2 * sizeof(int16_t),
      &bytesWritten,
      portMAX_DELAY
    );
    if (err == ESP_OK) {
      totalSamplesWritten += (bytesWritten / (sizeof(int16_t) * 2));
    }
  }

  return totalSamplesWritten;
}

void AudioOutput::playChime() {
  if (!_isInitialized) {
    begin(24000);
  }

  LOG_PRINTLN("[AMP] Playing welcome chime (C5 -> E5 -> G5)...");

  const uint32_t sr = 24000;
  const size_t toneSamples = sr / 5; // 200 ms per tone
  int16_t* buf = (int16_t*)malloc(toneSamples * sizeof(int16_t));
  if (!buf) return;

  // Tone 1: 523.25 Hz (C5) - Full volume sine wave
  for (size_t i = 0; i < toneSamples; i++) {
    float env = 1.0f;
    if (i > (toneSamples * 4 / 5)) {
      env = (float)(toneSamples - i) / (toneSamples / 5); // Smooth decay to prevent clicks
    }
    float s = sin(2.0f * PI * 523.25f * ((float)i / sr)) * 24000.0f * env;
    buf[i] = (int16_t)s;
  }
  writePcm(buf, toneSamples);

  // Short pause (25 ms silence)
  memset(buf, 0, (sr / 40) * sizeof(int16_t));
  writePcm(buf, sr / 40);

  // Tone 2: 659.25 Hz (E5)
  for (size_t i = 0; i < toneSamples; i++) {
    float env = 1.0f;
    if (i > (toneSamples * 4 / 5)) {
      env = (float)(toneSamples - i) / (toneSamples / 5);
    }
    float s = sin(2.0f * PI * 659.25f * ((float)i / sr)) * 24000.0f * env;
    buf[i] = (int16_t)s;
  }
  writePcm(buf, toneSamples);

  // Short pause (25 ms silence)
  memset(buf, 0, (sr / 40) * sizeof(int16_t));
  writePcm(buf, sr / 40);

  // Tone 3: 783.99 Hz (G5)
  for (size_t i = 0; i < toneSamples; i++) {
    float env = 1.0f;
    if (i > (toneSamples * 4 / 5)) {
      env = (float)(toneSamples - i) / (toneSamples / 5);
    }
    float s = sin(2.0f * PI * 783.99f * ((float)i / sr)) * 24000.0f * env;
    buf[i] = (int16_t)s;
  }
  writePcm(buf, toneSamples);

  free(buf);
  LOG_PRINTLN("[AMP] Chime playback complete.");
}
