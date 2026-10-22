/*
 * =====================================================================================
 * BUDDY AI — ST7789 Display Manager Implementation
 * =====================================================================================
 */

#include "display_manager.h"

// Color Palette (RGB565 format)
#define COLOR_BG          0x0821  // Deep tech dark navy
#define COLOR_CARD_BG     0x1084  // Subtle slate card
#define COLOR_ACCENT      0x05BF  // Vibrant electric cyan
#define COLOR_TEXT        0xFFFF  // Crisp white
#define COLOR_TEXT_MUTED  0x9CD3  // Soft gray
#define COLOR_SUCCESS     0x2E65  // Emerald green
#define COLOR_AMBER       0xFD20  // Warm amber
#define COLOR_ALERT       0xF800  // Red

DisplayManager displayManager;

DisplayManager::DisplayManager()
  : _tft(PIN_TFT_CS, PIN_TFT_DC, PIN_TFT_MOSI, PIN_TFT_SCLK, PIN_TFT_RST),
    _currentState(STATE_BOOTING),
    _lastAnimUpdate(0),
    _stateStartTime(0),
    _ssid("Connecting..."),
    _ip("0.0.0.0"),
    _messageTitle("Welcome"),
    _messageBody("APCOER College Reception Robot"),
    _audioLevel(0.0f),
    _animFrame(0),
    _needsFullRedraw(true) {}

void DisplayManager::begin() {
  // Initialize Backlight pin if defined
  if (PIN_TFT_BLK >= 0) {
    pinMode(PIN_TFT_BLK, OUTPUT);
    digitalWrite(PIN_TFT_BLK, HIGH); // Turn backlight ON
  }

  // Initialize ST7789 controller in 240x320 mode
  _tft.init(TFT_WIDTH, TFT_HEIGHT);
  _tft.setRotation(TFT_ROTATION);
  _tft.fillScreen(COLOR_BG);

  _stateStartTime = millis();
  _needsFullRedraw = true;
  drawHeader();
  drawStatusCard();
  drawFooter();

  LOG_PRINTLN("[Display] ST7789 240x320 initialized successfully.");
}

void DisplayManager::setState(BuddyState state) {
  if (_currentState != state) {
    _currentState = state;
    _stateStartTime = millis();
    _animFrame = 0;
    drawStatusCard();
    clearContentArea();
  }
}

void DisplayManager::setWifiInfo(const String& ssid, const String& ip) {
  _ssid = ssid;
  _ip = ip;
  drawFooter();
}

void DisplayManager::setMessage(const String& title, const String& body) {
  _messageTitle = title;
  _messageBody = body;
  clearContentArea();

  _tft.setCursor(14, 185);
  _tft.setTextColor(COLOR_ACCENT);
  _tft.setTextSize(2);
  _tft.println(_messageTitle);

  _tft.setCursor(14, 210);
  _tft.setTextColor(COLOR_TEXT);
  _tft.setTextSize(1);
  _tft.println(_messageBody);
}

void DisplayManager::setAudioLevel(float level) {
  _audioLevel = constrain(level, 0.0f, 1.0f);
}

void DisplayManager::clearContentArea() {
  _tft.fillRect(10, 80, 220, 195, COLOR_BG);
}

void DisplayManager::drawHeader() {
  _tft.fillRect(0, 0, 240, 40, COLOR_CARD_BG);
  
  _tft.setCursor(14, 10);
  _tft.setTextColor(COLOR_ACCENT);
  _tft.setTextSize(2);
  _tft.print("BUDDY AI");

  _tft.setCursor(145, 14);
  _tft.setTextColor(COLOR_TEXT_MUTED);
  _tft.setTextSize(1);
  _tft.print("APCOER PUNE");

  _tft.drawFastHLine(0, 40, 240, COLOR_ACCENT);
}

