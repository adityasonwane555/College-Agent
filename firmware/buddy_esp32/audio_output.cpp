/*
 * =====================================================================================
 * BUDDY AI — MAX98357A Audio Output Implementation
 * =====================================================================================
 */

#include "audio_output.h"
#include <math.h>

AudioOutput audioOutput;

AudioOutput::AudioOutput()
  : _isInitialized(false),
    _volume(SPK_DEFAULT_VOLUME),
    _sampleRate(SPK_SAMPLE_RATE) {}

bool AudioOutput::begin(uint32_t sampleRate) {
  if (_isInitialized && _sampleRate == sampleRate) {
    return true;
  }
  if (_isInitialized) {
    stop();
  }

  _sampleRate = sampleRate;

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
    i2s_driver_uninstall(I2S_NUM_1);
    _isInitialized = false;
    LOG_PRINTLN("[AMP] Driver stopped.");
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

  // Allocate a stereo interleaved buffer on the stack / heap
  // MAX98357A consumes standard stereo I2S frames (duplicate mono sample to Left & Right)
  size_t stereoSamples = sampleCount * 2;
  int16_t* stereoBuf = (int16_t*)malloc(stereoSamples * sizeof(int16_t));
  if (!stereoBuf) {
    return 0;
  }

  for (size_t i = 0; i < sampleCount; i++) {
    int16_t scaled = (int16_t)(samples[i] * _volume);
    stereoBuf[i * 2]     = scaled; // Left
    stereoBuf[i * 2 + 1] = scaled; // Right
  }

  size_t bytesWritten = 0;
  i2s_write(
    I2S_NUM_1,
    (const void*)stereoBuf,
    stereoSamples * sizeof(int16_t),
    &bytesWritten,
    pdMS_TO_TICKS(100)
  );

  free(stereoBuf);
  return bytesWritten / (sizeof(int16_t) * 2);
}

void AudioOutput::playChime() {
  if (!_isInitialized) {
    begin(24000);
  }

  LOG_PRINTLN("[AMP] Playing test chime (440Hz -> 880Hz)...");

  const uint32_t sr = 24000;
  const size_t toneSamples = sr / 5; // 200 ms per tone
  int16_t* buf = (int16_t*)malloc(toneSamples * sizeof(int16_t));
  if (!buf) return;

  // Tone 1: 440 Hz (A4)
  for (size_t i = 0; i < toneSamples; i++) {
    float env = 1.0f - ((float)i / toneSamples); // Fade out envelope
    float s = sin(2.0f * PI * 440.0f * ((float)i / sr)) * 8000.0f * env;
    buf[i] = (int16_t)s;
  }
  writePcm(buf, toneSamples);

  // Short pause (20ms silence)
  memset(buf, 0, (sr / 50) * sizeof(int16_t));
  writePcm(buf, sr / 50);

  // Tone 2: 880 Hz (A5)
  for (size_t i = 0; i < toneSamples; i++) {
    float env = 1.0f - ((float)i / toneSamples);
    float s = sin(2.0f * PI * 880.0f * ((float)i / sr)) * 7500.0f * env;
    buf[i] = (int16_t)s;
  }
  writePcm(buf, toneSamples);

  free(buf);
  LOG_PRINTLN("[AMP] Chime playback complete.");
}
