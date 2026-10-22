/*
 * =====================================================================================
 * BUDDY AI — Wi-Fi & WebServer Manager
 * =====================================================================================
 */

#pragma once

#include "config.h"
#include <WiFi.h>
#include <WebServer.h>

class WifiManager {
public:
  WifiManager();

  void begin(const char* ssid = WIFI_SSID_DEFAULT, const char* password = WIFI_PASS_DEFAULT);
  void update(); // Called in loop()

  bool isConnected() const;
  String getIpAddress() const;
  int8_t getRssi() const;

private:
  WebServer _server;
  const char* _ssid;
  const char* _password;
  unsigned long _lastReconnectAttempt;
  bool _wasConnected;

  void setupRoutes();
  void handleHealth();
  void handleState();
  void handleDisplay();
  void handleChime();
  void handleMicStream();
  void handleSpeakStream();
};

extern WifiManager wifiManager;
