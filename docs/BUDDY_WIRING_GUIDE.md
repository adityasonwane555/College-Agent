# BUDDY AI — Master Hardware Wiring Guide

**Target Hardware:** ESP32-S3 N16R8 Dev Module  
**Project:** BUDDY AI — College Reception Robot for APCOER Pune  
**Document Revision:** 1.0 (Hardware-Ready)  

---

## 1. Safety Rules & Golden Principles

> [!IMPORTANT]
> **READ BEFORE PLUGGING IN ANY JUMPER WIRE:**
> 1. **ALWAYS DISCONNECT POWER (USB cable unplugged)** when plugging or moving Dupont wires on the breadboard.
> 2. **NEVER CONNECT 5V TO AN ESP32 GPIO PIN.** The ESP32-S3 is strictly a **3.3V logic** device. Any 5V signal applied to a GPIO will destroy the chip.
> 3. **INMP441 MICROPHONE MUST BE POWERED FROM 3.3V ONLY.** Connecting VDD to 5V will instantly fry the micro-electromechanical (MEMS) sensor.
> 4. **SPEAKER OUTPUTS (SPK+ and SPK-) ARE DIFFERENTIAL (BTL).**
>    - Connect speaker wires ONLY to the terminal blocks of the MAX98357A.
>    - **NEVER** connect SPK+ or SPK- to GND, VCC, or to each other.
>    - Doing so will instantly blow the output MOSFET bridge in the MAX98357A amplifier IC.
> 5. **KEEP COMMON GROUND CONNECTED:** All GND pins (ESP32 GND, Display GND, Mic GND, Amp GND) must connect to the breadboard GND rail to maintain a common voltage reference.

---

## 2. Master Wiring Table

| Section | Component Pin Label | ESP32-S3 Connection | Wire Type | Signal Direction | Voltage Level | Primary Purpose | Key Precautions |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | **ST7789 GND** | **GND Rail** | Female-to-Male | Power (0V) | 0V | Ground reference | Ensure firm ground connection. |
| **A** | **ST7789 VCC** | **3.3V Rail** | Female-to-Male | Power (+3.3V) | 3.3V DC | Display logic & panel power | Safe with 3.3V. |
| **A** | **ST7789 SCL (SCK)** | **GPIO 12** | Female-to-Male | ESP32 → Display | 3.3V Logic | SPI Clock | Keep wire under 15 cm. |
| **A** | **ST7789 SDA (MOSI)**| **GPIO 11** | Female-to-Male | ESP32 → Display | 3.3V Logic | SPI Data Out | Master Out Slave In. |
| **A** | **ST7789 RES (RST)** | **GPIO 13** | Female-to-Male | ESP32 → Display | 3.3V Logic | Hardware Reset | Active LOW pulse resets panel. |
| **A** | **ST7789 DC** | **GPIO 9** | Female-to-Male | ESP32 → Display | 3.3V Logic | Command / Data Select | HIGH = Data, LOW = Command. |
| **A** | **ST7789 CS** | **GPIO 10** (or GND) | Female-to-Male | ESP32 → Display | 3.3V Logic | Chip Select | Tie to GND if 7-pin module. |
| **A** | **ST7789 BLK (LEDA)**| **GPIO 14** (or 3.3V)| Female-to-Male | ESP32 → Display | 3.3V Logic | Backlight enable / PWM | Connect to 3.3V for always-on. |
| **B** | **INMP441 VDD** | **3.3V Rail** | Female-to-Male | Power (+3.3V) | 3.3V DC | Mic core power | **NEVER connect to 5V!** |
| **B** | **INMP441 GND** | **GND Rail** | Female-to-Male | Power (0V) | 0V | Ground reference | Common reference. |
| **B** | **INMP441 SCK** | **GPIO 4** | Female-to-Male | ESP32 → Mic | 3.3V Logic | I²S Serial Bit Clock | I²S Controller 0 Clock. |
| **B** | **INMP441 WS** | **GPIO 5** | Female-to-Male | ESP32 → Mic | 3.3V Logic | I²S Word Select / LRC | Frame synchronisation. |
| **B** | **INMP441 SD** | **GPIO 6** | Female-to-Male | Mic → ESP32 | 3.3V Logic | I²S Audio Data Input | Digital audio stream from mic. |
| **B** | **INMP441 L/R** | **GND Rail** | Female-to-Male | Config | 0V | Left/Right Channel Select | Tied to GND for Left channel mono. |
| **C** | **MAX98357A VIN** | **5V (VBUS / VIN)** | Female-to-Male | Power (+5V) | 5V DC | Amplifier power rail | Power from 5V for loud clear audio. |
| **C** | **MAX98357A GND** | **GND Rail** | Female-to-Male | Power (0V) | 0V | Ground reference | Common ground with ESP32. |
| **C** | **MAX98357A BCLK**| **GPIO 15** | Female-to-Male | ESP32 → Amp | 3.3V Logic | I²S Bit Clock | I²S Controller 1 Clock. |
| **C** | **MAX98357A LRC** | **GPIO 16** | Female-to-Male | ESP32 → Amp | 3.3V Logic | I²S Left/Right Clock | Frame clock. |
| **C** | **MAX98357A DIN** | **GPIO 17** | Female-to-Male | ESP32 → Amp | 3.3V Logic | I²S Audio Data Output | Audio stream from ESP32 to Amp. |
| **C** | **MAX98357A SD_MODE**| **3.3V Rail** | Female-to-Male | Config | 3.3V Logic | Shutdown / Mode Enable | **CRUCIAL:** Must be tied to 3.3V to wake chip from shutdown! |
| **D** | **Speaker Wire 1** | **MAX98357A SPK+** | Bare wire to block | Amp → Speaker | Analog BTL | Audio signal positive | Screw tightly into terminal. |
| **D** | **Speaker Wire 2** | **MAX98357A SPK-** | Bare wire to block | Amp → Speaker | Analog BTL | Audio signal negative | **NEVER connect to GND!** |
| **E** | **Onboard WS2812** | **GPIO 48 (Internal)**| Onboard trace | ESP32 → LED | 3.3V Logic | RGB Animation & States | Pre-wired on PCB. |
| **F** | **Tactile Push Button**| **GPIO 0** (or GPIO 1)| Male-to-Male | Switch → ESP32 | 3.3V (Pull-up)| Push-to-Talk / Wake | Use internal `INPUT_PULLUP`. |
| **G** | **External LED** | **GPIO 2 via 220Ω** | Male-to-Male | ESP32 → LED | 3.3V Logic | Hardware Indicator | Resistor in series required. |

