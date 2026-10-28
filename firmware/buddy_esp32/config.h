/*
 * =====================================================================================
 * BUDDY AI — ESP32-S3 COMPLETE HARDWARE CONFIGURATION
 * Target: ESP32-S3 N16R8 (16MB Flash, 8MB Octal PSRAM)
 * Project: BUDDY AI — College Reception Robot for APCOER Pune
 * =====================================================================================
 */

#pragma once

#include <Arduino.h>

// =====================================================================
// 1. PIN ALLOCATION MAP (Verified Conflict-Free)
// =====================================================================

// --- Onboard WS2812 RGB LED ---
#define PIN_RGB_LED             48      // Verified onboard WS2812 RGB LED pin

// --- ST7789 2.8-inch SPI TFT LCD (240x320) ---
#define PIN_TFT_SCLK            12      // SPI Serial Clock (SCL / SCK)
#define PIN_TFT_MOSI            11      // SPI Master Out Slave In (SDA / MOSI)
#define PIN_TFT_CS              10      // Chip Select (tie to GND if 7-pin module)
#define PIN_TFT_DC              9       // Data / Command Select
#define PIN_TFT_RST             13      // Hardware Reset (RES)
#define PIN_TFT_BLK             14      // Backlight Enable / PWM (or connect to 3.3V)

// --- INMP441 I²S Digital Microphone (I²S Controller 0 RX) ---
#define PIN_MIC_SCK             4       // I²S Serial Bit Clock (SCK / BCLK)
#define PIN_MIC_WS              5       // I²S Word Select / Left-Right Clock (WS / LRC)
#define PIN_MIC_SD              6       // I²S Serial Data Out from Mic to ESP32 (SD / DIN)

// --- MAX98357A I²S Class-D Amplifier (I²S Controller 1 TX) ---
#define PIN_AMP_BCLK            15      // I²S Bit Clock for audio output
#define PIN_AMP_LRC             16      // I²S Left-Right Frame Clock
#define PIN_AMP_DIN             17      // I²S Audio Data from ESP32 to Amp

// --- Optional Tactile Buttons & Indicator LEDs ---
#define PIN_BTN_ACTION          0       // Onboard BOOT button (or external button on GPIO 1)
#define PIN_BTN_AUX             1       // Auxiliary Push Button (with INPUT_PULLUP)
#define PIN_LED_STATUS          2       // External Status LED (via 220 ohm resistor)

// =====================================================================
// 2. WI-FI & NETWORK CONFIGURATION
// =====================================================================
#define WIFI_SSID_DEFAULT       "Aditya"
#define WIFI_PASS_DEFAULT       "Kamaataj"
#define HTTP_SERVER_PORT        80
#define API_TOKEN_DEFAULT       ""      // Optional shared secret; empty = open local subnet

// =====================================================================
// 3. AUDIO PARAMETERS
// =====================================================================
#define MIC_SAMPLE_RATE         16000   // 16 kHz optimal for Whisper / Speech Recognition
#define MIC_BITS_PER_SAMPLE     16      // 16-bit PCM
#define MIC_BUFFER_SIZE         512     // DMA read buffer size (samples)

#define SPK_SAMPLE_RATE         24000   // 24 kHz for Fish-TTS / Edge-TTS neural voice
#define SPK_BITS_PER_SAMPLE     16      // 16-bit PCM
#define SPK_DEFAULT_VOLUME      0.75f   // Default output volume scale (0.0 to 1.0)

// =====================================================================
// 4. DISPLAY PARAMETERS
// =====================================================================
#define TFT_WIDTH               240
#define TFT_HEIGHT              320
#define TFT_ROTATION            0       // 0 or 2 for Portrait mode
#define TFT_INVERT_COLORS       false   // false = standard black background (fixes Adafruit ST77XX_INVON default); true if inverted panel

// =====================================================================
// 5. LED PARAMETERS
// =====================================================================
#define RGB_MAX_BRIGHTNESS      60      // Safe, pleasant brightness (0 - 255)

// =====================================================================
// 6. DUAL-PORT UNIVERSAL SERIAL LOGGING
// =====================================================================
// Ensures output is logged regardless of whether Native USB CDC or
// Hardware UART (COM port) is selected.
#if ARDUINO_USB_CDC_ON_BOOT
  #define LOG_PRINT(x)          do { Serial.print(x);   Serial0.print(x);   } while(0)
  #define LOG_PRINTLN(x)        do { Serial.println(x); Serial0.println(x); } while(0)
  #define LOG_PRINTLN_EMPTY()   do { Serial.println();  Serial0.println();  } while(0)
  #define LOG_PRINTF(...)       do { Serial.printf(__VA_ARGS__); Serial0.printf(__VA_ARGS__); } while(0)
#else
  #define LOG_PRINT(x)          Serial.print(x)
  #define LOG_PRINTLN(x)        Serial.println(x)
  #define LOG_PRINTLN_EMPTY()   Serial.println()
  #define LOG_PRINTF(...)       Serial.printf(__VA_ARGS__)
#endif

// =====================================================================
// 7. ROBOT HARDWARE STATES
// =====================================================================
enum BuddyState {
  STATE_BOOTING,
  STATE_IDLE,
  STATE_LISTENING,
  STATE_THINKING,
  STATE_SPEAKING,
  STATE_INTERRUPTED,
  STATE_ERROR
};

inline const char* buddyStateToString(BuddyState state) {
  switch (state) {
    case STATE_BOOTING:     return "BOOTING";
    case STATE_IDLE:        return "IDLE";
    case STATE_LISTENING:   return "LISTENING";
    case STATE_THINKING:    return "THINKING";
    case STATE_SPEAKING:    return "SPEAKING";
    case STATE_INTERRUPTED: return "INTERRUPTED";
    case STATE_ERROR:       return "ERROR";
    default:                return "UNKNOWN";
  }
}
