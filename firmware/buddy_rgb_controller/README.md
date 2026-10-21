# BUDDY AI — Speech-Reactive ESP32-S3 RGB LED Controller

Complete hardware guide and firmware instructions for connecting your **ESP32-S3 N16R8** onboard WS2812 RGB LED (GPIO 48) with the BUDDY AI college receptionist robot over local Wi-Fi.

---

## 1. System Architecture

```
[ Visitor Speaks / Mic ]
         │
         ▼
[ BUDDY Frontend / Vite React ] ──── (State & Audio Amplitude) ──┐
         │                                                       │
         ▼                                                       │
[ BUDDY Backend (FastAPI) ]                                      │
   ├─ Faster-Whisper (CUDA STT)                                  │
   ├─ Ollama Qwen / RAG (Reasoning)                              │
   └─ Edge-TTS / Fish-Audio (Neural Voice)                       │
         │                                                       │
         ▼                                                       │
[ Audible Audio Playback in Browser ]                            │
   (audio.onplay / audio.onended)                                │
         │                                                       │
         ▼                                                       │
[ Non-blocking PC RGB Controller ] <─────────────────────────────┘
         │
         │ HTTP POST /api/state (over Local Wi-Fi, <0.2ms caller delay)
         ▼
[ ESP32-S3 N16R8 HTTP Server ]
         │
         │ Non-blocking millis() animation state machine
         ▼
[ Onboard WS2812 RGB LED on GPIO 48 ]
   ├─ BOOTING     : Cyan breathing cycle
   ├─ IDLE        : Soothing, gentle dim Cyan/Blue breath (3200ms)
   ├─ LISTENING   : Attentive Electric Blue pulse (1400ms)
   ├─ THINKING    : Warm Golden Amber glow (1200ms)
   ├─ SPEAKING    : Smooth Purple/Magenta breath modulated by speech volume
   ├─ INTERRUPTED : Warm Orange fade (600ms) -> IDLE
   ├─ COMPLETED   : Emerald Green acknowledgment (450ms) -> IDLE
   └─ ERROR       : Red pulsing alert (900ms)
```

---

## 2. Hardware Specifications

- **Microcontroller**: ESP32-S3 N16R8 (16MB Quad-SPI Flash, 8MB Octal PSRAM).
- **USB Connection**: COM/UART USB-C port for flashing and serial monitoring at 115200 baud.
- **Onboard RGB LED**: WS2812 addressable RGB LED connected to **GPIO 48**.
- **Driver**: Native ESP32 Arduino Core `rgbLedWrite(48, r, g, b)`.
- **Power**: Powered directly from USB or internal robot battery (no level shifters or external resistors needed).

---

## 3. Arduino IDE Setup & Configuration

1. **Install ESP32 Board Package**:
   - Open **Arduino IDE** > **File** > **Preferences**.
   - Add the following URL into **Additional Board Manager URLs**:
     ```
     https://espressif.github.io/arduino-esp32/package_esp32_index.json
     ```
   - Go to **Tools** > **Board** > **Boards Manager**, search for `esp32` by Espressif Systems, and click **Install** (version 2.0.14+ or 3.0.x).

2. **Select Board Profile**:
   - **Board**: `ESP32S3 Dev Module`
   - **Port**: Select your active COM port (e.g., `COM3`, `COM4`, etc.)
   - **USB CDC On Boot**: `Enabled` (for Serial output)
   - **Flash Size**: `16MB (128Mb)`
   - **Partition Scheme**: `16M Flash (3MB APP / 9.9MB FAT)` or `Default 4MB with spiffs`
   - **PSRAM**: `OPI PSRAM` (for 8MB Octal PSRAM)
   - **Upload Speed**: `921600`

---

## 4. Firmware Flashing Instructions

1. Open the sketch in Arduino IDE:
   ```
   firmware/buddy_rgb_controller/buddy_rgb_controller.ino
   ```
2. Locate the **Wi-Fi Configuration** section near the top of the file:
   ```cpp
   const char* WIFI_SSID     = "YOUR_WIFI_SSID";
   const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
   ```
   Replace `YOUR_WIFI_SSID` and `YOUR_WIFI_PASSWORD` with your local 2.4 GHz Wi-Fi credentials.
