/*
 * =====================================================================================
 * BUDDY AI — HARDWARE TEST 6: Push Buttons & Auxiliary LEDs
 * Hardware Wiring:
 *   Tactile Push Button -> Connected between GPIO 1 and GND (uses INPUT_PULLUP)
 *   Onboard BOOT Button -> GPIO 0 (built-in pull-up)
 *   External Status LED -> Anode to GPIO 2 via 220 Ohm resistor, Cathode to GND
 * =====================================================================================
 */

#define PIN_BUTTON_EXT  1
#define PIN_BUTTON_BOOT 0
#define PIN_LED_STATUS  2

bool lastExtBtn = HIGH;
bool lastBootBtn = HIGH;
unsigned long lastDebounceExt = 0;
unsigned long lastDebounceBoot = 0;
const unsigned long debounceTime = 40;

void setup() {
  Serial.begin(115200);
  Serial0.begin(115200);
  delay(500);

  Serial.println("\n========================================================");
  Serial.println("  BUDDY AI — TEST 6: Buttons & Auxiliary LEDs Check     ");
  Serial.println("========================================================");

  pinMode(PIN_BUTTON_EXT, INPUT_PULLUP);
  pinMode(PIN_BUTTON_BOOT, INPUT_PULLUP);
  pinMode(PIN_LED_STATUS, OUTPUT);

  // Blink external LED 3 times to verify current
  Serial.println("[LED] Testing external LED on GPIO 2 (3 blinks)...");
  for (int i = 0; i < 3; i++) {
    digitalWrite(PIN_LED_STATUS, HIGH);
    delay(200);
    digitalWrite(PIN_LED_STATUS, LOW);
    delay(200);
  }

  Serial.println("[Buttons] Press the external button (GPIO 1) or BOOT button (GPIO 0).");
  Serial.println("========================================================");
}

void loop() {
  // 1. External Button on GPIO 1
  int readExt = digitalRead(PIN_BUTTON_EXT);
  if (readExt != lastExtBtn) {
    lastDebounceExt = millis();
  }
  if ((millis() - lastDebounceExt) > debounceTime) {
    if (readExt == LOW && lastExtBtn == HIGH) {
      Serial.println("[Button Event] External Button (GPIO 1) PRESSED!");
      digitalWrite(PIN_LED_STATUS, HIGH);
    } else if (readExt == HIGH && lastExtBtn == LOW) {
      Serial.println("[Button Event] External Button (GPIO 1) RELEASED.");
      digitalWrite(PIN_LED_STATUS, LOW);
    }
  }
  lastExtBtn = readExt;

  // 2. Onboard BOOT Button on GPIO 0
  int readBoot = digitalRead(PIN_BUTTON_BOOT);
  if (readBoot != lastBootBtn) {
    lastDebounceBoot = millis();
  }
  if ((millis() - lastDebounceBoot) > debounceTime) {
    if (readBoot == LOW && lastBootBtn == HIGH) {
      Serial.println("[Button Event] Onboard BOOT Button (GPIO 0) PRESSED!");
      digitalWrite(PIN_LED_STATUS, HIGH);
    } else if (readBoot == HIGH && lastBootBtn == LOW) {
      Serial.println("[Button Event] Onboard BOOT Button (GPIO 0) RELEASED.");
      digitalWrite(PIN_LED_STATUS, LOW);
    }
  }
  lastBootBtn = readBoot;

  delay(10);
}
