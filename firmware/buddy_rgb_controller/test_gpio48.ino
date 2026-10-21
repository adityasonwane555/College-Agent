/*
 * BUDDY AI - Quick GPIO 48 Hardware RGB Test
 * Cycles Red -> Green -> Blue -> Amber -> Magenta -> Cyan
 */
#include <Arduino.h>

#define RGB_LED_PIN 48
#define BRIGHTNESS 50 // Safe moderate level

void setColor(uint8_t r, uint8_t g, uint8_t b) {
  rgbLedWrite(RGB_LED_PIN, (r * BRIGHTNESS) / 255, (g * BRIGHTNESS) / 255, (b * BRIGHTNESS) / 255);
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("BUDDY ESP32-S3 GPIO 48 RGB LED Quick Test");
}

void loop() {
  Serial.println("RED (ERROR state)");
  setColor(255, 0, 0);
  delay(1000);

  Serial.println("AMBER (THINKING state)");
  setColor(255, 140, 0);
  delay(1000);

  Serial.println("BLUE (LISTENING state)");
  setColor(0, 40, 255);
  delay(1000);

  Serial.println("PURPLE / MAGENTA (SPEAKING state)");
  setColor(220, 0, 200);
  delay(1000);

  Serial.println("CYAN (IDLE state)");
  setColor(0, 180, 255);
  delay(1000);
}
