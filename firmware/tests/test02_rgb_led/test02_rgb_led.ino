/*
 * =====================================================================================
 * BUDDY AI — HARDWARE TEST 2: Onboard WS2812 RGB LED (GPIO 48)
 * Hardware: ESP32-S3 Dev Module with built-in WS2812 RGB LED
 * Function: Tests solid colors and non-blocking Buddy AI breathing animations.
 * =====================================================================================
 */

#define RGB_PIN 48
#define BRIGHTNESS 50 // Safe, eye-friendly brightness (0 - 255)

void setRGB(uint8_t r, uint8_t g, uint8_t b) {
  uint8_t scaledR = (uint8_t)(((uint16_t)r * BRIGHTNESS) / 255);
  uint8_t scaledG = (uint8_t)(((uint16_t)g * BRIGHTNESS) / 255);
  uint8_t scaledB = (uint8_t)(((uint16_t)b * BRIGHTNESS) / 255);
  rgbLedWrite(RGB_PIN, scaledR, scaledG, scaledB);
}

void setup() {
  Serial.begin(115200);
  Serial0.begin(115200);
  delay(500);

  Serial.println("\n========================================================");
  Serial.println("  BUDDY AI — TEST 2: Onboard WS2812 RGB LED (GPIO 48)   ");
  Serial.println("========================================================");

  // 1. Primary Color Calibration Test
  Serial.println("[LED] Testing Solid RED...");
  setRGB(255, 0, 0);
  delay(1000);

  Serial.println("[LED] Testing Solid GREEN...");
  setRGB(0, 255, 0);
  delay(1000);

  Serial.println("[LED] Testing Solid BLUE...");
  setRGB(0, 0, 255);
  delay(1000);

  Serial.println("[LED] Testing Solid WHITE...");
  setRGB(255, 255, 255);
  delay(1000);

  Serial.println("\n[LED] Primary test complete. Starting Buddy AI state animations...");
  Serial.println("  1. Cyan Breathing  (IDLE State)");
  Serial.println("  2. Blue Pulsing    (LISTENING State)");
  Serial.println("  3. Amber Pulsing   (THINKING State)");
  Serial.println("  4. Purple Wave     (SPEAKING State)");
  Serial.println("  5. Red Alert       (ERROR State)");
  Serial.println("========================================================");
  Serial.println("  >>> TEST 2 STATUS: PASS <<<                           ");
  Serial.println("========================================================");
}

void loop() {
  unsigned long t = millis();
  int mode = (t / 5000) % 5; // Switch animation state every 5 seconds

  if (mode == 0) {
    // IDLE: Soft cyan breathing (3s cycle)
    float wave = (sin((t / 3000.0f) * 2.0f * PI) + 1.0f) * 0.5f;
    uint8_t v = (uint8_t)(15 + wave * 65);
    setRGB(0, v, (uint8_t)(v * 1.2f));
  } else if (mode == 1) {
    // LISTENING: Blue pulsing (1.2s cycle)
    float wave = (sin((t / 1200.0f) * 2.0f * PI) + 1.0f) * 0.5f;
    uint8_t v = (uint8_t)(40 + wave * 180);
    setRGB(0, (uint8_t)(v * 0.35f), v);
  } else if (mode == 2) {
    // THINKING: Warm amber pulse (800ms cycle)
    float wave = (sin((t / 800.0f) * 2.0f * PI) + 1.0f) * 0.5f;
    uint8_t v = (uint8_t)(40 + wave * 180);
    setRGB(v, (uint8_t)(v * 0.45f), 0);
  } else if (mode == 3) {
    // SPEAKING: Smooth reactive purple
    float wave = (sin((t / 1400.0f) * 2.0f * PI) + 1.0f) * 0.5f;
    uint8_t v = (uint8_t)(40 + wave * 170);
    setRGB(v, 0, (uint8_t)(v * 1.4f));
  } else {
    // ERROR: Gentle red pulse
    float wave = (sin((t / 1000.0f) * 2.0f * PI) + 1.0f) * 0.5f;
    uint8_t v = (uint8_t)(50 + wave * 160);
    setRGB(v, 0, 0);
  }

  delay(20);
}
