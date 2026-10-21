#include <Arduino.h>
#include "esp_heap_caps.h"

void setup() {
  Serial.begin(115200);
  delay(2000);

  Serial.println("\n=== BUDDY HARDWARE CHECK ===");

  Serial.printf("Free internal RAM: %u bytes\n",
                ESP.getFreeHeap());

  Serial.printf("Flash size: %u MB\n",
                ESP.getFlashChipSize() / (1024 * 1024));

  Serial.printf("PSRAM detected: %s\n",
                psramFound() ? "YES" : "NO");

  Serial.printf("PSRAM size: %u MB\n",
                ESP.getPsramSize() / (1024 * 1024));

  if (psramFound()) {
    Serial.printf("Free PSRAM: %u bytes\n",
                  ESP.getFreePsram());
  }

  Serial.println("============================");
}

void loop() {
  delay(1000);
}