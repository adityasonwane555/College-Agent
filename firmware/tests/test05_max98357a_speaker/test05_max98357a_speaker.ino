/*
 * =====================================================================================
 * BUDDY AI — HARDWARE TEST 5: MAX98357A I²S Amplifier & Speaker Output
 * Hardware Wiring:
 *   MAX98357A VIN   -> 5V (ESP32 5V or VBUS pin)
 *   MAX98357A GND   -> GND
 *   MAX98357A BCLK  -> GPIO 15 (I2S1 Bit Clock)
 *   MAX98357A LRC   -> GPIO 16 (I2S1 Word Select)
 *   MAX98357A DIN   -> GPIO 17 (I2S1 Audio Data)
 *   MAX98357A SD    -> Connect to 3.3V Rail (wakes chip up from shutdown & enables Left channel)
 *   SPK+ and SPK-   -> Passive 4 or 8 Ohm Speaker Terminals (NEVER GROUND!)
 * =====================================================================================
 */

#include <driver/i2s.h>
#include <math.h>

#define I2S_PORT        I2S_NUM_1
#define PIN_AMP_BCLK    15
#define PIN_AMP_LRC     16
#define PIN_AMP_DIN     17

#define SAMPLE_RATE     24000
#define BUFFER_SIZE     256

float volume = 0.85f; // Clear audible volume level (0.0 to 1.0)

void playTone(float freqHz, uint32_t durationMs) {
  size_t totalSamples = (SAMPLE_RATE * durationMs) / 1000;
  int16_t stereoBuffer[BUFFER_SIZE * 2];
  size_t samplesGenerated = 0;

  while (samplesGenerated < totalSamples) {
    size_t chunk = min((size_t)BUFFER_SIZE, totalSamples - samplesGenerated);
    for (size_t i = 0; i < chunk; i++) {
      float t = (float)(samplesGenerated + i) / SAMPLE_RATE;
      // Exponential fade out in the last 20% of the note to eliminate clicks
      float env = 1.0f;
      size_t remaining = totalSamples - (samplesGenerated + i);
      if (remaining < (totalSamples / 5)) {
        env = (float)remaining / (totalSamples / 5);
      }
      int16_t sample = (int16_t)(sin(2.0f * PI * freqHz * t) * 24000.0f * volume * env);
      stereoBuffer[i * 2]     = sample; // Left
      stereoBuffer[i * 2 + 1] = sample; // Right
    }

    size_t bytesWritten = 0;
    i2s_write(I2S_PORT, stereoBuffer, chunk * 2 * sizeof(int16_t), &bytesWritten, portMAX_DELAY);
    samplesGenerated += chunk;
  }
}

void setup() {
  Serial.begin(115200);
  Serial0.begin(115200);
  delay(500);

  Serial.println("\n========================================================");
  Serial.println("  BUDDY AI — TEST 5: MAX98357A I²S Amplifier Diagnostic ");
  Serial.println("========================================================");

  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4,
    .dma_buf_len = BUFFER_SIZE,
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

  esp_err_t err = i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
  if (err != ESP_OK) {
    Serial.printf("[FAIL] i2s_driver_install returned: 0x%x\n", err);
    return;
  }

  err = i2s_set_pin(I2S_PORT, &pin_config);
  if (err != ESP_OK) {
    Serial.printf("[FAIL] i2s_set_pin returned: 0x%x\n", err);
    return;
  }

  Serial.println("[AMP] MAX98357A initialized on I2S1 (15, 16, 17) @ 24kHz.");
  Serial.println("[Audio] Playing major chord chime: C4 (261Hz) -> E4 (329Hz) -> G4 (392Hz) -> C5 (523Hz)...");

  // Play pleasant welcome arpeggio
  playTone(261.63f, 250); // C4
  delay(20);
  playTone(329.63f, 250); // E4
  delay(20);
  playTone(392.00f, 250); // G4
  delay(20);
  playTone(523.25f, 400); // C5
  delay(100);

  Serial.println("\n========================================================");
  Serial.println("  >>> TEST 5 STATUS: PASS <<<                           ");
  Serial.println("========================================================");
}

void loop() {
  delay(1000);
}
