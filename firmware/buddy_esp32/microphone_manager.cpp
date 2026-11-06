/*
 * =====================================================================================
 * BUDDY AI — INMP441 Omnidirectional Microphone Manager Implementation
 * Hardware Peripheral: ESP32-S3 I2S0 Controller (Dedicated RX)
 * Pins: SCK=GPIO 4, WS=GPIO 5, SD=GPIO 6
 *
 * Hardware & Audio Pipeline Architecture:
 *   - Dedicated I2S0 Peripheral: Runs in Master RX mode at 16,000 Hz, strictly isolated
 *     from I2S1 TX (speaker DAC) to guarantee non-blocking full-duplex operation.
 *   - Precision Bit Shift & Alignment: INMP441 transmits 24-bit audio left-justified
 *     inside a 32-bit slot. Samples are shifted right by 14 bits (`_rawBuffer[i] >> 14`)
 *     and clamped to signed 16-bit boundaries [-32768, 32767] to prevent wrap-around clicks.
 *   - DMA Ring Buffering: 4 ring buffers of 512 samples each provide jitter-free continuous
 *     capture with minimal latency for real-time speech streaming.
 *   - Real-Time Energy Computation: Computes instantaneous Root-Mean-Square (RMS) amplitude
 *     normalized to [0.0, 1.0] across each chunk for voice activity detection and lip sync.
 * =====================================================================================
 */

#include "microphone_manager.h"
#include <math.h>

MicrophoneManager microphoneManager;

MicrophoneManager::MicrophoneManager()
  : _isInitialized(false),
    _recentEnergy(0.0f) {}

/**
 * Initializes the INMP441 digital MEMS microphone driver on I2S0.
 * Configures the peripheral in Master RX mode with 32-bit slot width.
 * Maps SCK (GPIO 4), WS (GPIO 5), and SD (GPIO 6).
 *
 * @return True if I2S0 driver installed and GPIO pins successfully mapped.
 */
bool MicrophoneManager::begin() {
  if (_isInitialized) {
    return true;
  }

  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = MIC_SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT, // INMP441 outputs 24-bit in 32-bit slot
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,  // L/R tied to GND selects Left
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4,
    .dma_buf_len = MIC_BUFFER_SIZE,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };

  i2s_pin_config_t pin_config = {
    .bck_io_num = PIN_MIC_SCK,
    .ws_io_num = PIN_MIC_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = PIN_MIC_SD
  };

  esp_err_t err = i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  if (err != ESP_OK) {
    LOG_PRINTF("[MIC Error] i2s_driver_install failed: 0x%x\n", err);
    return false;
  }

  err = i2s_set_pin(I2S_NUM_0, &pin_config);
  if (err != ESP_OK) {
    LOG_PRINTF("[MIC Error] i2s_set_pin failed: 0x%x\n", err);
    i2s_driver_uninstall(I2S_NUM_0);
    return false;
  }

  _isInitialized = true;
  LOG_PRINTLN("[MIC] INMP441 initialized on I2S0 (SCK=4, WS=5, SD=6) @ 16kHz.");
  return true;
}

/**
 * Safely uninstalls the I2S0 driver and releases allocated DMA buffers.
 */
void MicrophoneManager::stop() {
  if (_isInitialized) {
    i2s_driver_uninstall(I2S_NUM_0);
    _isInitialized = false;
    LOG_PRINTLN("[MIC] Driver stopped.");
  }
}

/**
 * Reads captured audio samples from the I2S0 DMA ring buffer into a signed 16-bit PCM array.
 * Converts 24-bit/32-slot raw data into standard signed 16-bit PCM via bit-shift decimation.
 * Clamps values to [-32768, 32767] and calculates the RMS energy level for speech activity.
 *
 * @param outBuffer Destination buffer for signed 16-bit PCM samples.
 * @param maxSamples Maximum number of samples to read.
 * @return Number of 16-bit samples successfully read and converted.
 */
size_t MicrophoneManager::readSamples(int16_t* outBuffer, size_t maxSamples) {
  if (!_isInitialized || !outBuffer || maxSamples == 0) {
    return 0;
  }

  size_t toRead = min(maxSamples, (size_t)MIC_BUFFER_SIZE);
  size_t bytesRead = 0;
  
  esp_err_t res = i2s_read(
    I2S_NUM_0,
    (void*)_rawBuffer,
    toRead * sizeof(int32_t),
    &bytesRead,
    pdMS_TO_TICKS(50)
  );

  if (res != ESP_OK || bytesRead == 0) {
    return 0;
  }

  size_t samplesRead = bytesRead / sizeof(int32_t);
  int64_t sumSquares = 0;

  for (size_t i = 0; i < samplesRead; i++) {
    // INMP441 24-bit data sits in the upper bits of the 32-bit word.
    // Shift right by 14 and clamp strictly within signed 16-bit bounds [-32768, 32767]
    // to preserve vocal dynamic range while avoiding integer wrap-around distortion.
    int32_t val32 = _rawBuffer[i] >> 14;
    if (val32 > 32767) val32 = 32767;
    else if (val32 < -32768) val32 = -32768;
    int16_t sample16 = (int16_t)val32;
    outBuffer[i] = sample16;
    sumSquares += (int64_t)sample16 * sample16;
  }

  // Calculate RMS energy (normalized 0.0 to 1.0)
  float meanSquare = (float)sumSquares / (float)samplesRead;
  float rms = sqrt(meanSquare);
  _recentEnergy = constrain(rms / 12000.0f, 0.0f, 1.0f);

  return samplesRead;
}
