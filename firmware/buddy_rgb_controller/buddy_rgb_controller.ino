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
const char* WIFI_SSID     = "Aditya";
const char* WIFI_PASSWORD = "Kamaataj";

// Optional: Define a simple shared token if your network requires basic protection.
// Leave empty ("") to disable token verification for simple local use.
const char* API_TOKEN     = ""; 

// --- Dual-Port Universal Serial Logging ---
// When USB CDC On Boot is Enabled, Serial is routed to native USB.
// Serial0 remains connected to hardware UART0 (the COM/UART USB-C port).
#if ARDUINO_USB_CDC_ON_BOOT
  #define LOG_PRINT(x)        do { Serial.print(x);   Serial0.print(x);   } while(0)
  #define LOG_PRINTLN(x)      do { Serial.println(x); Serial0.println(x); } while(0)
  #define LOG_PRINTLN_EMPTY() do { Serial.println();  Serial0.println();  } while(0)
  #define LOG_PRINTF(...)     do { Serial.printf(__VA_ARGS__); Serial0.printf(__VA_ARGS__); } while(0)
#else
  #define LOG_PRINT(x)        Serial.print(x)
  #define LOG_PRINTLN(x)      Serial.println(x)
  #define LOG_PRINTLN_EMPTY() Serial.println()
  #define LOG_PRINTF(...)     Serial.printf(__VA_ARGS__)
#endif

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
float currentAmplitude = 0.0f; // 0.0 to 1.0 overall volume
float currentBass      = 0.0f; // 0.0 to 1.0 low notes (bass/vowels)
float currentMid       = 0.0f; // 0.0 to 1.0 mid notes (formants/speech body)
float currentTreble    = 0.0f; // 0.0 to 1.0 high notes (sibilants/consonants)

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
  while (valEnd < json.length() && json[valEnd] != '\"' && json[valEnd] != ',' && json[valEnd] != '}' && json[valEnd] != '\r' && json[valEnd] != '\n') {
    valEnd++;
  }

  return json.substring(valStart, valEnd);
}

