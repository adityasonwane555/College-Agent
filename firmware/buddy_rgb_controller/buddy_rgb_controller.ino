/*
 * =====================================================================================
 * BUDDY AI - Speech-Reactive Onboard RGB LED Controller
 * Hardware: ESP32-S3 N16R8 (ESP32S3 Dev Module profile)
 * LED: Onboard WS2812 RGB LED on GPIO 48
 * Communication: Local Wi-Fi HTTP Server
 * =====================================================================================
 */

#include <WiFi.h>
#include <WebServer.h>

// ========================== CONFIGURATION ==========================
#define RGB_LED_PIN 48          // Verified onboard WS2812 LED pin on ESP32-S3 Dev Module
#define MAX_BRIGHTNESS 60       // Safe, eye-friendly brightness limit (0 - 255)
#define HTTP_PORT 80            // Lightweight local HTTP server port
#define IDLE_TIMEOUT_MS 60000   // Auto-fallback to IDLE if no command received for 60s

// --- Wi-Fi Credentials (Change to match your local network) ---
// NOTE: For security, never commit real credentials to public repositories.
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Optional: Define a simple shared token if your network requires basic protection.
// Leave empty ("") to disable token verification for simple local use.
const char* API_TOKEN     = ""; 

// ========================== STATE DEFINITIONS ==========================
enum LedState {
  STATE_BOOTING,
  STATE_IDLE,
  STATE_LISTENING,
  STATE_THINKING,
  STATE_SPEAKING,
  STATE_INTERRUPTED,
  STATE_ERROR,
  STATE_COMPLETED
};

volatile LedState currentState = STATE_BOOTING;
unsigned long lastStateUpdate = 0;
unsigned long stateEnteredTime = 0;
float currentAmplitude = 0.0f; // 0.0 to 1.0 audio volume indicator

// ========================== SERVER INSTANCE ==========================
WebServer server(HTTP_PORT);

// ========================== HELPER FUNCTIONS ==========================
// Safe RGB write function using ESP32 Arduino Core's built-in rgbLedWrite()
void setLedColor(uint8_t r, uint8_t g, uint8_t b) {
  // Scale each channel according to MAX_BRIGHTNESS
  uint8_t scaledR = (uint8_t)(((uint16_t)r * MAX_BRIGHTNESS) / 255);
  uint8_t scaledG = (uint8_t)(((uint16_t)g * MAX_BRIGHTNESS) / 255);
  uint8_t scaledB = (uint8_t)(((uint16_t)b * MAX_BRIGHTNESS) / 255);
  rgbLedWrite(RGB_LED_PIN, scaledR, scaledG, scaledB);
}

const char* stateToString(LedState state) {
  switch (state) {
    case STATE_BOOTING:     return "BOOTING";
    case STATE_IDLE:        return "IDLE";
    case STATE_LISTENING:   return "LISTENING";
    case STATE_THINKING:    return "THINKING";
    case STATE_SPEAKING:    return "SPEAKING";
    case STATE_INTERRUPTED: return "INTERRUPTED";
    case STATE_ERROR:       return "ERROR";
    case STATE_COMPLETED:   return "COMPLETED";
    default:                return "UNKNOWN";
  }
}

bool parseStateString(String str, LedState &outState) {
  str.trim();
  str.toUpperCase();
  if (str == "BOOTING")     { outState = STATE_BOOTING;     return true; }
  if (str == "IDLE")        { outState = STATE_IDLE;        return true; }
  if (str == "LISTENING")   { outState = STATE_LISTENING;   return true; }
  if (str == "THINKING")    { outState = STATE_THINKING;    return true; }
  if (str == "SPEAKING")    { outState = STATE_SPEAKING;    return true; }
  if (str == "INTERRUPTED") { outState = STATE_INTERRUPTED; return true; }
  if (str == "ERROR")       { outState = STATE_ERROR;       return true; }
  if (str == "COMPLETED" || str == "COMPLETED_SPEECH") { outState = STATE_COMPLETED; return true; }
  return false;
}

