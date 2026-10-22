# BUDDY AI — Hardware Step-by-Step Test Plan

**Target Hardware:** ESP32-S3 N16R8 Dev Module  
**Project:** BUDDY AI — College Reception Robot for APCOER Pune  
**Document Revision:** 1.0 (Hardware-Ready)  

---

## 1. Golden Testing Rule

> [!IMPORTANT]
> **TEST ONE COMPONENT AT A TIME.**  
> Do not wire all components to the breadboard simultaneously before running initial diagnostics. If all parts are connected at once and the system fails to boot, diagnosing the fault is difficult. By testing each component individually in the sequence below, you can isolate problems quickly.

---

## 2. Master Test Sequence

```
[TEST 1] Board & Wi-Fi Check ──► [TEST 2] Onboard RGB LED (GPIO 48)
                                              │
[TEST 4] INMP441 Microphone  ◄── [TEST 3] ST7789 TFT Display (SPI)
         │
         ▼
[TEST 5] MAX98357A & Speaker ──► [TEST 6] Buttons & Aux LEDs
                                              │
[TEST 8] Mic Audio Transport ◄── [TEST 7] PC-to-ESP32 Wi-Fi API
         │
         ▼
[TEST 9] Speaker Audio Stream──► [TEST 10] Full BUDDY AI System
```

---

## 3. Detailed Component Test Procedures

### TEST 1: ESP32 Board, Serial Output, and Wi-Fi Connection
- **Objective:** Verify ESP32-S3 microcontroller boot, dual-port serial output, and 2.4 GHz Wi-Fi connectivity.
- **Physical Wiring:** None! Only the ESP32-S3 board plugged into your PC via the **COM** USB-C port.
- **Sketch File:** `firmware/tests/test01_board_wifi/test01_board_wifi.ino`
- **Arduino IDE Settings:**
  - Board: **ESP32S3 Dev Module**
  - USB CDC On Boot: **Enabled**
  - Flash Size: **16MB (128Mb)**
  - Partition Scheme: **16M Flash (3MB APP/9.9MB FATFS)** or **Default 4MB with spiffs**
  - PSRAM: **OPI PSRAM** (or Enabled)
- **Expected Serial Output (115200 baud):**
  ```text
  =============================================
    TEST 1: ESP32-S3 Board & Wi-Fi Diagnostic
  =============================================
  [Chip] Model: ESP32-S3, Cores: 2, Revision: v0.2
  [Memory] Total Heap: 382412 bytes | Free: 351296 bytes
  [PSRAM] Total PSRAM: 8388608 bytes (8MB) | Free: 8384512 bytes
  [Wi-Fi] Connecting to 'Aditya'...
  [Wi-Fi] Connected successfully!
  [Wi-Fi] IP Address: 192.168.x.x
  [Wi-Fi] RSSI Signal: -48 dBm (Strong)
  =============================================
  TEST 1 STATUS: PASS
  =============================================
  ```
- **Pass Criterion:** ESP32 connects to Wi-Fi, acquires an IP address, and verifies 8MB PSRAM.

---

### TEST 2: Onboard WS2812 RGB LED (GPIO 48)
- **Objective:** Verify color cycling and non-blocking breathing animations on the onboard RGB LED.
- **Physical Wiring:** None (pre-wired on PCB).
- **Sketch File:** `firmware/tests/test02_rgb_led/test02_rgb_led.ino`
- **Expected Visual Behavior:**
  1. Cycles through solid RED (1 sec), GREEN (1 sec), BLUE (1 sec).
  2. Transitions into smooth breathing animations for each Buddy AI state:
     - **IDLE:** Dim Cyan breathing.
     - **LISTENING:** Soft Blue pulse.
     - **THINKING:** Warm Amber pulse.
     - **SPEAKING:** Vibrant Purple breathing.
     - **ERROR:** Alert Red pulse.
- **Pass Criterion:** The onboard LED lights up, displays the correct colors, and breathes smoothly without flickering.

---

### TEST 3: ST7789 2.8" SPI TFT LCD (240 × 320)
- **Objective:** Verify SPI communication, color rendering, and screen layout.
- **Physical Wiring:**
  - `ST7789 GND` → **GND**
  - `ST7789 VCC` → **3.3V**
  - `ST7789 SCL` → **GPIO 12**
  - `ST7789 SDA` → **GPIO 11**
  - `ST7789 RES` → **GPIO 13**
  - `ST7789 DC`  → **GPIO 9**
  - `ST7789 CS`  → **GPIO 10** (or GND if 7-pin module)
  - `ST7789 BLK` → **3.3V** (or GPIO 14)
- **Sketch File:** `firmware/tests/test03_st7789_display/test03_st7789_display.ino`
- **Expected Display Output:**
  - Solid color fill tests (Red, Green, Blue, Black).
  - Buddy AI Robot Face & Status Card:
    - Title: **BUDDY AI**
    - Subtitle: **APCOER College Reception**
    - Status: **Ready (Online)**
    - IP Address and animated listening audio wave.
- **Pass Criterion:** Sharp text, vibrant colors, no distortion, no screen rolling or inversion.

---

