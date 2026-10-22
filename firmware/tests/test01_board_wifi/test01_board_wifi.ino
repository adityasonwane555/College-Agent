/*
 * =====================================================================================
 * BUDDY AI — HARDWARE TEST 1: Board Boot, Serial & Wi-Fi Check
 * Hardware: ESP32-S3 N16R8 (No external components needed)
 * =====================================================================================
 */

#include <WiFi.h>

const char* WIFI_SSID = "Aditya";
const char* WIFI_PASS = "Kamaataj";

void setup() {
  Serial.begin(115200);
  Serial0.begin(115200);
  delay(1000);

  Serial.println("\n========================================================");
  Serial.println("  BUDDY AI — TEST 1: ESP32-S3 Board & Wi-Fi Diagnostic  ");
  Serial.println("========================================================");

  // 1. Chip Architecture & Memory
  Serial.printf("[Chip] ESP32-S3 Cores: %d, Rev: v%d\n", ESP.getChipCores(), ESP.getChipRevision());
  Serial.printf("[Flash] Size: %u MB, Speed: %u MHz\n", ESP.getFlashChipSize() / (1024 * 1024), ESP.getFlashChipSpeed() / 1000000);
  Serial.printf("[SRAM] Total Heap: %u bytes | Free: %u bytes\n", ESP.getHeapSize(), ESP.getFreeHeap());

  // 2. PSRAM Verification (Crucial for N16R8 Octal PSRAM)
  if (psramInit()) {
    Serial.printf("[PSRAM] Total: %u MB | Free: %u bytes (SUCCESS)\n", ESP.getPsramSize() / (1024 * 1024), ESP.getFreePsram());
  } else {
    Serial.println("[PSRAM] WARNING: PSRAM not initialized. Verify 'OPI PSRAM' in Tools menu.");
  }

  // 3. Wi-Fi Connection
  Serial.printf("[Wi-Fi] Connecting to '%s'...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 15000) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("[Wi-Fi] Connected successfully!");
    Serial.printf("[Wi-Fi] IP Address:  http://%s/\n", WiFi.localIP().toString().c_str());
    Serial.printf("[Wi-Fi] Signal RSSI: %d dBm\n", WiFi.RSSI());
    Serial.println("\n========================================================");
    Serial.println("  >>> TEST 1 STATUS: PASS <<<                           ");
    Serial.println("========================================================");
  } else {
    Serial.println("[Wi-Fi] Connection failed. Check SSID and Password.");
    Serial.println("========================================================");
    Serial.println("  >>> TEST 1 STATUS: FAIL (Wi-Fi timeout) <<<           ");
    Serial.println("========================================================");
  }
}

void loop() {
  delay(1000);
}
