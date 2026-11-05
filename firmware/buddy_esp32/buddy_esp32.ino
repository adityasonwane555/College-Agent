/*
 * =====================================================================================
 * BUDDY AI — Master ESP32-S3 Hardware Controller
 * 
 * Target Board: ESP32-S3 N16R8 (ESP32S3 Dev Module profile)
 * Features:
 *   - Onboard WS2812 RGB LED (GPIO 48)
 *   - ST7789 2.8" SPI TFT LCD (240x320)
 *   - INMP441 I²S Digital Microphone (I2S0)
 *   - MAX98357A I²S Class-D Amplifier (I2S1) & Passive Speaker
 *   - Wi-Fi REST WebServer on Port 80
 *   - Push-to-Talk Button (GPIO 1 / GPIO 0)
 * 
 * Project: BUDDY AI — College Reception Robot for APCOER Pune
 * =====================================================================================
 */

#include "config.h"
#include "rgb_manager.h"
#include "display_manager.h"
#include "microphone_manager.h"
#include "audio_output.h"
#include "wifi_manager.h"

// Button state tracking (falling-edge detection with debounce)
bool lastButtonReading = HIGH;
bool stableButtonState = HIGH;
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50;

void setup() {
  // 1. Dual-Port Universal Serial Initialization
  Serial.begin(115200);
  Serial0.begin(115200);
  delay(500);

  LOG_PRINTLN("\n========================================================");
  LOG_PRINTLN("  BUDDY AI — ESP32-S3 Hardware Controller Starting...  ");
  LOG_PRINTLN("  APCOER College Reception Robot                       ");
  LOG_PRINTLN("========================================================");

  // 2. Initialize Onboard RGB LED (GPIO 48)
  rgbManager.begin();
  rgbManager.setState(STATE_BOOTING);

  // 3. Initialize ST7789 2.8" SPI Display
  displayManager.begin();
  displayManager.setState(STATE_BOOTING);

  // 4. Initialize MAX98357A Audio Amplifier (I2S1)
  audioOutput.begin(SPK_SAMPLE_RATE);

  // 5. Initialize INMP441 Digital Microphone (I2S0)
  microphoneManager.begin();

  // 6. Configure Optional Push-to-Talk Button
#if defined(PIN_BTN_AUX) && (PIN_BTN_AUX >= 0)
  pinMode(PIN_BTN_AUX, INPUT_PULLUP);
#endif
  if (PIN_BTN_ACTION >= 0) {
    pinMode(PIN_BTN_ACTION, INPUT_PULLUP);
  }

  // 7. Start Wi-Fi & WebServer
  wifiManager.begin(WIFI_SSID_DEFAULT, WIFI_PASS_DEFAULT);

  // 8. Play Startup Chime
  audioOutput.playChime();

  LOG_PRINTLN("[Setup] All hardware subsystems initialized successfully.");
}

void loop() {
  // Non-blocking subsystem updates
  wifiManager.update();
  rgbManager.update();
  displayManager.update();

  // Push-to-Talk Button Monitoring (clean falling-edge trigger)
  // Ensures push-to-talk only fires ONCE per physical button press (transition from HIGH to LOW).
  // Prevents persistent clamp in STATE_LISTENING if the button is held or an input pin floats.
  int reading = HIGH;
  if (PIN_BTN_ACTION >= 0) {
    reading = digitalRead(PIN_BTN_ACTION);
  }
#if defined(PIN_BTN_AUX) && (PIN_BTN_AUX >= 0)
  reading = reading && digitalRead(PIN_BTN_AUX);
#endif

  if (reading != lastButtonReading) {
    lastDebounceTime = millis();
    lastButtonReading = reading;
  }

  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (reading != stableButtonState) {
      stableButtonState = reading;
      if (stableButtonState == LOW) {
        LOG_PRINTLN("[Button] Push-to-Talk activated (falling edge)!");
        rgbManager.setState(STATE_LISTENING);
        displayManager.setState(STATE_LISTENING);
        displayManager.setMessage("Listening", "Speak your question now...");
      }
    }
  }

  // Real-time microphone audio energy monitoring
  if (rgbManager.getState() == STATE_LISTENING) {
    int16_t sampleBuf[64];
    size_t count = microphoneManager.readSamples(sampleBuf, 64);
    if (count > 0) {
      float energy = microphoneManager.getRecentEnergy();
      displayManager.setAudioLevel(energy);
    }
  }

  delay(2); // Yield to FreeRTOS scheduler
}
