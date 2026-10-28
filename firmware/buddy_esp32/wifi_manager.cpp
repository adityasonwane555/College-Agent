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
    _wasConnected(false),
    _abortPlayback(false) {}

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
  _server.on("/api/health", HTTP_GET, [this]() { handleHealth(); });
  _server.on("/api/status", HTTP_GET, [this]() { handleHealth(); });
  _server.on("/", HTTP_GET, [this]() { handleHealth(); });
  _server.on("/api/state", HTTP_POST, [this]() { handleState(); });
  _server.on("/api/display", HTTP_POST, [this]() { handleDisplay(); });
  _server.on("/api/chime", HTTP_POST, [this]() { handleChime(); });
  _server.on("/api/mic", HTTP_GET, [this]() { handleMicStream(); });
  _server.on("/api/mic/record", HTTP_GET, [this]() { handleMicRecord(); });
  _server.on("/api/speak", HTTP_POST, [this]() { handleSpeakEnd(); }, [this]() { handleSpeakRaw(); });
  _server.on("/api/speak/raw", HTTP_POST, [this]() { handleSpeakEnd(); }, [this]() { handleSpeakRaw(); });
  _server.on("/api/stop", HTTP_POST, [this]() { handleStop(); });
  _server.on("/api/stop", HTTP_OPTIONS, [this]() {
    _server.sendHeader("Access-Control-Allow-Origin", "*");
    _server.sendHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
    _server.sendHeader("Access-Control-Allow-Headers", "*");
    _server.send(204);
  });
  _server.on("/api/speak", HTTP_OPTIONS, [this]() {
    _server.sendHeader("Access-Control-Allow-Origin", "*");
    _server.sendHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
    _server.sendHeader("Access-Control-Allow-Headers", "Content-Type");
    _server.send(204);
  });
  _server.on("/api/speak/raw", HTTP_OPTIONS, [this]() {
    _server.sendHeader("Access-Control-Allow-Origin", "*");
    _server.sendHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
    _server.sendHeader("Access-Control-Allow-Headers", "Content-Type");
    _server.send(204);
  });

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

    // Robust JSON state extraction (tolerant to spaces, quotes, newlines)
    int keyPos = body.indexOf("\"state\"");
    if (keyPos >= 0) {
      int colonPos = body.indexOf(':', keyPos + 7);
      if (colonPos >= 0) {
        int firstQuote = body.indexOf('"', colonPos + 1);
        if (firstQuote >= 0) {
          int secondQuote = body.indexOf('"', firstQuote + 1);
          if (secondQuote > firstQuote) {
            stateStr = body.substring(firstQuote + 1, secondQuote);
          }
        }
      }
    }

    // Robust numerical extraction
    int aIdx = body.indexOf("\"amplitude\"");
    if (aIdx >= 0) {
      int c = body.indexOf(':', aIdx + 11);
      if (c >= 0) amp = body.substring(c + 1).toFloat();
    }
    int bIdx = body.indexOf("\"bass\"");
    if (bIdx >= 0) {
      int c = body.indexOf(':', bIdx + 6);
      if (c >= 0) bass = body.substring(c + 1).toFloat();
    }
    int mIdx = body.indexOf("\"mid\"");
    if (mIdx >= 0) {
      int c = body.indexOf(':', mIdx + 5);
      if (c >= 0) mid = body.substring(c + 1).toFloat();
    }
    int tIdx = body.indexOf("\"treble\"");
    if (tIdx >= 0) {
      int c = body.indexOf(':', tIdx + 8);
      if (c >= 0) treble = body.substring(c + 1).toFloat();
    }
  }

  stateStr.toUpperCase();
  stateStr.trim();

  BuddyState targetState = rgbManager.getState();
  if (stateStr == "BOOTING") {
    targetState = STATE_BOOTING;
  } else if (stateStr == "IDLE" || stateStr == "COMPLETED" || stateStr == "INTERRUPTED" || stateStr == "READY" || stateStr == "DONE" || stateStr == "HAPPY") {
    targetState = STATE_IDLE;
  } else if (stateStr == "LISTENING") {
    targetState = STATE_LISTENING;
  } else if (stateStr == "THINKING") {
    targetState = STATE_THINKING;
  } else if (stateStr == "SPEAKING") {
    targetState = STATE_SPEAKING;
  } else if (stateStr == "ERROR") {
    targetState = STATE_ERROR;
  }

  rgbManager.setState(targetState);
  rgbManager.setAudioLevels(amp, bass, mid, treble);
  displayManager.setState(targetState);
  displayManager.setAudioLevel(amp);
  displayManager.update();
  rgbManager.update();

  _server.sendHeader("Access-Control-Allow-Origin", "*");
  _server.send(200, "application/json", "{\"ok\":true,\"state\":\"" + String(buddyStateToString(targetState)) + "\"}");
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