// Simple zero-dependency JSON field extractor to eliminate extra library prerequisites
String extractJsonValue(const String& json, const String& key) {
  String searchKey = "\"" + key + "\"";
  int keyIndex = json.indexOf(searchKey);
  if (keyIndex == -1) return "";

  int colonIndex = json.indexOf(':', keyIndex + searchKey.length());
  if (colonIndex == -1) return "";

  int valStart = colonIndex + 1;
  while (valStart < json.length() && (json[valStart] == ' ' || json[valStart] == '\"')) {
    valStart++;
  }

  int valEnd = valStart;
  while (valEnd < json.length() && json[valEnd] != '\"' && json[valEnd] != ',' && json[valEnd] != '}' && json[valEnd] != '\n' && json[valEnd] != '\r') {
    valEnd++;
  }

  return json.substring(valStart, valEnd);
}

void transitionTo(LedState newState, float amplitude = 0.0f) {
  if (currentState != newState) {
    Serial.printf("[LED] State transition: %s -> %s\n", stateToString(currentState), stateToString(newState));
    currentState = newState;
    stateEnteredTime = millis();
  }
  currentAmplitude = amplitude;
  lastStateUpdate = millis();
}

// ========================== HTTP HANDLERS ==========================
void sendCorsHeader() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Access-Control-Allow-Methods", "POST, GET, OPTIONS");
  server.sendHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");
}

void handleOptions() {
  sendCorsHeader();
  server.send(204);
}

void handleHealth() {
  sendCorsHeader();
  String response = "{\"ok\":true,\"status\":\"healthy\",\"device\":\"BUDDY-ESP32-S3\"}";
  server.send(200, "application/json", response);
}

void handleStatus() {
  sendCorsHeader();
  String response = "{";
  response += "\"ok\":true,";
  response += "\"state\":\"" + String(stateToString(currentState)) + "\",";
  response += "\"device\":\"BUDDY-ESP32-S3\",";
  response += "\"gpio\":" + String(RGB_LED_PIN) + ",";
  response += "\"wifi_rssi\":" + String(WiFi.RSSI()) + ",";
  response += "\"uptime_ms\":" + String(millis());
  response += "}";
  server.send(200, "application/json", response);
}

void handleSetState() {
  sendCorsHeader();

  // Basic security token verification if configured
  if (strlen(API_TOKEN) > 0) {
    if (!server.hasHeader("Authorization") || server.header("Authorization") != API_TOKEN) {
      server.send(401, "application/json", "{\"ok\":false,\"error\":\"Unauthorized\"}");
      return;
    }
  }

  if (!server.hasArg("plain")) {
    server.send(400, "application/json", "{\"ok\":false,\"error\":\"Missing JSON body\"}");
    return;
  }

  String body = server.arg("plain");
  String stateStr = extractJsonValue(body, "state");

  if (stateStr.length() == 0) {
    server.send(400, "application/json", "{\"ok\":false,\"error\":\"Field 'state' is required\"}");
    return;
  }

  LedState targetState;
  if (!parseStateString(stateStr, targetState)) {
    server.send(400, "application/json", "{\"ok\":false,\"error\":\"Unknown state: " + stateStr + "\"}");
    return;
  }

  // Optional amplitude value for audio reactivity
  float amp = 0.0f;
  String ampStr = extractJsonValue(body, "amplitude");
  if (ampStr.length() > 0) {
    amp = ampStr.toFloat();
    if (amp < 0.0f) amp = 0.0f;
    if (amp > 1.0f) amp = 1.0f;
  }

  transitionTo(targetState, amp);

  String response = "{\"ok\":true,\"state\":\"" + String(stateToString(targetState)) + "\"}";
  server.send(200, "application/json", response);
}

