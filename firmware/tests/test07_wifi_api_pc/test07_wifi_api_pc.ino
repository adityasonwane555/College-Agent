/*
 * =====================================================================================
 * BUDDY AI — HARDWARE TEST 7: PC-to-ESP32 Wi-Fi REST API Communication
 * =====================================================================================
 */

#include <WiFi.h>
#include <WebServer.h>

const char* WIFI_SSID = "Aditya";
const char* WIFI_PASS = "Kamaataj";

WebServer server(80);

void setup() {
  Serial.begin(115200);
  Serial0.begin(115200);
  delay(500);

  Serial.println("\n========================================================");
  Serial.println("  BUDDY AI — TEST 7: Wi-Fi REST API Diagnostic          ");
  Serial.println("========================================================");

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n[Wi-Fi] Connected!");
  Serial.printf("[Wi-Fi] Listening at: http://%s/\n", WiFi.localIP().toString().c_str());

  server.on("/health", HTTP_GET, []() {
    Serial.println("[API] Received GET /health");
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", "{\"status\":\"ok\",\"device\":\"buddy_esp32_s3\",\"test\":7}");
  });

  server.on("/api/state", HTTP_POST, []() {
    String state = server.hasArg("state") ? server.arg("state") : "UNKNOWN";
    Serial.printf("[API] State transition commanded: %s\n", state.c_str());
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", "{\"ok\":true,\"state\":\"" + state + "\"}");
  });

  server.begin();
  Serial.println("[HTTP] Server ready. Test from PC using:");
  Serial.printf("  curl http://%s/health\n", WiFi.localIP().toString().c_str());
  Serial.println("========================================================");
}

void loop() {
  server.handleClient();
  delay(2);
}