void DisplayManager::drawStatusCard() {
  _tft.fillRect(10, 48, 220, 26, COLOR_CARD_BG);
  _tft.drawRoundRect(10, 48, 220, 26, 4, COLOR_TEXT_MUTED);

  _tft.setCursor(18, 55);
  _tft.setTextSize(1);
  _tft.setTextColor(COLOR_TEXT_MUTED);
  _tft.print("STATUS: ");

  uint16_t statusColor = COLOR_ACCENT;
  const char* statusText = "Ready";

  switch (_currentState) {
    case STATE_BOOTING:
      statusColor = COLOR_AMBER;
      statusText = "Starting...";
      break;
    case STATE_IDLE:
      statusColor = COLOR_SUCCESS;
      statusText = "Ready (Online)";
      break;
    case STATE_LISTENING:
      statusColor = 0x05BF;
      statusText = "Listening...";
      break;
    case STATE_THINKING:
      statusColor = COLOR_AMBER;
      statusText = "Thinking...";
      break;
    case STATE_SPEAKING:
      statusColor = 0xC1BF; // Purple/magenta
      statusText = "Speaking...";
      break;
    case STATE_ERROR:
      statusColor = COLOR_ALERT;
      statusText = "Connection Error";
      break;
    default:
      break;
  }

  _tft.setTextColor(statusColor);
  _tft.print(statusText);
}

void DisplayManager::drawRobotFace(unsigned long elapsed) {
  // Center of Robot Face
  int centerX = 120;
  int centerY = 130;

  // Face outer frame
  _tft.drawRoundRect(centerX - 50, centerY - 40, 100, 80, 14, COLOR_ACCENT);

  // Animated Eyes
  bool blinking = ((elapsed % 4000) > 3800); // Blink every 4 seconds for 200ms
  
  if (blinking) {
    // Closed eye line
    _tft.fillRect(centerX - 30, centerY - 10, 20, 3, COLOR_ACCENT);
    _tft.fillRect(centerX + 10, centerY - 10, 20, 3, COLOR_ACCENT);
  } else {
    // Open expressive eyes
    _tft.fillCircle(centerX - 20, centerY - 10, 8, COLOR_ACCENT);
    _tft.fillCircle(centerX + 20, centerY - 10, 8, COLOR_ACCENT);
    // Eye shine dot
    _tft.fillCircle(centerX - 18, centerY - 12, 2, COLOR_TEXT);
    _tft.fillCircle(centerX + 22, centerY - 12, 2, COLOR_TEXT);
  }

  // Mouth Animation based on state
  if (_currentState == STATE_SPEAKING) {
    // Speaking waveform mouth
    int mouthH = (int)(6 + _audioLevel * 16.0f);
    _tft.fillRoundRect(centerX - 25, centerY + 15 - mouthH / 2, 50, mouthH, 4, 0xC1BF);
  } else if (_currentState == STATE_LISTENING) {
    // Listening O-shape mouth
    _tft.drawCircle(centerX, centerY + 18, 6, COLOR_ACCENT);
  } else {
    // Gentle friendly smile
    _tft.drawFastHLine(centerX - 18, centerY + 18, 36, COLOR_ACCENT);
    _tft.drawPixel(centerX - 19, centerY + 17, COLOR_ACCENT);
    _tft.drawPixel(centerX + 19, centerY + 17, COLOR_ACCENT);
  }
}

void DisplayManager::drawFooter() {
  _tft.fillRect(0, 285, 240, 35, COLOR_CARD_BG);
  _tft.drawFastHLine(0, 285, 240, COLOR_TEXT_MUTED);

  _tft.setCursor(12, 292);
  _tft.setTextSize(1);
  _tft.setTextColor(COLOR_TEXT_MUTED);
  _tft.print("Wi-Fi: ");
  _tft.setTextColor(COLOR_TEXT);
  _tft.print(_ssid);

  _tft.setCursor(12, 305);
  _tft.setTextColor(COLOR_TEXT_MUTED);
  _tft.print("IP: ");
  _tft.setTextColor(COLOR_ACCENT);
  _tft.print(_ip);
}

void DisplayManager::update() {
  unsigned long now = millis();
  if (now - _lastAnimUpdate < 60) { // ~16 FPS visualizer
    return;
  }
  _lastAnimUpdate = now;
  unsigned long elapsed = now - _stateStartTime;

  // Refresh dynamic face & visualizer
  drawRobotFace(elapsed);
}
