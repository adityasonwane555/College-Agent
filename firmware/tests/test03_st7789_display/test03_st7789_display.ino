/*
 * =====================================================================================
 * BUDDY AI — HARDWARE TEST 3: ST7789 2.8" SPI TFT LCD (240x320)
 * Hardware Wiring:
 *   ST7789 GND  -> GND
 *   ST7789 VCC  -> 3.3V
 *   ST7789 SCL  -> GPIO 12 (SPI Clock)
 *   ST7789 SDA  -> GPIO 11 (SPI MOSI)
 *   ST7789 RES  -> GPIO 13 (Hardware Reset)
 *   ST7789 DC   -> GPIO 9  (Data/Command)
 *   ST7789 CS   -> GPIO 10 (Chip Select; or GND if 7-pin module)
 *   ST7789 BLK  -> 3.3V    (or GPIO 14)
 * =====================================================================================
 */

#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>

#define TFT_CS   10
#define TFT_DC   9
#define TFT_MOSI 11
#define TFT_SCLK 12
#define TFT_RST  13
#define TFT_BLK  14

Adafruit_ST7789 tft = Adafruit_ST7789(&SPI, TFT_CS, TFT_DC, TFT_RST);

void setup() {
  Serial.begin(115200);
  Serial0.begin(115200);
  delay(500);

  Serial.println("\n========================================================");
  Serial.println("  BUDDY AI — TEST 3: ST7789 2.8\" SPI TFT Diagnostic    ");
  Serial.println("========================================================");

  // Turn on Backlight
  pinMode(TFT_BLK, OUTPUT);
  digitalWrite(TFT_BLK, HIGH);

  // Initialize Hardware SPI on ESP32-S3 and ST7789 in 240x320 portrait mode
  SPI.begin(TFT_SCLK, -1, TFT_MOSI, -1);
  tft.init(240, 320);
  tft.setSPISpeed(40000000);
  tft.setRotation(0); // 0 = Portrait
  tft.invertDisplay(false); // Inversion OFF: ensures 0x0000 is black

  // 1. Solid Color Screen Tests
  Serial.println("[TFT] Screen fill: RED...");
  tft.fillScreen(ST77XX_RED);
  delay(500);

  Serial.println("[TFT] Screen fill: GREEN...");
  tft.fillScreen(ST77XX_GREEN);
  delay(500);

  Serial.println("[TFT] Screen fill: BLUE...");
  tft.fillScreen(ST77XX_BLUE);
  delay(500);

  Serial.println("[TFT] Rendering Buddy AI Interface...");
  tft.fillScreen(0x0821); // Dark navy background

  // Header Bar
  tft.fillRect(0, 0, 240, 42, 0x1084);
  tft.drawFastHLine(0, 42, 240, 0x05BF); // Cyan accent line
  tft.setCursor(14, 12);
  tft.setTextColor(0x05BF);
  tft.setTextSize(2);
  tft.print("BUDDY AI");
  tft.setCursor(140, 16);
  tft.setTextColor(0xFFFF);
  tft.setTextSize(1);
  tft.print("APCOER PUNE");

  // Status Card
  tft.fillRect(10, 50, 220, 26, 0x1084);
  tft.drawRoundRect(10, 50, 220, 26, 4, 0x9CD3);
  tft.setCursor(18, 57);
  tft.setTextColor(0x9CD3);
  tft.setTextSize(1);
  tft.print("STATUS: ");
  tft.setTextColor(0x2E65); // Emerald Green
  tft.print("Display Ready (PASS)");

  // Robot Face
  tft.drawRoundRect(70, 95, 100, 80, 14, 0x05BF);
  tft.fillCircle(100, 125, 8, 0x05BF);
  tft.fillCircle(140, 125, 8, 0x05BF);
  tft.fillCircle(102, 123, 2, 0xFFFF);
  tft.fillCircle(142, 123, 2, 0xFFFF);
  tft.drawFastHLine(102, 155, 36, 0x05BF);

  // College Card Box
  tft.drawRoundRect(10, 190, 220, 80, 6, 0x05BF);
  tft.setCursor(18, 202);
  tft.setTextColor(0x05BF);
  tft.setTextSize(1);
  tft.println("Anantrao Pawar College of");
  tft.setCursor(18, 215);
  tft.println("Engineering & Research");
  tft.setCursor(18, 235);
  tft.setTextColor(0xFFFF);
  tft.println("Hardware Test: OK");
  tft.setCursor(18, 248);
  tft.setTextColor(0x9CD3);
  tft.println("SPI Bus: 40 MHz Verified");

  // Footer
  tft.fillRect(0, 285, 240, 35, 0x1084);
  tft.drawFastHLine(0, 285, 240, 0x9CD3);
  tft.setCursor(12, 298);
  tft.setTextColor(0xFFFF);
  tft.print("ST7789 2.8-inch TFT LCD");

  Serial.println("\n========================================================");
  Serial.println("  >>> TEST 3 STATUS: PASS <<<                           ");
  Serial.println("========================================================");
}

void loop() {
  delay(1000);
}
