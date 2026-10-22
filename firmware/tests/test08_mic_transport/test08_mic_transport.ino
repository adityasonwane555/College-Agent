/*
 * =====================================================================================
 * BUDDY AI — HARDWARE TEST 8: Microphone Audio Transport (ESP32 -> PC)
 * Captures 16kHz 16-bit mono audio from INMP441 and serves it as a downloadable WAV file.
 * =====================================================================================
 */

#include <WiFi.h>
#include <WebServer.h>
#include <driver/i2s.h>

const char* WIFI_SSID = "Aditya";
const char* WIFI_PASS = "Kamaataj";

#define I2S_PORT        I2S_NUM_0
#define PIN_MIC_SCK     4
#define PIN_MIC_WS      5
#define PIN_MIC_SD      6
#define SAMPLE_RATE     16000

WebServer server(80);

// Simple WAV header generator
void createWavHeader(uint8_t* header, uint32_t totalDataLen) {
  uint32_t totalFileLen = totalDataLen + 36;
  uint32_t byteRate = SAMPLE_RATE * 2; // 16-bit mono = 2 bytes/sec * sample_rate

  header[0] = 'R'; header[1] = 'I'; header[2] = 'F'; header[3] = 'F';
  header[4] = (uint8_t)(totalFileLen & 0xFF);
  header[5] = (uint8_t)((totalFileLen >> 8) & 0xFF);
  header[6] = (uint8_t)((totalFileLen >> 16) & 0xFF);
  header[7] = (uint8_t)((totalFileLen >> 24) & 0xFF);
  header[8] = 'W'; header[9] = 'A'; header[10] = 'V'; header[11] = 'E';
  header[12] = 'f'; header[13] = 'm'; header[14] = 't'; header[15] = ' ';
  header[16] = 16; header[17] = 0; header[18] = 0; header[19] = 0; // Subchunk1Size (16 for PCM)
  header[20] = 1; header[21] = 0; // AudioFormat (1 = PCM)
  header[22] = 1; header[23] = 0; // NumChannels (1 = Mono)
  header[24] = (uint8_t)(SAMPLE_RATE & 0xFF);
  header[25] = (uint8_t)((SAMPLE_RATE >> 8) & 0xFF);
  header[26] = (uint8_t)((SAMPLE_RATE >> 16) & 0xFF);
  header[27] = (uint8_t)((SAMPLE_RATE >> 24) & 0xFF);
  header[28] = (uint8_t)(byteRate & 0xFF);
  header[29] = (uint8_t)((byteRate >> 8) & 0xFF);
  header[30] = (uint8_t)((byteRate >> 16) & 0xFF);
  header[31] = (uint8_t)((byteRate >> 24) & 0xFF);
  header[32] = 2; header[33] = 0; // BlockAlign (2 bytes)
  header[34] = 16; header[35] = 0; // BitsPerSample (16 bits)
  header[36] = 'd'; header[37] = 'a'; header[38] = 't'; header[39] = 'a';
  header[40] = (uint8_t)(totalDataLen & 0xFF);
  header[41] = (uint8_t)((totalDataLen >> 8) & 0xFF);
  header[42] = (uint8_t)((totalDataLen >> 16) & 0xFF);
  header[43] = (uint8_t)((totalDataLen >> 24) & 0xFF);
}

void setup() {
  Serial.begin(115200);
  Serial0.begin(115200);
  delay(500);

  Serial.println("\n========================================================");
  Serial.println("  BUDDY AI — TEST 8: Microphone Audio Transport         ");
  Serial.println("========================================================");

  // Initialize I2S0 RX for INMP441
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4,
    .dma_buf_len = 512,
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

  i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_PORT, &pin_config);

  // Connect to Wi-Fi
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.printf("\n[Wi-Fi] Ready: http://%s/\n", WiFi.localIP().toString().c_str());

  // Record endpoint: records 3 seconds and downloads as WAV
  server.on("/api/mic/record", HTTP_GET, []() {
    Serial.println("[Mic] Recording 3 seconds of audio...");
    const size_t totalSamples = SAMPLE_RATE * 3; // 3 seconds = 48,000 samples
    int16_t* pcm16 = (int16_t*)ps_malloc(totalSamples * sizeof(int16_t));
    if (!pcm16) pcm16 = (int16_t*)malloc(totalSamples * sizeof(int16_t));

    if (!pcm16) {
      server.send(500, "text/plain", "Out of memory");
      return;
    }

    int32_t dmaChunk[256];
    size_t samplesCaptured = 0;

    while (samplesCaptured < totalSamples) {
      size_t bytesRead = 0;
      i2s_read(I2S_PORT, dmaChunk, sizeof(dmaChunk), &bytesRead, pdMS_TO_TICKS(100));
      size_t count = bytesRead / sizeof(int32_t);
      for (size_t i = 0; i < count && samplesCaptured < totalSamples; i++) {
        pcm16[samplesCaptured++] = (int16_t)(dmaChunk[i] >> 14);
      }
    }

    uint8_t wavHeader[44];
    createWavHeader(wavHeader, totalSamples * sizeof(int16_t));

    WiFiClient client = server.client();
    server.sendHeader("Content-Type", "audio/wav");
    server.sendHeader("Content-Disposition", "attachment; filename=\"buddy_mic_test.wav\"");
    server.sendHeader("Connection", "close");
    server.setContentLength(44 + totalSamples * sizeof(int16_t));
    server.send(200, "audio/wav", "");

    client.write(wavHeader, 44);
    client.write((const uint8_t*)pcm16, totalSamples * sizeof(int16_t));

    free(pcm16);
    Serial.println("[Mic] 3-second WAV file streamed to client successfully.");
  });

  server.begin();
  Serial.printf("Download a 3-second recording by opening in browser:\n  http://%s/api/mic/record\n", WiFi.localIP().toString().c_str());
  Serial.println("========================================================");
}

void loop() {
  server.handleClient();
  delay(2);
}