void transitionTo(LedState newState, float amplitude = -1.0f, float bass = -1.0f, float mid = -1.0f, float treble = -1.0f) {
  if (currentState != newState) {
    LOG_PRINTF("[LED] State transition: %s -> %s\n", stateToString(currentState), stateToString(newState));
    currentState = newState;
    stateEnteredTime = millis();
    // Reset frequencies on state change
    if (newState != STATE_SPEAKING) {
      currentBass = 0.0f;
      currentMid = 0.0f;
      currentTreble = 0.0f;
    }
  }
  if (amplitude >= 0.0f) currentAmplitude = amplitude;
  if (bass >= 0.0f) currentBass = bass;
  if (mid >= 0.0f) currentMid = mid;
  if (treble >= 0.0f) currentTreble = treble;
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

  // Optional equalizer and volume reactivity parameters
  float amp = -1.0f;
  String ampStr = extractJsonValue(body, "amplitude");
  if (ampStr.length() > 0) amp = constrain(ampStr.toFloat(), 0.0f, 1.0f);

  float bass = -1.0f;
  String bassStr = extractJsonValue(body, "bass");
  if (bassStr.length() > 0) bass = constrain(bassStr.toFloat(), 0.0f, 1.0f);

  float mid = -1.0f;
  String midStr = extractJsonValue(body, "mid");
  if (midStr.length() > 0) mid = constrain(midStr.toFloat(), 0.0f, 1.0f);

  float treble = -1.0f;
  String trebleStr = extractJsonValue(body, "treble");
  if (trebleStr.length() > 0) treble = constrain(trebleStr.toFloat(), 0.0f, 1.0f);

  transitionTo(targetState, amp, bass, mid, treble);

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
    // SPEAKING: Speaker Equalizer Audio-Reactive Engine
    // Blinks and pulses to high and low notes like a speaker / VU meter
    // - Low notes (Bass): Deep Magenta / Crimson Subwoofer Pulse
    // - Mid notes (Syllables): Royal Violet / Purple Body
    // - High notes (Treble): Crisp Electric Cyan / White Sparkles
    // -------------------------------------------------------------
    case STATE_SPEAKING: {
      // 1. Syllable Cadence: Human speech pacing (~3.8 Hz, 260ms per syllable)
      float syllPhase = (float)(now % 260) / 260.0f;
      float syllWave = 0.5f - 0.5f * cos(syllPhase * 2.0f * PI);
      float syllSnap = powf(syllWave, 2.0f); // Sharp physical speaker cone snap

      // 2. Bass (Low Notes): Deep vowel resonance & chest tone (1.8 Hz phrase breathing)
      float bassPhase = (float)(now % 540) / 540.0f;
      float bassWave = 0.5f - 0.5f * cos(bassPhase * 2.0f * PI);

      // 3. Treble (High Notes): Sibilants & crisp consonants (8-14 Hz rapid staccato blinks)
      float trebPhase = (float)(now % 95) / 95.0f;
      float trebBlink = (trebPhase > 0.60f) ? (0.5f - 0.5f * cos((trebPhase - 0.60f) / 0.40f * 2.0f * PI)) : 0.0f;

      // Blend external audio data if provided, or use organic speech harmonics
      float activeBass = (currentBass > 0.01f) ? currentBass : bassWave;
      float activeMid  = (currentMid > 0.01f)  ? currentMid  : syllSnap;
      float activeTreb = (currentTreble > 0.01f) ? currentTreble : trebBlink;
      float activeAmp  = (currentAmplitude > 0.01f) ? currentAmplitude : (0.40f + 0.60f * syllSnap);

      // --- Color Equalizer Synthesis ---
      // Bass (Low notes) -> Punchy Deep Magenta / Crimson Subwoofer Pulse
      float r = 245.0f * activeBass + 170.0f * activeMid + 70.0f * activeTreb;
      // Mid (Vocal core) -> Rich Royal Violet / Purple Body
      float g = 10.0f * activeBass + 25.0f * activeMid + 225.0f * activeTreb;
      // Treble (High notes) -> Electric Cyan / Crisp White Flash
      float b = 70.0f * activeBass + 255.0f * activeMid + 255.0f * activeTreb;

      // Master volume envelope (expands and contracts like a pulsing speaker diaphragm)
      float masterEnvelope = activeAmp * (0.35f + 0.65f * syllSnap);
      if (activeTreb > 0.45f) {
        // High note treble flash accent
        masterEnvelope = fminf(1.0f, masterEnvelope + 0.35f * activeTreb);
      }

      uint8_t finalR = (uint8_t)constrain(r * masterEnvelope, 0.0f, 255.0f);
      uint8_t finalG = (uint8_t)constrain(g * masterEnvelope, 0.0f, 255.0f);
      uint8_t finalB = (uint8_t)constrain(b * masterEnvelope, 0.0f, 255.0f);

      setLedColor(finalR, finalG, finalB);
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
  // 1. Instant hardware visual feedback: soft white blip confirms CPU entered setup()
  rgbLedWrite(RGB_LED_PIN, 40, 40, 40);

  // 2. Initialize primary Serial port
  Serial.begin(115200);

#if ARDUINO_USB_CDC_ON_BOOT
  // When USB CDC On Boot is Enabled, Serial is Native USB.
  // We initialize Serial0 so logs also appear on the hardware UART0 / COM port!
  Serial0.begin(115200);
#endif

  delay(400);
  setLedColor(0, 0, 0);

  LOG_PRINTLN("\n=============================================");
  LOG_PRINTLN("  BUDDY AI - Speech-Reactive RGB Controller  ");
  LOG_PRINTLN("=============================================");

  // Initialize Onboard WS2812 LED into BOOTING state
  transitionTo(STATE_BOOTING);

  // Connect to Wi-Fi
  LOG_PRINTF("[Wi-Fi] Connecting to '%s'...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long startAttempt = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startAttempt < 15000) {
    renderLedAnimation();
    delay(20);
    LOG_PRINT(".");
  }
  LOG_PRINTLN_EMPTY();

  if (WiFi.status() == WL_CONNECTED) {
    LOG_PRINTLN("[Wi-Fi] Connected successfully!");
    LOG_PRINTF("[Wi-Fi] IP Address:  http://%s\n", WiFi.localIP().toString().c_str());
    LOG_PRINTF("[Wi-Fi] Signal (RSSI): %d dBm\n", WiFi.RSSI());
  } else {
    LOG_PRINTLN("[Wi-Fi] Warning: Connection timed out. Running in offline fallback.");
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
  LOG_PRINTLN("[Server] HTTP API ready on port " + String(HTTP_PORT));
  LOG_PRINTLN("[Server] Endpoints: /health, /api/status, /api/state [POST]");
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