void WifiManager::handleMicRecord() {
  uint32_t seconds = 3;
  if (_server.hasArg("seconds")) {
    seconds = _server.arg("seconds").toInt();
    if (seconds < 1) seconds = 1;
    if (seconds > 10) seconds = 10;
  }

  uint32_t sampleRate = MIC_SAMPLE_RATE; // 16000 Hz
  size_t totalSamples = sampleRate * seconds;
  size_t pcmBytes = totalSamples * sizeof(int16_t);

  int16_t* pcmBuffer = (int16_t*)ps_malloc(pcmBytes);
  if (!pcmBuffer) {
    pcmBuffer = (int16_t*)malloc(pcmBytes);
  }
  if (!pcmBuffer) {
    _server.send(500, "text/plain", "Out of memory");
    return;
  }

  rgbManager.setState(STATE_LISTENING);
  displayManager.setState(STATE_LISTENING);
  displayManager.update();
  rgbManager.update();

  size_t samplesRecorded = 0;
  unsigned long startRec = millis();
  unsigned long lastDisplayTick = 0;
  while (samplesRecorded < totalSamples && (millis() - startRec < (seconds * 1000 + 2000))) {
    size_t remainingSamples = totalSamples - samplesRecorded;
    size_t chunk = (remainingSamples < 512) ? remainingSamples : 512;
    size_t readCount = microphoneManager.readSamples(pcmBuffer + samplesRecorded, chunk);
    if (readCount > 0) {
      samplesRecorded += readCount;
      displayManager.setAudioLevel(microphoneManager.getRecentEnergy());
    } else {
      delay(2);
    }

    // Actively animate the robot face and RGB LED at 40 FPS while user is speaking
    unsigned long now = millis();
    if (now - lastDisplayTick >= 25) {
      lastDisplayTick = now;
      displayManager.update();
      rgbManager.update();
    }
  }

  // Smoothly transition directly to THINKING state while audio is sent and processed
  rgbManager.setState(STATE_THINKING);
  displayManager.setState(STATE_THINKING);
  displayManager.update();
  rgbManager.update();

  // Standard 44-byte RIFF/WAVE header
  uint8_t header[44];
  uint32_t byteRate = sampleRate * 1 * sizeof(int16_t);
  uint16_t blockAlign = 1 * sizeof(int16_t);
  uint32_t dataSize = samplesRecorded * sizeof(int16_t);
  uint32_t riffSize = 36 + dataSize;

  memcpy(header, "RIFF", 4);
  header[4] = (uint8_t)(riffSize);
  header[5] = (uint8_t)(riffSize >> 8);
  header[6] = (uint8_t)(riffSize >> 16);
  header[7] = (uint8_t)(riffSize >> 24);
  memcpy(header + 8, "WAVEfmt ", 8);
  header[16] = 16; header[17] = 0; header[18] = 0; header[19] = 0;
  header[20] = 1; header[21] = 0;
  header[22] = 1; header[23] = 0;
  header[24] = (uint8_t)(sampleRate);
  header[25] = (uint8_t)(sampleRate >> 8);
  header[26] = (uint8_t)(sampleRate >> 16);
  header[27] = (uint8_t)(sampleRate >> 24);
  header[28] = (uint8_t)(byteRate);
  header[29] = (uint8_t)(byteRate >> 8);
  header[30] = (uint8_t)(byteRate >> 16);
  header[31] = (uint8_t)(byteRate >> 24);
  header[32] = (uint8_t)(blockAlign);
  header[33] = (uint8_t)(blockAlign >> 8);
  header[34] = 16; header[35] = 0;
  memcpy(header + 36, "data", 4);
  header[40] = (uint8_t)(dataSize);
  header[41] = (uint8_t)(dataSize >> 8);
  header[42] = (uint8_t)(dataSize >> 16);
  header[43] = (uint8_t)(dataSize >> 24);

  WiFiClient client = _server.client();
  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: audio/wav");
  client.println("Access-Control-Allow-Origin: *");
  client.print("Content-Length: ");
  client.println(44 + dataSize);
  client.println("Connection: close");
  client.println();

  client.write(header, 44);
  const size_t sendChunk = 1024;
  const uint8_t* pcmRaw = (const uint8_t*)pcmBuffer;
  for (size_t sent = 0; sent < dataSize; sent += sendChunk) {
    size_t remainingBytes = (size_t)(dataSize - sent);
    size_t toSend = (remainingBytes < sendChunk) ? remainingBytes : sendChunk;
    client.write(pcmRaw + sent, toSend);
  }

  free(pcmBuffer);
}