### TEST 4: INMP441 Omnidirectional I²S Microphone
- **Objective:** Verify I²S clocking, DMA sample acquisition, and acoustic response.
- **Physical Wiring:**
  - `INMP441 VDD` → **3.3V** (*NEVER 5V*)
  - `INMP441 GND` → **GND**
  - `INMP441 SCK` → **GPIO 4**
  - `INMP441 WS`  → **GPIO 5**
  - `INMP441 SD`  → **GPIO 6**
  - `INMP441 L/R` → **GND**
- **Sketch File:** `firmware/tests/test04_inmp441_mic/test04_inmp441_mic.ino`
- **Expected Serial Output:**
  - Live ASCII VU-Meter bar that reacts to your voice:
  ```text
  [Mic VU] Energy:  120 | [====                ] Ambient Room
  [Mic VU] Energy: 1850 | [====================] Speaking: "Hello Buddy!"
  [Mic VU] Energy: 2400 | [========================] Clapping hands
  ```
- **Pass Criterion:** Non-zero sample values; VU-meter expands dynamically when speaking near the microphone and contracts in silence.

---

### TEST 5: MAX98357A I²S Class-D Amplifier & Passive Speaker
- **Objective:** Verify digital-to-analog audio output, I²S audio transmission, and speaker fidelity.
- **Physical Wiring:**
  - `MAX98357A VIN` → **ESP32 5V (or VBUS)**
  - `MAX98357A GND` → **GND**
  - `MAX98357A BCLK`→ **GPIO 15**
  - `MAX98357A LRC` → **GPIO 16**
  - `MAX98357A DIN` → **GPIO 17**
  - `SPK+` / `SPK-` → Connected to passive $4\Omega$ or $8\Omega$ speaker terminals.
- **Sketch File:** `firmware/tests/test05_max98357a_speaker/test05_max98357a_speaker.ino`
- **Expected Audio Output:**
  - Plays a gentle, pleasant dual-tone chime ($440\text{ Hz}$ then $880\text{ Hz}$) at low safe volume.
  - No loud clicking, popping, or harsh distortion.
- **Pass Criterion:** Clear chime heard through speaker; amplifier chip stays cool to the touch.

---

### TEST 6: Push Buttons & External Status LEDs (Optional)
- **Objective:** Verify switch debouncing and GPIO output current.
- **Physical Wiring:**
  - Tactile button between **GPIO 1** and **GND**.
  - LED anode to **GPIO 2** via $220\Omega$, cathode to **GND**.
- **Sketch File:** `firmware/tests/test06_buttons_leds/test06_buttons_leds.ino`
- **Expected Behavior:** LED turns ON when the button is held down and OFF when released; button presses are logged to the Serial Monitor with zero bounce glitches.
- **Pass Criterion:** Clean trigger log without double-clicks.

---

### TEST 7: PC-to-ESP32 Wi-Fi REST API Communication
- **Objective:** Verify that the PC backend can query the ESP32 status and command state transitions over local Wi-Fi.
- **Sketch File:** `firmware/tests/test07_wifi_api_pc/test07_wifi_api_pc.ino`
- **PC Test Command (Run from PC terminal):**
  ```bash
  .venv\Scripts\python.exe -c "import httpx; r = httpx.get('http://<ESP32_IP>/health'); print(r.json())"
  ```
- **Expected Result:** HTTP 200 response with JSON `{"status":"ok","device":"buddy_esp32","state":"IDLE"}`.
- **Pass Criterion:** Latency $<25\text{ ms}$; zero packet drops on the local Wi-Fi network.

---

### TEST 8: Microphone Audio Streaming (ESP32 → PC STT)
- **Objective:** Stream real-time 16 kHz 16-bit PCM audio from the INMP441 microphone to the PC for transcription.
- **Sketch File:** `firmware/tests/test08_mic_transport/test08_mic_transport.ino`
- **PC Test Tool:** `scripts/test_mic_stream.py`
- **Expected Result:** PC receives live audio stream and Whisper transcribes spoken words accurately.
- **Pass Criterion:** Clear audio recorded into a test WAV file with speech intelligibility.

---

### TEST 9: Speaker Audio Streaming (PC TTS → ESP32)
- **Objective:** Stream synthesized neural speech WAV/PCM from the PC to the ESP32 for playback through the speaker.
- **Sketch File:** `firmware/tests/test09_speaker_stream/test09_speaker_stream.ino`
- **PC Test Tool:** `scripts/test_speaker_stream.py`
- **Expected Result:** Buddy's generated voice ("Welcome to Anantrao Pawar College of Engineering") plays clearly through the speaker.
- **Pass Criterion:** Synchronized playback without buffer underrun stutters or delays.

---

### TEST 10: Complete Integrated System Test
- **Objective:** Full end-to-end integration of display, microphone, amplifier, RGB LED, and PC agent.
- **Sketch File:** `firmware/buddy_esp32/buddy_esp32.ino`
- **Expected Behavior:**
  1. Boot: Display shows "BUDDY AI Starting...", RGB LED boots red/amber, connects to Wi-Fi.
  2. Ready: Display shows IP address, RGB LED breathes cyan (IDLE).
  3. User speaks: RGB pulses blue (LISTENING), display shows user speech audio wave.
  4. AI Processing: RGB pulses amber (THINKING), display shows thinking spinner.
  5. Response: High-quality speech plays from speaker, RGB breathes purple reacting to speech volume, display shows robot smile face and text answer.
  6. Returns gracefully to IDLE state.
