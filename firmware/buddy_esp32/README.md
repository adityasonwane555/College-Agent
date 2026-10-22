# BUDDY AI — ESP32-S3 Firmware Compilation & Flashing Guide

## 1. Arduino IDE Setup

### Required Board Package:
- **esp32 by Espressif Systems** (version 2.0.14 or 3.0.x recommended)
- In Arduino IDE: `Tools -> Board -> Boards Manager -> search 'esp32'`

### Required Arduino Libraries:
Install these via `Tools -> Manage Libraries...`:
1. **Adafruit GFX Library** (by Adafruit) — Core graphics primitives.
2. **Adafruit ST7735 and ST7789 Library** (by Adafruit) — ST7789 display driver.
3. *Note:* `WiFi.h`, `WebServer.h`, and `driver/i2s.h` are built into the official ESP32 board core.

---

## 2. Arduino IDE Board Configuration Menu

When flashing the **ESP32-S3 N16R8**, configure the **Tools** menu options as follows:

| Setting | Recommended Value | Why |
| :--- | :--- | :--- |
| **Board** | `ESP32S3 Dev Module` | Standard official target for dual-port ESP32-S3. |
| **USB CDC On Boot** | `Enabled` | Allows `Serial.print()` to output over the native USB port. |
| **Flash Size** | `16MB (128Mb)` | Matches your board's physical 16MB SPI flash. |
| **Partition Scheme** | `16M Flash (3MB APP/9.9MB FATFS)` | Allocates ample space for firmware and sound assets. |
| **PSRAM** | `OPI PSRAM` (or `Enabled`) | Activates the board's high-speed 8MB Octal PSRAM. |
| **Upload Speed** | `921600` (or `460800`) | Fast flashing speed over USB. |
| **Port** | `COMx` (Your board's COM port) | Select the COM port corresponding to the board. |

---

## 3. Wi-Fi Credentials

Open `config.h` and verify lines 37–38:
```cpp
#define WIFI_SSID_DEFAULT       "Aditya"
#define WIFI_PASS_DEFAULT       "Kamaataj"
```
Change these to match your local 2.4 GHz Wi-Fi router or smartphone mobile hotspot.

---

## 4. Flashing Procedure

1. Connect the ESP32-S3 board to your PC using a high-quality USB-C data cable plugged into the **COM** port.
2. Open `firmware/buddy_esp32/buddy_esp32.ino` in Arduino IDE.
3. Click the **Verify / Compile** button (check-mark icon) to verify there are no compilation errors.
4. Click the **Upload** button (arrow icon).
5. Open the **Serial Monitor** at **115200 baud**.
6. When the board boots, it will print the local IP address:
   ```text
   [Wi-Fi] Connected successfully!
   [Wi-Fi] IP Address: http://192.168.x.x/
   ```