// ========================== ANIMATION ENGINE (Non-blocking) ==========================
void renderLedAnimation() {
  unsigned long now = millis();
  unsigned long elapsed = now - stateEnteredTime;

  // Auto-revert to IDLE after prolonged inactivity (except during boot)
  if (currentState != STATE_IDLE && currentState != STATE_BOOTING && currentState != STATE_ERROR) {
    if (now - lastStateUpdate > IDLE_TIMEOUT_MS) {
      Serial.println("[LED] Inactivity timeout reached. Returning to IDLE.");
      transitionTo(STATE_IDLE);
    }
  }

  switch (currentState) {
    // -------------------------------------------------------------
    // BOOTING: Brief cyan animation, then smooth transition to IDLE
    // -------------------------------------------------------------
    case STATE_BOOTING: {
      if (elapsed > 2500) {
        transitionTo(STATE_IDLE);
        break;
      }
      float phase = (float)(elapsed % 1200) / 1200.0f;
      float brightness = 0.3f + 0.7f * (0.5f - 0.5f * cos(phase * 2.0f * PI));
      uint8_t val = (uint8_t)(brightness * 200.0f);
      setLedColor(0, val, val); // Cyan
      break;
    }

    // -------------------------------------------------------------
    // IDLE: Dim, soothing cyan/blue breathing (slow period: 3200ms)
    // -------------------------------------------------------------
    case STATE_IDLE: {
      float phase = (float)(now % 3200) / 3200.0f;
      // Gentle breathing wave from 8% to 35% brightness
      float factor = 0.08f + 0.27f * (0.5f - 0.5f * cos(phase * 2.0f * PI));
      uint8_t cyanG = (uint8_t)(factor * 160.0f);
      uint8_t cyanB = (uint8_t)(factor * 255.0f);
      setLedColor(0, cyanG, cyanB);
      break;
    }

    // -------------------------------------------------------------
    // LISTENING: Blue pulsing, faster and attentive (period: 1400ms)
    // -------------------------------------------------------------
    case STATE_LISTENING: {
      float phase = (float)(now % 1400) / 1400.0f;
      float factor = 0.20f + 0.80f * (0.5f - 0.5f * cos(phase * 2.0f * PI));
      uint8_t blue = (uint8_t)(factor * 255.0f);
      uint8_t cyanAccent = (uint8_t)(factor * 60.0f);
      setLedColor(0, cyanAccent, blue); // Deep attentive electric blue
      break;
    }

    // -------------------------------------------------------------
    // THINKING: Warm amber/golden breathing (period: 1200ms)
    // -------------------------------------------------------------
    case STATE_THINKING: {
      float phase = (float)(now % 1200) / 1200.0f;
      float factor = 0.25f + 0.75f * (0.5f - 0.5f * cos(phase * 2.0f * PI));
      uint8_t r = (uint8_t)(factor * 255.0f);
      uint8_t g = (uint8_t)(factor * 135.0f); // Warm amber
      setLedColor(r, g, 0);
      break;
    }

    // -------------------------------------------------------------
    // SPEAKING: Purple / Magenta animated breathing with subtle color
    // shifts and optional amplitude reactivity
    // -------------------------------------------------------------
    case STATE_SPEAKING: {
      // Base breathing cycle (period: 1600ms)
      float phase = (float)(now % 1600) / 1600.0f;
      float wave = 0.35f + 0.65f * (0.5f - 0.5f * cos(phase * 2.0f * PI));

      // If audio amplitude is provided, modulate brightness with voice dynamics
      if (currentAmplitude > 0.05f) {
        wave = wave * 0.4f + currentAmplitude * 0.6f;
        if (wave > 1.0f) wave = 1.0f;
      }

      // Subtle color transition between rich purple and vibrant magenta
      float colorShift = 0.5f + 0.5f * sin(phase * PI);
      uint8_t r = (uint8_t)(wave * (190.0f + 65.0f * colorShift)); // 190 to 255
      uint8_t g = (uint8_t)(wave * (10.0f * (1.0f - colorShift))); // Very subtle green
      uint8_t b = (uint8_t)(wave * (240.0f - 80.0f * colorShift)); // 240 down to 160
      setLedColor(r, g, b);
      break;
    }

    // -------------------------------------------------------------
    // INTERRUPTED: Brief gentle orange transition for 600ms, then IDLE
    // -------------------------------------------------------------
    case STATE_INTERRUPTED: {
      if (elapsed > 600) {
        transitionTo(STATE_IDLE);
        break;
      }
      float progress = (float)elapsed / 600.0f;
      float fade = 1.0f - progress;
      uint8_t r = (uint8_t)(fade * 255.0f);
      uint8_t g = (uint8_t)(fade * 90.0f);
      setLedColor(r, g, 0); // Gentle warm orange fade
      break;
    }

    // -------------------------------------------------------------
    // COMPLETED SPEECH: Crisp pleasant green acknowledgment (450ms)
    // -------------------------------------------------------------
    case STATE_COMPLETED: {
      if (elapsed > 450) {
        transitionTo(STATE_IDLE);
        break;
      }
      float progress = (float)elapsed / 450.0f;
      float brightness = sin(progress * PI);
      uint8_t g = (uint8_t)(brightness * 240.0f);
      uint8_t b = (uint8_t)(brightness * 120.0f);
      setLedColor(0, g, b); // Emerald cyan acknowledgment
      break;
    }

    // -------------------------------------------------------------
    // ERROR: Gentle red pulsing pattern (period: 900ms)
    // -------------------------------------------------------------
    case STATE_ERROR: {
      float phase = (float)(now % 900) / 900.0f;
      float factor = 0.20f + 0.80f * (0.5f - 0.5f * cos(phase * 2.0f * PI));
      uint8_t r = (uint8_t)(factor * 255.0f);
      setLedColor(r, 0, 0);
      break;
    }
  }
}

