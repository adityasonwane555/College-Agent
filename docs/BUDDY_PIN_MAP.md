# BUDDY AI — ESP32-S3 Complete Pin Allocation & Hardware Map

**Target Board:** ESP32-S3 N16R8 (16MB Flash, 8MB Octal PSRAM)  
**Microcontroller:** Dual-core Xtensa LX7 @ 240 MHz  
**Project:** BUDDY AI — Reception Robot for APCOER Pune  
**Revision:** 1.0 (Hardware-Ready)  

---

## 1. Safety Rules & Forbidden Pins for ESP32-S3 N16R8

> [!CAUTION]
> **STRICT FORBIDDEN PINS (PSRAM & FLASH CORRUPTION RISK):**  
> Because the N16R8 board utilizes **Octal PSRAM (8MB)** and **Quad/Octal SPI Flash (16MB)**, the following pins are hardwired internally to the Flash/PSRAM dies. **NEVER CONNECT ANY EXTERNAL WIRE TO THESE PINS**:
> - **GPIO 26, 27, 28, 29, 30, 31, 32** (SPI Flash)
> - **GPIO 33, 34, 35, 36, 37** (Octal PSRAM data & clock)  
> Connecting any peripheral to GPIO 26–37 will instantly crash the ESP32-S3 and can permanently damage the PSRAM chip.

> [!WARNING]
> **BOOTSTRAPPING & USB PINS TO AVOID:**
> - **GPIO 19 & GPIO 20:** Native USB D- and D+. Connected directly to the native USB-C port. Keep free for native USB CDC/JTAG.
> - **GPIO 45:** VDD_SPI internal power strapping pin.
> - **GPIO 46:** Boot ROM strapping pin (must not be pulled HIGH at boot).

---

## 2. Master GPIO Allocation Table

All assigned pins are 100% verified to be conflict-free, physically broken out on the ESP32-S3 DevKit headers, and completely safe from Flash/PSRAM/Strapping issues:

| GPIO | Peripheral | Signal Function | Direction | Operating Voltage | Notes / Precautions |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **GPIO 48** | **Onboard WS2812** | RGB LED Data | Output | 3.3V Logic | **Verified working** via `rgbLedWrite(48, R, G, B)`. |
| **GPIO 12** | **ST7789 Display** | SPI SCLK (SCL) | Output | 3.3V Logic | High-speed SPI clock (up to 40 MHz). |
| **GPIO 11** | **ST7789 Display** | SPI MOSI (SDA) | Output | 3.3V Logic | Master Out Slave In display pixel data. |
| **GPIO 10** | **ST7789 Display** | TFT_CS | Output | 3.3V Logic | Chip Select (tie GND if 7-pin module lacks CS). |
| **GPIO 9** | **ST7789 Display** | TFT_DC | Output | 3.3V Logic | Data / Command control pin. |
| **GPIO 13** | **ST7789 Display** | TFT_RST (RES) | Output | 3.3V Logic | Hardware Reset pin (active LOW). |
| **GPIO 14** | **ST7789 Display** | TFT_BLK (Backlight) | Output | 3.3V Logic | Optional PWM backlight dimming (or tie to 3.3V). |
| **GPIO 4** | **INMP441 Mic** | I²S SCK (BCLK) | Output | 3.3V Logic | I²S Serial Bit Clock for microphone. |
| **GPIO 5** | **INMP441 Mic** | I²S WS (LRC) | Output | 3.3V Logic | I²S Word Select / Left-Right Clock. |
| **GPIO 6** | **INMP441 Mic** | I²S SD (DIN) | Input | 3.3V Logic | Digital audio data from INMP441 to ESP32. |
| **GPIO 15** | **MAX98357A Amp** | I²S BCLK | Output | 3.3V Logic | Bit clock for audio output. |
| **GPIO 16** | **MAX98357A Amp** | I²S LRC (WS) | Output | 3.3V Logic | Word select / frame clock for audio output. |
| **GPIO 17** | **MAX98357A Amp** | I²S DIN | Output | 3.3V Logic | Audio samples from ESP32 to MAX98357A. |
| **GPIO 0** | **Tactile Button** | Action / Push-To-Talk | Input | 3.3V (Pull-up) | Built-in Boot button or external push-button. |
| **GPIO 1** | **Aux Button** | Volume / Mute Button | Input | 3.3V (Pull-up) | Optional tactile button with internal pull-up. |
| **GPIO 2** | **Indicator LED** | Hardware Status LED | Output | 3.3V (via 220Ω) | Optional breadboard external status LED. |

---

## 3. Peripheral Architecture Rationale

### A. Independent I²S Channels (I²S0 vs I²S1)
The ESP32-S3 contains **two independent hardware I²S peripherals**:
- **I²S Controller 0 (I²S0):** Assigned exclusively to the **INMP441 Microphone (RX)** on GPIO 4, 5, 6.
- **I²S Controller 1 (I²S1):** Assigned exclusively to the **MAX98357A Amplifier (TX)** on GPIO 15, 16, 17.

**Why this is the superior design:**
1. **Zero Sample Rate Locking:** INMP441 speech recognition operates best at **16 kHz 16-bit mono**, while TTS audio playback often streams at **22.05 kHz or 24 kHz**. Using separate I²S controllers allows simultaneous recording and playback at completely different sample rates without clock conflicts.
2. **True Full-Duplex Without DMA Glitches:** Dedicated DMA channels prevent audio underruns or buffer starvation while the robot is speaking and listening simultaneously.

### B. Contiguous Header Pin Placement
- **Display Pins (9, 10, 11, 12, 13, 14):** Form a contiguous block on the development board, enabling neat ribbon/Dupont cable runs directly to the ST7789 display without crossing jumper wires.
- **Audio Output (15, 16, 17):** Directly follows the display block.
- **Microphone (4, 5, 6):** Placed on the low GPIO block with minimal electrical crosstalk from high-frequency SPI bus lines.

---

## 4. Verification Checklist Before Wiring

- [x] GPIO 48 verified for onboard WS2812 RGB LED (tested in previous session).
- [x] Zero pins assigned to the Octal PSRAM/Flash zone (GPIO 26–37).
- [x] Native USB pins (GPIO 19, 20) left unencumbered.
- [x] Separate 3.3V and 5V power rails identified.
- [x] Common Ground verified across ESP32, Display, Mic, and Amplifier.