---

## 3. Step-by-Step Connection Guide by Subsystem

### Section A: ST7789 2.8-inch SPI TFT LCD (240 × 320)
1. **GND** → Connect to the breadboard **GND rail** with a black wire.
2. **VCC** → Connect to the breadboard **3.3V rail** with a red wire.
3. **SCL (or SCK)** → Connect to **ESP32 GPIO 12**.
4. **SDA (or MOSI)** → Connect to **ESP32 GPIO 11**.
5. **RES (or RST)** → Connect to **ESP32 GPIO 13**.
6. **DC** → Connect to **ESP32 GPIO 9**.
7. **CS (Chip Select)**:
   - If your module has 8 pins including **CS**: Connect to **ESP32 GPIO 10**.
   - If your module has 7 pins (no CS pin): The CS is tied internally to ground on the PCB.
8. **BLK (Backlight / LEDA)**:
   - Connect to **ESP32 GPIO 14** if software dimming is desired, OR connect directly to the **3.3V rail** for constant full brightness.

### Section B: INMP441 Omnidirectional I²S Microphone
1. **VDD** → Connect to the breadboard **3.3V rail**. (*DO NOT CONNECT TO 5V*).
2. **GND** → Connect to the breadboard **GND rail**.
3. **SCK** → Connect to **ESP32 GPIO 4**.
4. **WS** → Connect to **ESP32 GPIO 5**.
5. **SD** → Connect to **ESP32 GPIO 6**.
6. **L/R** → Connect to the breadboard **GND rail** with a short jumper wire (sets Left channel mono).

### Section C: MAX98357A I²S Class-D Amplifier
1. **VIN** → Connect to the **ESP32 5V (or VBUS) pin**.
   *(5V supplies enough power for clear, dynamic speech without clipping).*
2. **GND** → Connect to the breadboard **GND rail**.
3. **BCLK** → Connect to **ESP32 GPIO 15**.
4. **LRC (WS)** → Connect to **ESP32 GPIO 16**.
5. **DIN** → Connect to **ESP32 GPIO 17**.
6. **SD_MODE (Shutdown)**: Connect to the **3.3V rail** (or directly to ESP32 3.3V pin).
   *(CRUCIAL: Most breakout boards have a 1MΩ pull-down resistor to GND; leaving SD_MODE floating keeps the amplifier in permanent SHUTDOWN mode with zero sound. Connecting SD_MODE to 3.3V wakes the amplifier up and selects Left channel audio).*
7. **GAIN**: Leave unconnected for default $9\text{ dB}$ gain (clean speech volume).

### Section D: Passive 4Ω or 8Ω Speaker
1. Strip $5\text{ mm}$ of insulation from both speaker leads.
2. Insert one lead into the **SPK+** screw terminal of the MAX98357A module and tighten the screw.
3. Insert the other lead into the **SPK-** screw terminal of the MAX98357A module and tighten the screw.
4. **Critical check:** Ensure no stray copper strands touch the adjacent terminal or the PCB ground plane.

### Section E: Onboard WS2812 RGB LED
- **GPIO 48:** Hardwired directly on the ESP32-S3 DevKit PCB. No external jumper wire needed!

### Section F: Optional Tactile Push Button (Push-to-Talk)
1. Place a momentary 2-pin or 4-pin tactile push button across the center divider of the breadboard.
2. Connect one terminal to **ESP32 GPIO 1** (or GPIO 0).
3. Connect the opposite diagonal terminal to the **GND rail**.
4. The firmware uses the internal ESP32 pull-up resistor (`pinMode(1, INPUT_PULLUP)`), so no external resistor is required.

### Section G: Optional External Status LED
1. Insert the long leg (anode, positive) of a 3mm or 5mm LED into a breadboard row.
2. Connect that row to a **220 Ω resistor**, and connect the other end of the resistor to **ESP32 GPIO 2**.
3. Connect the short leg (cathode, negative) of the LED directly to the **GND rail**.

---

## 4. Connection Inspection & Sanity Verification

Before powering up the system:
1. **Tug Test:** Lightly pull each Dupont wire to confirm it is firmly seated in the header and breadboard.
2. **Short Circuit Check:** If you have a digital multimeter, set it to continuity/resistance mode:
   - Measure resistance between **3.3V rail** and **GND rail**. It must be $>10\text{ k}\Omega$ (not shorted).
   - Measure resistance between **5V rail** and **GND rail**. It must be $>10\text{ k}\Omega$.
   - Measure resistance between **SPK+** and **GND**. It must be open circuit (no continuity).
   - Measure resistance between **SPK-** and **GND**. It must be open circuit (no continuity).
3. **Power-Up Sequence:**
   - Plug the USB-C cable into the **COM port** of the ESP32-S3 board.
   - Confirm the red power LED on the ESP32-S3 lights up.
   - Confirm neither the MAX98357A nor the INMP441 becomes hot to the touch.
