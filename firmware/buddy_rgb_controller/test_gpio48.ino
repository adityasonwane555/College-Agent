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
  // Instant visual feedback that CPU has entered setup()
  rgbLedWrite(RGB_LED_PIN, 40, 40, 40); // Soft white startup blip

  // Initialize primary Serial
  Serial.begin(115200);

#if ARDUINO_USB_CDC_ON_BOOT
  // When USB CDC On Boot is Enabled, Serial is Native USB.
  // Initialize Serial0 so logs also appear on the hardware UART/COM port!
  Serial0.begin(115200);
#endif

  delay(600);
  setColor(0, 0, 0);

  Serial.println("\nBUDDY ESP32-S3 GPIO 48 RGB LED Quick Test Started!");
#if ARDUINO_USB_CDC_ON_BOOT
  Serial0.println("\nBUDDY ESP32-S3 GPIO 48 RGB LED Quick Test Started!");
#endif
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