void WifiManager::handleSpeakRaw() {
  HTTPRaw& raw = _server.raw();
  if (raw.status == RAW_START) {
    _abortPlayback = false;
    LOG_PRINTLN("[Audio] Incoming speech stream started...");
    rgbManager.setState(STATE_SPEAKING);
    displayManager.setState(STATE_SPEAKING);
    displayManager.update();
    rgbManager.update();
  } else if (raw.status == RAW_WRITE) {
    if (_abortPlayback) {
      return; // Discard audio data if user interrupted speech
    }
    if (raw.currentSize > 0) {
      const int16_t* samples = (const int16_t*)raw.buf;
      size_t count = raw.currentSize / sizeof(int16_t);

      // Real-time speech amplitude estimation from PCM stream to drive lip-sync and LED EQ
      int32_t peak = 0;
      for (size_t i = 0; i < count; i += 8) {
        int32_t s = abs((int32_t)samples[i]);
        if (s > peak) peak = s;
      }
      float level = constrain((float)peak / 20000.0f, 0.05f, 1.0f);
      displayManager.setAudioLevel(level);
      rgbManager.setAudioLevels(level, level * 0.9f, level * 0.8f, level * 0.5f);

      audioOutput.writePcm(samples, count);

      // Actively refresh display and RGB animation while playing audio chunk
      displayManager.update();
      rgbManager.update();
    }
  } else if (raw.status == RAW_END) {
    if (_abortPlayback) {
      rgbManager.setState(STATE_IDLE);
      displayManager.setState(STATE_IDLE);
      displayManager.update();
      rgbManager.update();
      return;
    }
    LOG_PRINTLN("[Audio] Speech stream completed. Draining I2S buffer...");
    // Keep mouth speaking and LED active while remaining DMA samples drain out of speaker
    unsigned long startDrain = millis();
    while (millis() - startDrain < 350) {
      displayManager.update();
      rgbManager.update();
      delay(15);
    }
    rgbManager.setState(STATE_IDLE);
    displayManager.setState(STATE_IDLE);
    displayManager.update();
    rgbManager.update();
  } else if (raw.status == RAW_ABORTED) {
    LOG_PRINTLN("[Audio] Speech stream aborted.");
    rgbManager.setState(STATE_IDLE);
    displayManager.setState(STATE_IDLE);
    displayManager.update();
    rgbManager.update();
  }
}

void WifiManager::handleSpeakEnd() {
  _server.sendHeader("Access-Control-Allow-Origin", "*");
  _server.send(200, "application/json", "{\"ok\":true,\"message\":\"Playback finished\"}");
}

void WifiManager::handleStop() {
  LOG_PRINTLN("[Control] Emergency Stop / Interrupt requested.");
  _abortPlayback = true;
  audioOutput.stop();
  bool resetToIdle = true;
  if (_server.hasArg("idle") && _server.arg("idle") == "0") {
    resetToIdle = false;
  }
  if (resetToIdle) {
    rgbManager.setState(STATE_IDLE);
    displayManager.setState(STATE_IDLE);
    displayManager.update();
    rgbManager.update();
  }
  _server.sendHeader("Access-Control-Allow-Origin", "*");
  _server.send(200, "application/json", "{\"ok\":true,\"stopped\":true}");
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
