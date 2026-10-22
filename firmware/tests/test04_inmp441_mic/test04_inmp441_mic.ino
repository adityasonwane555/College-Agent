/*
 * =====================================================================================
 * BUDDY AI — HARDWARE TEST 4: INMP441 I²S Digital Microphone
 * Hardware Wiring:
 *   INMP441 VDD -> 3.3V (NEVER 5V!)
 *   INMP441 GND -> GND
 *   INMP441 SCK -> GPIO 4 (I2S0 Bit Clock)
 *   INMP441 WS  -> GPIO 5 (I2S0 Word Select)
 *   INMP441 SD  -> GPIO 6 (I2S0 Serial Data Out to ESP32)
 *   INMP441 L/R -> GND    (Selects Left channel)
 * =====================================================================================
 */

#include <driver/i2s.h>
#include <math.h>

#define I2S_PORT            I2S_NUM_0
#define PIN_MIC_SCK         4
#define PIN_MIC_WS          5
#define PIN_MIC_SD          6

#define SAMPLE_RATE         16000
#define BLOCK_SIZE          256

int32_t rawSamples[BLOCK_SIZE];

void setup() {
  Serial.begin(115200);
  Serial0.begin(115200);
  delay(500);

  Serial.println("\n========================================================");
  Serial.println("  BUDDY AI — TEST 4: INMP441 Digital Microphone Check   ");
  Serial.println("========================================================");

  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4,
    .dma_buf_len = BLOCK_SIZE,
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

  Serial.println("[I2S] Driver started successfully on I2S0 @ 16kHz.");
  Serial.println("[INMP441] Speak, whisper, or snap your fingers near the microphone.");
  Serial.println("========================================================");
}

void loop() {
  size_t bytesRead = 0;
  esp_err_t res = i2s_read(I2S_PORT, (void*)rawSamples, sizeof(rawSamples), &bytesRead, pdMS_TO_TICKS(100));

  if (res == ESP_OK && bytesRead > 0) {
    size_t samples = bytesRead / sizeof(int32_t);
    int64_t sumSquares = 0;

    for (size_t i = 0; i < samples; i++) {
      int16_t val16 = (int16_t)(rawSamples[i] >> 14);
      sumSquares += (int64_t)val16 * val16;
    }

    float rms = sqrt((float)sumSquares / (float)samples);
    int bars = (int)(rms / 250.0f);
    if (bars > 30) bars = 30;

    Serial.printf("[Audio RMS: %5.0f] [", rms);
    for (int b = 0; b < 30; b++) {
      if (b < bars) Serial.print("=");
      else Serial.print(" ");
    }
    Serial.println("]");
  } else {
    Serial.println("[Warning] No data received from I2S DMA.");
  }

  delay(60);
}