// Non-blocking Wi-Fi auto-reconnection monitor
void checkWiFiConnection() {
  static unsigned long lastWifiCheck = 0;
  if (millis() - lastWifiCheck > 10000) {
    lastWifiCheck = millis();
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("[Wi-Fi] Disconnected! Attempting non-blocking reconnect...");
      WiFi.reconnect();
    }
  }
}

// ========================== SETUP & LOOP ==========================
void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("\n=============================================");
  Serial.println("  BUDDY AI - Speech-Reactive RGB Controller  ");
  Serial.println("=============================================");

  // Initialize Onboard WS2812 LED on GPIO 48
  setLedColor(0, 0, 0);
  transitionTo(STATE_BOOTING);

  // Connect to Wi-Fi
  Serial.printf("[Wi-Fi] Connecting to '%s'...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long startAttempt = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startAttempt < 15000) {
    renderLedAnimation();
    delay(20);
    Serial.print(".");
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("[Wi-Fi] Connected successfully!");
    Serial.printf("[Wi-Fi] IP Address:  http://%s\n", WiFi.localIP().toString().c_str());
    Serial.printf("[Wi-Fi] Signal (RSSI): %d dBm\n", WiFi.RSSI());
  } else {
    Serial.println("[Wi-Fi] Warning: Connection timed out. Running in offline fallback.");
  }

  // Register HTTP Endpoints
  server.on("/health", HTTP_GET, handleHealth);
  server.on("/api/status", HTTP_GET, handleStatus);
  server.on("/api/state", HTTP_POST, handleSetState);
  server.on("/api/state", HTTP_OPTIONS, handleOptions);
  server.onNotFound([]() {
    sendCorsHeader();
    server.send(404, "application/json", "{\"ok\":false,\"error\":\"Endpoint not found\"}");
  });

  server.begin();
  Serial.println("[Server] HTTP API ready on port " + String(HTTP_PORT));
  Serial.println("[Server] Endpoints: /health, /api/status, /api/state [POST]");
}

void loop() {
  // Handle incoming HTTP requests
  server.handleClient();

  // Non-blocking animation frame
  renderLedAnimation();

  // Monitor Wi-Fi liveness
  checkWiFiConnection();

  // Small 5ms sleep to yield to RTOS watchdog and Wi-Fi stack
  delay(5);
}
