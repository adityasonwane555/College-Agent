# BUDDY AI — Hardware Troubleshooting & Diagnostic Guide

**Project:** BUDDY AI — College Reception Robot for APCOER Pune  
**Target Board:** ESP32-S3 N16R8  
**Document Revision:** 1.0 (Hardware-Ready)  

---

## 1. Fast Diagnostic Matrix

| Symptom | Primary Suspect | Quick Solution |
| :--- | :--- | :--- |
| **ESP32 repeatedly reboots (Brownout)** | Weak USB cable or power supply | Use 5V 2A adapter; connect $220\mu\text{F}$ capacitor across 5V and GND. |
| **ST7789 display is completely black** | Backlight pin disconnected | Connect **BLK** to **3.3V** to force backlight ON. |
| **ST7789 display is pure white** | SPI SCLK / MOSI / DC inverted | Verify SCL=GPIO 12, SDA=GPIO 11, DC=GPIO 9, RES=GPIO 13. |
| **ST7789 colors are inverted** | Panel driver offset (`invertDisplay`) | Set `tft.invertDisplay(true)` or `false` in initialization. |
| **INMP441 reads only zeros (silence)** | L/R pin floating or SCK/WS swapped | Tie **L/R to GND** firmly; swap GPIO 4 (SCK) and GPIO 5 (WS). |
| **INMP441 reads constant loud static** | Powered from 5V or noisy ground | **Strictly power from 3.3V**; use short jumper wires ($<15\text{ cm}$). |
| **MAX98357A speaker produces no sound** | VIN not powered or SPK disconnected | Connect VIN to **5V**; check speaker screws; check BCLK=15, LRC=16, DIN=17. |
| **MAX98357A makes a clicking sound** | Buffer underrun or power dipping | Add $100\mu\text{F}$ capacitor across 5V and GND; increase DMA buffer size. |
| **Onboard RGB LED doesn't light up** | GPIO pin mismatch | Board uses **GPIO 48**; verify `rgbLedWrite(48, R, G, B)`. |

---

## 2. In-Depth Subsystem Troubleshooting

### A. ST7789 TFT Display

#### 1. White Screen / No Graphic Display
- **Check 1: Power supply:** Measure voltage between display VCC and GND pins with a voltmeter. It must be between $3.25\text{V}$ and $3.35\text{V}$.
- **Check 2: Reset pulse:** Ensure the **RES** pin is connected to **GPIO 13**. If RES is floating, the display controller remains in an uninitialized reset state.
- **Check 3: Chip Select (CS):** Many 7-pin modules omit the CS pin and ground it internally. If your module has an explicit CS pin, it **must** be connected to **GPIO 10** (or tied directly to the **GND** rail).
- **Check 4: Data/Command (DC) pin:** If DC is swapped with SCL or SDA, the display will receive pixel data as command registers and reject the entire frame. Verify DC is wired to **GPIO 9**.

#### 2. Display Colors Are Inverted (e.g. Black appears White, Blue appears Yellow)
- ST7789 panels are manufactured in both normally-black and normally-white variants.
- In `display_manager.cpp`, toggle the inversion setting:
  ```cpp
  tft.invertDisplay(true); // Switch between true and false to correct color mapping
  ```

#### 3. Image is Shifted / Pixels Cut Off by 20 to 80 Pixels
- Some 2.8" ST7789 displays use an internal 240x320 RAM matrix but with offset starting rows.
- If the screen content is shifted downwards, add row/column offsets in the initialization call:
  ```cpp
  tft.init(240, 320);
  tft.setRotation(0); // 0 or 2 for portrait
  ```

---

### B. INMP441 I²S Digital Microphone

#### 1. Zero Audio Data / RMS Energy Always 0
- **L/R Pin Check:** If the **L/R** pin is left floating, the microphone output will be undefined. Connect **L/R to GND** with a jumper wire to select the Left Channel.
- **Clock Verification:** Use `test04_inmp441_mic.ino`. If the DMA queue reports timeout, verify:
  - **SCK (Serial Clock)** is connected to **GPIO 4**.
  - **WS (Word Select)** is connected to **GPIO 5**.
  - **SD (Serial Data)** is connected to **GPIO 6**.

#### 2. Static / Buzzing / High Floor Noise
- **VDD Check:** Confirm that VDD is connected to the **3.3V rail**, NOT 5V!
- **Ground Loop:** Ensure the INMP441 GND pin connects directly to the same ground rail as the ESP32. Avoid running microphone wires directly over or parallel to the MAX98357A speaker wires.

---

### C. MAX98357A I²S Amplifier & Speaker

#### 1. Absolute Silence
- **Speaker Terminal Check:** Unscrew the speaker terminals and ensure the exposed wire strands are making direct metal contact with the terminal block clamp.
- **VIN Check:** Ensure VIN is connected to the **5V** (or VBUS) pin of the ESP32. If connected to an unpowered pin, the amplifier will remain off.
- **SD_MODE Pin:** The SD_MODE pin on the MAX98357A sets shutdown and channel selection. When left **floating** (unconnected), the internal $100\text{ k}\Omega$ pull-up turns the amplifier ON in mixed stereo mode $((L+R)/2)$. If someone tied SD_MODE to Ground, the chip is in shutdown mode! Keep SD_MODE unconnected.

#### 2. Distortion / Crackling at High Volume
- **Power Sag:** When the speaker plays a loud vowel or bass note, it can draw $>500\text{ mA}$ instantaneously. If the 5V rail dips below $4.0\text{V}$, the audio signal will clip harshly.
- **Remedy:** Place a **$220\,\mu\text{F}$ or $470\,\mu\text{F}$ electrolytic capacitor** between VIN and GND directly on the amplifier's breadboard rows.
- **Volume Setting:** In `audio_output.cpp`, ensure the software gain is scaled between $0.2$ and $0.7$ (never overdrive into digital saturation).

---

### D. ESP32-S3 Wi-Fi & Boot Issues

#### 1. "rst:0x3 (RTC_SW_SYS_RST)" or "Brownout detector was triggered"
- **Cause:** Wi-Fi radio transmission requires up to $310\text{ mA}$ current spikes. If powered from a low-current USB port on a laptop or thin USB hub, the voltage drops and triggers the ESP32 brownout detector.
- **Fix:** Plug into a high-current USB 3.0 port or use the supplied **5V, 2A power adapter**.

#### 2. Wi-Fi Fails to Connect
- ESP32-S3 supports **2.4 GHz Wi-Fi only** (802.11 b/g/n). It does not support 5 GHz Wi-Fi. Ensure your router or mobile hotspot is broadcasting a 2.4 GHz network band.
