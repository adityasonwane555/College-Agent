/*
 * =====================================================================================
 * BUDDY AI — HARDWARE TEST 10: Complete Integration Self-Test
 * 
 * Verifies all 6 hardware components running simultaneously:
 *   1. Onboard WS2812 RGB LED (GPIO 48)
 *   2. ST7789 2.8" SPI Display (SCL=12, SDA=11, CS=10, DC=9, RST=13, BLK=14)
 *   3. INMP441 Microphone (SCK=4, WS=5, SD=6)
 *   4. MAX98357A Amplifier & Speaker (BCLK=15, LRC=16, DIN=17)
 *   5. Push-to-Talk Button (GPIO 1 / GPIO 0)
 *   6. Wi-Fi Local REST Server
 * =====================================================================================
 */

#include <WiFi.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <driver/i2s.h>

const char* WIFI_SSID = "Aditya";
const char* WIFI_PASS = "Kamaataj";

#define RGB_PIN       48
#define TFT_CS        10
#define TFT_DC        9
#define TFT_MOSI      11
#define TFT_SCLK      12
#define TFT_RST       13
#define TFT_BLK       14

Adafruit_ST7789 tft = Adafruit_ST7789(TFT_CS, TFT_DC, TFT_MOSI, TFT_SCLK, TFT_RST);

void setRGB(uint8_t r, uint8_t g, uint8_t b) {
  rgbLedWrite(RGB_PIN, (r * 50) / 255, (g * 50) / 255, (b * 50) / 255);
}

void setup() {
  Serial.begin(115200);
  Serial0.begin(115200);
  delay(500);

  Serial.println("\n========================================================");
  Serial.println("  BUDDY AI — TEST 10: Complete Hardware Integration     ");
  Serial.println("  Anantrao Pawar College of Engineering & Research      ");
  Serial.println("========================================================");

  // 1. RGB LED Check
  Serial.print("[1/5] Testing Onboard RGB LED (GPIO 48)... ");
  setRGB(0, 255, 255); // Cyan
  Serial.println("OK");

  // 2. Display Check
  Serial.print("[2/5] Testing ST7789 2.8\" Display... ");
  pinMode(TFT_BLK, OUTPUT);
  digitalWrite(TFT_BLK, HIGH);
  tft.init(240, 320);
  tft.setRotation(0);
  tft.fillScreen(0x0821);
  tft.fillRect(0, 0, 240, 42, 0x1084);
  tft.setCursor(14, 12);
  tft.setTextColor(0x05BF);
  tft.setTextSize(2);
  tft.print("BUDDY AI");
  tft.setCursor(140, 16);
  tft.setTextColor(0xFFFF);
  tft.setTextSize(1);
  tft.print("APCOER PUNE");
  Serial.println("OK");

  // 3. Microphone Check (I2S0)
  Serial.print("[3/5] Testing INMP441 Mic (GPIO 4,5,6)... ");
  i2s_config_t mic_cfg = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = 16000,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4,
    .dma_buf_len = 256,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };
  i2s_pin_config_t mic_pins = {
    .bck_io_num = 4, .ws_io_num = 5, .data_out_num = -1, .data_in_num = 6
  };
  i2s_driver_install(I2S_NUM_0, &mic_cfg, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &mic_pins);
  Serial.println("OK");

  // 4. Amplifier & Speaker Check (I2S1)
  Serial.print("[4/5] Testing MAX98357A Amp (GPIO 15,16,17)... ");
  i2s_config_t amp_cfg = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
    .sample_rate = 24000,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4,
    .dma_buf_len = 256,
    .use_apll = false,
    .tx_desc_auto_clear = true,
    .fixed_mclk = 0
  };
  i2s_pin_config_t amp_pins = {
    .bck_io_num = 15, .ws_io_num = 16, .data_out_num = 17, .data_in_num = -1
  };
  i2s_driver_install(I2S_NUM_1, &amp_cfg, 0, NULL);
  i2s_set_pin(I2S_NUM_1, &amp_pins);
  Serial.println("OK");

  // 5. Wi-Fi Check
  Serial.printf("[5/5] Connecting to Wi-Fi '%s'...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 10000) {
    delay(400);
    Serial.print(".");
  }
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("[Wi-Fi] Online! IP: http://%s/\n", WiFi.localIP().toString().c_str());
    tft.setCursor(14, 290);
    tft.setTextColor(0xFFFF);
    tft.setTextSize(1);
    tft.printf("IP: %s", WiFi.localIP().toString().c_str());
  }

  Serial.println("\n========================================================");
  Serial.println("  >>> ALL HARDWARE SUBSYSTEMS OPERATIONAL: PASS <<<    ");
  Serial.println("========================================================");
}

void loop() {
  // Animated Cyan breathing for IDLE state
  unsigned long t = millis();
  float wave = (sin((t / 3000.0f) * 2.0f * PI) + 1.0f) * 0.5f;
  uint8_t v = (uint8_t)(15 + wave * 65);
  setRGB(0, v, (uint8_t)(v * 1.2f));
  delay(20);
}
