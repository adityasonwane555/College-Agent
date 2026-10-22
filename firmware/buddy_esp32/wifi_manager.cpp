/*
 * =====================================================================================
 * BUDDY AI — Wi-Fi & WebServer Manager Implementation
 * =====================================================================================
 */

#include "wifi_manager.h"
#include "rgb_manager.h"
#include "display_manager.h"
#include "audio_output.h"
#include "microphone_manager.h"

WifiManager wifiManager;

WifiManager::WifiManager()
  : _server(HTTP_SERVER_PORT),
    _ssid(WIFI_SSID_DEFAULT),
    _password(WIFI_PASS_DEFAULT),
    _lastReconnectAttempt(0),
    _wasConnected(false) {}

void WifiManager::begin(const char* ssid, const char* password) {
  _ssid = ssid;
  _password = password;

  LOG_PRINTF("[Wi-Fi] Connecting to '%s'...\n", _ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(_ssid, _password);

  setupRoutes();
  _server.begin();
  LOG_PRINTLN("[Wi-Fi] HTTP Server initialized.");
}

bool WifiManager::isConnected() const {
  return (WiFi.status() == WL_CONNECTED);
}

String WifiManager::getIpAddress() const {
  return isConnected() ? WiFi.localIP().toString() : String("0.0.0.0");
}

int8_t WifiManager::getRssi() const {
  return isConnected() ? WiFi.RSSI() : -100;
}

void WifiManager::setupRoutes() {
  _server.on("/health", HTTP_GET, [this]() { handleHealth(); });
  _server.on("/", HTTP_GET, [this]() { handleHealth(); });
  _server.on("/api/state", HTTP_POST, [this]() { handleState(); });
  _server.on("/api/display", HTTP_POST, [this]() { handleDisplay(); });
  _server.on("/api/chime", HTTP_POST, [this]() { handleChime(); });
  _server.on("/api/mic", HTTP_GET, [this]() { handleMicStream(); });
  _server.on("/api/speak", HTTP_POST, [this]() { handleSpeakStream(); });

  _server.onNotFound([this]() {
    _server.send(404, "text/plain", "Buddy AI: Endpoint Not Found");
  });
}

void WifiManager::handleHealth() {
  String json = "{";
  json += "\"status\":\"ok\",";
  json += "\"device\":\"buddy_esp32_s3\",";
  json += "\"target\":\"APCOER College Reception Robot\",";
  json += "\"state\":\"" + String(buddyStateToString(rgbManager.getState())) + "\",";
  json += "\"ip\":\"" + getIpAddress() + "\",";
  json += "\"rssi\":" + String(getRssi()) + ",";
  json += "\"free_heap\":" + String(ESP.getFreeHeap()) + ",";
  json += "\"psram_free\":" + String(ESP.getFreePsram());
  json += "}";

  _server.sendHeader("Access-Control-Allow-Origin", "*");
  _server.send(200, "application/json", json);
}

void WifiManager::handleState() {
  String stateStr = "";
  float amp = 0.0f, bass = 0.0f, mid = 0.0f, treble = 0.0f;

  if (_server.hasArg("state")) {
    stateStr = _server.arg("state");
  } else if (_server.hasArg("plain")) {
    String body = _server.arg("plain");
    // Simple fast JSON extraction
    int sIdx = body.indexOf("\"state\":\"");
    if (sIdx >= 0) {
      int endIdx = body.indexOf("\"", sIdx + 9);
      if (endIdx > sIdx) stateStr = body.substring(sIdx + 9, endIdx);
    }
    int aIdx = body.indexOf("\"amplitude\":");
    if (aIdx >= 0) amp = body.substring(aIdx + 12).toFloat();
    int bIdx = body.indexOf("\"bass\":");
    if (bIdx >= 0) bass = body.substring(bIdx + 7).toFloat();
    int mIdx = body.indexOf("\"mid\":");
    if (mIdx >= 0) mid = body.substring(mIdx + 6).toFloat();
    int tIdx = body.indexOf("\"treble\":");
    if (tIdx >= 0) treble = body.substring(tIdx + 9).toFloat();
  }

  stateStr.toUpperCase();
  stateStr.trim();

  BuddyState targetState = rgbManager.getState();
  if (stateStr == "BOOTING") targetState = STATE_BOOTING;
  else if (stateStr == "IDLE") targetState = STATE_IDLE;
  else if (stateStr == "LISTENING") targetState = STATE_LISTENING;
  else if (stateStr == "THINKING") targetState = STATE_THINKING;
  else if (stateStr == "SPEAKING") targetState = STATE_SPEAKING;
  else if (stateStr == "ERROR") targetState = STATE_ERROR;

  rgbManager.setState(targetState);
  rgbManager.setAudioLevels(amp, bass, mid, treble);
  displayManager.setState(targetState);
  displayManager.setAudioLevel(amp);

  _server.sendHeader("Access-Control-Allow-Origin", "*");
  _server.send(200, "application/json", "{\"ok\":true,\"state\":\"" + stateStr + "\"}");
}

void WifiManager::handleDisplay() {
  String title = "Buddy AI";
  String body = "";

  if (_server.hasArg("title")) title = _server.arg("title");
  if (_server.hasArg("body")) body = _server.arg("body");

  displayManager.setMessage(title, body);

  _server.sendHeader("Access-Control-Allow-Origin", "*");
  _server.send(200, "application/json", "{\"ok\":true}");
}

void WifiManager::handleChime() {
  audioOutput.playChime();
  _server.sendHeader("Access-Control-Allow-Origin", "*");
  _server.send(200, "application/json", "{\"ok\":true,\"message\":\"Chime played\"}");
}

void WifiManager::handleMicStream() {
  // Capture a 512-sample chunk of 16-bit PCM from the INMP441 and stream as binary WAV/PCM
  int16_t samples[512];
  size_t count = microphoneManager.readSamples(samples, 512);

  _server.sendHeader("Access-Control-Allow-Origin", "*");
  _server.sendHeader("Content-Type", "application/octet-stream");
  _server.send_P(200, "application/octet-stream", (const char*)samples, count * sizeof(int16_t));
}

void WifiManager::handleSpeakStream() {
  if (!_server.hasArg("plain")) {
    _server.send(400, "text/plain", "Missing audio payload");
    return;
  }

  String body = _server.arg("plain");
  const uint8_t* rawData = (const uint8_t*)body.c_str();
  size_t len = body.length();

  rgbManager.setState(STATE_SPEAKING);
  displayManager.setState(STATE_SPEAKING);

  // Stream directly to MAX98357A I2S
  audioOutput.writePcm((const int16_t*)rawData, len / sizeof(int16_t));

  rgbManager.setState(STATE_IDLE);
  displayManager.setState(STATE_IDLE);

  _server.send(200, "application/json", "{\"ok\":true,\"played_bytes\":" + String(len) + "}");
}

void WifiManager::update() {
  _server.handleClient();

  bool connected = isConnected();
  if (connected && !_wasConnected) {
    _wasConnected = true;
    LOG_PRINTLN("\n[Wi-Fi] Connected successfully!");
    LOG_PRINTF("[Wi-Fi] IP Address: http://%s/\n", getIpAddress().c_str());
    displayManager.setWifiInfo(_ssid, getIpAddress());
    rgbManager.setState(STATE_IDLE);
    displayManager.setState(STATE_IDLE);
  } else if (!connected && _wasConnected) {
    _wasConnected = false;
    LOG_PRINTLN("\n[Wi-Fi] Lost connection. Reconnecting...");
    displayManager.setWifiInfo(_ssid, "Reconnecting...");
    rgbManager.setState(STATE_ERROR);
    displayManager.setState(STATE_ERROR);
  }

  // Auto-reconnect poll every 12s only if connection failed or was lost
  if (!connected) {
    unsigned long now = millis();
    if (now - _lastReconnectAttempt > 12000) {
      _lastReconnectAttempt = now;
      wl_status_t st = WiFi.status();
      if (st == WL_CONNECT_FAILED || st == WL_CONNECTION_LOST || st == WL_NO_SSID_AVAIL) {
        LOG_PRINTF("[Wi-Fi] Retrying connection to '%s' (status code: %d)...\n", _ssid, (int)st);
        WiFi.disconnect(false);
        delay(100);
        WiFi.begin(_ssid, _password);
      }
    }
  }
}