3. Click **Upload** (Ctrl + U).
4. Open the **Serial Monitor** (Ctrl + Shift + M) set to **115200 baud**.
5. Once connected, the ESP32 will print:
   ```
   =============================================
     BUDDY AI - Speech-Reactive RGB Controller  
   =============================================
   [Wi-Fi] Connecting to 'MyHomeWiFi'...
   [Wi-Fi] Connected successfully!
   [Wi-Fi] IP Address:  http://192.168.1.105
   [Wi-Fi] Signal (RSSI): -52 dBm
   [Server] HTTP API ready on port 80
   [Server] Endpoints: /health, /api/status, /api/state [POST]
   ```
6. **Note the IP address** (e.g. `http://192.168.1.105`).

---

## 5. Configuring the PC Application

Open your `.env` file in the project root (or set environment variables in Windows PowerShell):

```env
ESP32_LED_ENABLED=True
ESP32_LED_URL=http://192.168.1.105
ESP32_LED_TIMEOUT_SECONDS=1.0
```

Restart your backend server to load the new URL:
```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 6. Testing the Hardware LED

You can test every LED state directly from Windows PowerShell without running the full AI system using the included test utility:

### Check Status & Connectivity:
```powershell
python scripts/test_led.py --url http://192.168.1.105 --status
```

### Test a Specific State:
```powershell
# Test Speaking state (Purple/Magenta)
python scripts/test_led.py --url http://192.168.1.105 --state SPEAKING

# Test Thinking state (Golden Amber)
python scripts/test_led.py --url http://192.168.1.105 --state THINKING

# Test Listening state (Electric Blue)
python scripts/test_led.py --url http://192.168.1.105 --state LISTENING

# Return to Idle (Cyan breath)
python scripts/test_led.py --url http://192.168.1.105 --state IDLE
```

### Run an Automated Showcase of All States:
```powershell
python scripts/test_led.py --url http://192.168.1.105 --cycle
```

### In-Browser Test:
Open the Buddy Kiosk Web UI at `http://localhost:5173/`, click the **Settings & Health** gear icon, and click the test buttons (`Test Purple`, `Test Amber`, `Test Blue`, `Test Cyan`) to see the onboard LED change in real-time!

---

## 7. Speech-Playback Lifecycle Synchronization

The state transitions strictly mirror the audible audio playback events:

| Interaction Event | Trigger Point | LED State | Color & Effect |
| :--- | :--- | :--- | :--- |
| **Idle** | Default baseline | `IDLE` | Very dim Cyan/Blue breath (3.2s period) |
| **User Push-to-Talk** | Microphone starts recording | `LISTENING` | Attentive Electric Blue pulse (1.4s period) |
| **User Releases Button** | Recording ends, audio uploads | `THINKING` | Warm Golden Amber glow (1.2s period) |
| **AI LLM / RAG Processing** | Ollama reasoning & Edge-TTS synthesis | `THINKING` | Warm Golden Amber glow |
| **Audible Audio Starts** | `audio.onplay` / `utterance.onstart` | `SPEAKING` | Purple/Magenta breathing + voice amplitude reactivity |
| **Audible Audio Finishes** | `audio.onended` / `utterance.onend` | `COMPLETED` | Emerald Green acknowledgment (450ms) -> `IDLE` |
| **User Interruption** | User talks or clicks mute mid-speech | `INTERRUPTED` | Gentle Warm Orange fade (600ms) -> `IDLE` |
| **System Error** | Mic error / network dropout | `ERROR` | Red pulsing alert (900ms period) |

---

## 8. Troubleshooting & Common Issues

### 1. The LED does not light up
- **Verify GPIO**: The onboard RGB LED on ESP32-S3 N16R8 Dev Modules is hardwired to **GPIO 48**.
- **Run the Standalone Test**: Flash `firmware/buddy_rgb_controller/test_gpio48.ino` to confirm that the physical LED hardware turns on without needing Wi-Fi.

### 2. Wi-Fi fails to connect
- Ensure you are connecting to a **2.4 GHz Wi-Fi** network (ESP32 does not support 5 GHz Wi-Fi).
- Verify SSID and password spelling in `buddy_rgb_controller.ino`.

### 3. PC says `Connection timed out` or `Cannot reach ESP32`
- Verify that both the PC and the ESP32-S3 are connected to the **same Wi-Fi router / subnet**.
- Check if AP client isolation is enabled on your router.
- Test pinging the ESP32 from PowerShell:
  ```powershell
  Test-NetConnection -ComputerName 192.168.1.105 -Port 80
  ```

### 4. Zero Latency Guarantee
- The PC controller uses a dedicated background thread with thread-safe queue dispatching. If the ESP32 loses power or disconnects, the AI robot will **continue talking and functioning without any stutter or delay**.
