/*
 * =====================================================================================
 * BUDDY AI — ST7789 2.8-inch SPI TFT LCD Display Manager
 * Resolution: 240 x 320 Portrait
 * Hardware: ST7789 (SCL=12, SDA=11, CS=10, DC=9, RST=13, BLK=14)
 * =====================================================================================
 */

#pragma once

#include "config.h"
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>

class DisplayManager {
public:
  DisplayManager();

  void begin();
  void setState(BuddyState state);
  void setWifiInfo(const String& ssid, const String& ip);
  void setMessage(const String& title, const String& body);
  void setAudioLevel(float level);
  void update(); // Called in loop()

private:
  Adafruit_ST7789 _tft;
  BuddyState _currentState;
  unsigned long _lastAnimUpdate;
  unsigned long _stateStartTime;
  
  String _ssid;
  String _ip;
  String _messageTitle;
  String _messageBody;
  float _audioLevel;
  
  uint8_t _animFrame;
  bool _needsFullRedraw;

  void drawHeader();
  void drawStatusCard();
  void drawRobotFace(unsigned long elapsed);
  void drawSpeechWaveform();
  void drawFooter();
  void clearContentArea();
};

extern DisplayManager displayManager;
