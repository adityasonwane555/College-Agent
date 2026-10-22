/*
 * =====================================================================================
 * BUDDY AI — HARDWARE TEST 9: Speaker Audio Streaming (PC -> ESP32)
 * Receives raw 24kHz/16kHz 16-bit PCM chunks over HTTP POST and streams to MAX98357A.
 * =====================================================================================
 */

#include <WiFi.h>
#include <WebServer.h>
#include <driver/i2s.h>

const char* WIFI_SSID = "Aditya";
const char* WIFI_PASS = "Kamaataj";

#define I2S_PORT        I2S_NUM_1
#define PIN_AMP_BCLK    15
#define PIN_AMP_LRC     16
#define PIN_AMP_DIN     17
#define SAMPLE_RATE     24000

WebServer server(80);

void setup() {
  Serial.begin(115200);
  Serial0.begin(115200);
  delay(500);

  Serial.println("\n========================================================");
  Serial.println("  BUDDY AI — TEST 9: Speaker Audio Streaming (PC->ESP32)");
  Serial.println("========================================================");

  // Initialize I2S1 TX for MAX98357A
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT,
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

  i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_PORT, &pin_config);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.printf("\n[Wi-Fi] Ready: http://%s/\n", WiFi.localIP().toString().c_str());

  // Audio stream endpoint
  server.on("/api/speak/raw", HTTP_POST, []() {
    if (!server.hasArg("plain")) {
      server.send(400, "text/plain", "Missing audio data");
      return;
    }

    String body = server.arg("plain");
    const int16_t* monoSamples = (const int16_t*)body.c_str();
    size_t sampleCount = body.length() / sizeof(int16_t);

    Serial.printf("[Audio] Streaming %u samples (%u bytes) to speaker...\n", sampleCount, body.length());

    // Interleave mono into stereo frames for MAX98357A
    const size_t chunkSize = 256;
    int16_t stereoChunk[chunkSize * 2];

    for (size_t i = 0; i < sampleCount; i += chunkSize) {
      size_t count = min(chunkSize, sampleCount - i);
      for (size_t c = 0; c < count; c++) {
        int16_t val = (int16_t)(monoSamples[i + c] * 0.7f); // 70% volume
        stereoChunk[c * 2]     = val;
        stereoChunk[c * 2 + 1] = val;
      }
      size_t bytesWritten = 0;
      i2s_write(I2S_PORT, stereoChunk, count * 2 * sizeof(int16_t), &bytesWritten, pdMS_TO_TICKS(100));
    }

    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", "{\"ok\":true,\"played\":true}");
  });

  server.begin();
  Serial.println("[Ready] Send raw audio using scripts/test_speaker_stream.py");
  Serial.println("========================================================");
}

void loop() {
  server.handleClient();
  delay(2);
}
