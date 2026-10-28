# PROJECT: BUDDY AI — ESP32-S3 COMPLETE HARDWARE INTEGRATION

Act as a senior embedded systems engineer specializing in ESP32-S3 development, I²S audio, SPI displays, Wi-Fi communication, and AI-powered reception robots.

I am building BUDDY AI, an AI-powered college reception robot for Anantrao Pawar College of Engineering & Research (APCOER), Pune.

My architecture is:

* Windows PC runs the AI agent, speech recognition, knowledge retrieval, and text-to-speech.
* ESP32-S3 handles the display, microphone, speaker output, RGB LED, buttons, and Wi-Fi communication.
* The PC and ESP32-S3 communicate over the local Wi-Fi network.

Your job is to inspect my existing BUDDY AI project and prepare the complete hardware integration so that I can connect the physical components safely, one at a time.

Do not merely explain the design. Create the firmware, configuration, pin map, wiring documentation, test programs, and integration instructions in my existing workspace.

IMPORTANT: Do not claim that physical hardware has been tested unless it has actually been connected and tested.

# 1. MY HARDWARE

I have purchased the following parts.

## Main controller

ESP32-S3 N16R8 development board:

* ESP32-S3 microcontroller
* 16 MB flash
* 8 MB PSRAM
* Wi-Fi
* Two USB-C ports labelled USB and COM
* Onboard WS2812-compatible RGB LED
* Board configuration previously used successfully: ESP32S3 Dev Module
* COM port used for uploading and serial debugging

The onboard RGB LED has successfully been turned red using:

rgbLedWrite(48, 50, 0, 0);

Use GPIO 48 as the initial RGB LED pin because that test worked on my board.

Do not change this pin unless a technical conflict or verified board specification requires it.

## Microphone

INMP441 omnidirectional I²S microphone module.

The module has soldered pins.

Expected signal pins include:

* VDD
* GND
* SCK
* WS
* SD
* L/R

Verify the exact pin labels from the module documentation or product specifications before creating the final wiring table.

## Audio amplifier

MAX98357A I²S Class-D amplifier module.

Expected signals include:

* VIN
* GND
* BCLK
* LRC
* DIN
* SD or EN, if present
* Speaker output terminals

Verify the actual module labels before specifying wiring.

## Display

2.8-inch ST7789 TFT LCD:

* 240 × 320 pixels
* SPI interface
* Soldered pins
* Expected labels: GND, VCC, SCL, SDA, RES, DC, BLK

Verify the exact module pinout and supply-voltage requirements.

Do not assume the module's VCC input is 5 V tolerant.

## Speaker

Passive 4 Ω or 8 Ω speaker compatible with the MAX98357A.

Verify the speaker's actual impedance and power rating before recommending output settings.

## Additional parts

* 830-point solderless breadboard.
* Male-to-male Dupont jumper wires.
* Male-to-female Dupont jumper wires.
* Female-to-female Dupont jumper wires.
* USB data cable.
* 5 V, 2 A USB power adapter.
* Momentary tactile push buttons.
* Assorted LEDs.
* 220 Ω resistors.
* 10 kΩ resistors.
* Foam board or cardboard enclosure.
* M2/M3 screws, nuts, and spacers.
* Double-sided tape or hot glue.
* Cable ties.
* Optional perfboard.

# 2. INSPECT MY EXISTING PROJECT FIRST

Before creating or changing code:

1. Inspect the existing project files.
2. Identify the current AI agent architecture.
3. Identify the existing Python or other PC-side application.
4. Identify existing TTS and audio playback code.
5. Identify existing ESP32 firmware.
6. Check which libraries and frameworks are already installed.
7. Preserve existing working functionality.
8. Do not replace the AI application unnecessarily.
9. Create separate hardware modules where practical.
10. Clearly identify files that are new versus modified.

# 3. VERIFY THE HARDWARE BEFORE ASSIGNING PINS

This step is mandatory.

Use official documentation or verified specifications for:

* ESP32-S3 GPIO capabilities and restrictions.
* INMP441 microphone pinout and voltage requirements.
* MAX98357A module pinout and voltage requirements.
* ST7789 display controller interface and module voltage requirements.
* Onboard WS2812 LED connection.
* Speaker impedance and power rating.

Where a module's exact revision is unknown, distinguish verified facts from assumptions.

Do not invent a GPIO assignment or module pinout.

Create a hardware verification report listing:

* Verified information.
* Information inferred from common module designs.
* Information that must be confirmed from physical labels or datasheets.

If a critical hardware detail cannot be established, clearly flag it instead of pretending it is known.

# 4. CREATE A COMPLETE GPIO ALLOCATION PLAN

Allocate ESP32-S3 pins for:

1. ST7789 SPI display.
2. INMP441 I²S microphone.
3. MAX98357A I²S amplifier.
4. Onboard WS2812 RGB LED.
5. Optional tactile buttons.
6. Optional external indicator LEDs.

The GPIO plan must:

* Avoid pin conflicts.
* Respect input/output capabilities.
* Avoid flash/PSRAM pins.
* Avoid problematic boot-strapping pins where possible.
* Avoid interfering with USB functionality.
* Avoid reserving the same pin for multiple peripherals.
* Keep the microphone and amplifier I²S signals logically compatible where appropriate.
* Account for the onboard RGB LED on GPIO 48.
* Use clearly documented, configurable pin constants.
* Keep future expansion in mind.

The INMP441 and MAX98357A both use I²S, but they have different data directions.

If practical, design the firmware to share suitable I²S clock signals while keeping microphone data input and speaker data output separate.

Do not assume that every I²S signal can be shared without checking the ESP32-S3 I²S peripheral and driver configuration.

Provide one recommended pin allocation and a concise explanation of why it was selected.

Do not generate the final physical wiring instructions until the pin allocation has been checked for conflicts.

# 5. CREATE THE MASTER WIRING TABLE

Create a detailed wiring document:

docs/BUDDY_WIRING_GUIDE.md

Include a master table with these columns:

* Component.
* Component pin label.
* ESP32-S3 GPIO or power connection.
* Wire type.
* Signal direction.
* Voltage level.
* Purpose.
* Important precautions.

Create separate sections for:

A. ST7789 TFT display.
B. INMP441 microphone.
C. MAX98357A amplifier.
D. Passive speaker.
E. Onboard WS2812 RGB LED.
F. Optional push buttons.
G. Optional external LEDs.
H. Power and grounding.

For every connection, specify the actual physical pin label and the assigned ESP32 GPIO.

Do not rely on ambiguous labels such as "connect to SPI" or "connect to I²S".

Provide a clear, numbered connection list.

If a signal requires a level shifter or other component, identify it explicitly.

Do not recommend connecting a 5 V signal directly to an ESP32-S3 GPIO.

# 6. POWER AND ELECTRICAL SAFETY

Create a separate power-planning section.

Requirements:

* Keep the ESP32-S3 logic at its supported voltage.
* Verify whether the display accepts 3.3 V logic and determine its correct supply voltage.
* Verify the INMP441 supply voltage.
* Verify the MAX98357A module's supported supply range.
* Determine whether the speaker power demand is appropriate.
* Keep all grounds connected where required for signal reference.
* Do not connect the passive speaker directly to ESP32 GPIO pins.
* Connect the speaker only to the amplifier's speaker outputs.
* Do not connect either speaker output to ground.
* Do not feed 5 V into an ESP32 GPIO.
* Avoid powering several high-current loads through a weak USB source.
* Do not connect two power supplies together without a verified power architecture.
* Clearly distinguish the ESP32's USB supply, peripheral power, and any external 5 V supply.
* Identify current limits and practical power risks.
* Recommend a safe common-ground arrangement where applicable.

The available 5 V, 2 A adapter must not automatically be assumed sufficient for every possible configuration. Estimate the expected load based on verified component specifications.

If an external power supply is required, explain how to avoid backfeeding the USB port.

# 7. CREATE THE ESP32 FIRMWARE STRUCTURE

Create a modular Arduino firmware project.

Suggested structure:

firmware/
buddy_esp32/
buddy_esp32.ino
config.h
display_manager.h
display_manager.cpp
microphone_manager.h
microphone_manager.cpp
audio_output.h
audio_output.cpp
rgb_manager.h
rgb_manager.cpp
wifi_manager.h
wifi_manager.cpp
README.md

Adapt the structure to the project's needs.

Use the appropriate official or maintained libraries for:

* ST7789 display.
* I²S microphone capture.
* I²S audio output.
* RGB LED control.
* Wi-Fi communication.

Verify library APIs and compatibility with the installed ESP32 Arduino core version.

Do not include fictional functions or nonexistent library APIs.

Keep pin definitions centralized in config.h.

Avoid unnecessary libraries and duplicated drivers.

# 8. DISPLAY IMPLEMENTATION

Create a display manager for the ST7789 TFT.

The initial screen should show:

BUDDY AI

Status: Starting...
Wi-Fi: Disconnected
AI Agent: Offline

Once Wi-Fi connects, update the status.

Support these display states:

* Starting.
* Ready.
* Listening.
* Thinking.
* Speaking.
* Error.

Keep the layout suitable for a 240 × 320 portrait display.

Use readable fonts, clear spacing, and a simple interface.

Avoid redrawing the entire screen unnecessarily.

Provide a display-only diagnostic sketch or test mode that can be run independently.

Confirm the required display rotation, offsets, SPI configuration, and initialization sequence using the actual module specification or a testable configuration.

Do not assume that every ST7789 module has identical offsets.

# 9. MICROPHONE IMPLEMENTATION

Create an INMP441 microphone manager.

Requirements:

* Configure the verified I²S pins.
* Configure the correct I²S receive mode.
* Read audio samples into a buffer.
* Handle buffer limits and read errors.
* Use a suitable sample rate for speech recognition.
* Provide a diagnostic mode that reports whether samples are being captured.
* Avoid sending raw microphone audio to unrelated destinations.
* Make the audio format and sample rate configurable.
* Do not claim speech recognition is working merely because the I²S peripheral initializes.

Provide a microphone test that can verify:

* Successful I²S initialization.
* Nonzero sample data.
* Reasonable response to nearby speech or sound.
* Stable operation without repeated errors.

Do not print every sample to the serial monitor.

# 10. SPEAKER AND AMPLIFIER IMPLEMENTATION

Create an audio output manager for the MAX98357A.

Requirements:

* Configure the verified I²S output pins.
* Use a compatible sample rate and audio format.
* Support mono audio where appropriate.
* Handle buffer underruns and errors.
* Support audio playback received from the PC.
* Keep the passive speaker connected to the amplifier output only.
* Include a low-volume audio test.
* Provide a way to stop playback safely.
* Do not attempt to stream large unbounded audio buffers into RAM.

Initially test a short generated tone or short PCM audio clip.

Keep the default volume low.

Document the amplifier's supported input formats and any mono/channel requirements that affect playback.

Do not assume the MAX98357A is a Bluetooth receiver.

# 11. WIFI COMMUNICATION WITH THE PC

The PC runs BUDDY AI; the ESP32 is a peripheral controller.

Create a simple, reliable communication interface between them.

Inspect the existing application before choosing HTTP, WebSocket, or another protocol.

Requirements:

* Both devices must be on the same local network.
* Do not hardcode an unverified IP address.
* Provide configurable Wi-Fi credentials.
* Do not commit passwords to source control.
* Report the ESP32 IP address over Serial.
* Provide a health-check endpoint or equivalent status message.
* Support display status updates.
* Support LED state updates.
* Support microphone audio transport.
* Support speaker audio transport.
* Handle disconnects and reconnects.
* Avoid blocking the UI or audio playback unnecessarily.
* Do not expose the ESP32 server to the public internet.

Use bounded buffers and backpressure for audio streaming.

Avoid sending an entire long audio response as one large memory allocation.

# 12. RGB LED IMPLEMENTATION

Use the known working onboard WS2812 LED connection:

GPIO 48.

Use rgbLedWrite() if it is supported by the installed ESP32 Arduino core.

Implement:

* IDLE: dim cyan breathing.
* LISTENING: blue pulse.
* THINKING: amber pulse.
* SPEAKING: smooth purple breathing.
* ERROR: gentle red pulse.

Use non-blocking animation based on millis().

Do not let LED animation block Wi-Fi, audio capture, or playback.

Keep the LED responsive to state changes.

Do not add external LEDs unless explicitly needed.

# 13. PUSH BUTTONS AND INDICATOR LEDS

Treat additional buttons and external LEDs as optional features.

If implementing buttons:

* Use debouncing.
* Document the required pull-up or pull-down arrangement.
* Avoid using pins already assigned to other peripherals.
* Provide configurable behavior.

If implementing external indicator LEDs:

* Use appropriate current-limiting resistors.
* Document polarity.
* Verify GPIO current limits.
* Do not assume every LED has the same forward voltage.

Do not let optional components delay the core microphone, display, speaker, and Wi-Fi implementation.

# 14. PC-SIDE INTEGRATION

Inspect the existing BUDDY application and create the minimum necessary modules to communicate with the ESP32.

If the PC application is Python-based, reuse the current Python environment and installed dependencies.

The PC should:

* Receive microphone audio from the ESP32 if the ESP32 microphone is used.
* Pass captured audio to the existing speech recognition pipeline.
* Process the user request using the existing AI agent and knowledge base.
* Generate speech using the existing TTS system.
* Stream or transmit audio to the ESP32 for playback.
* Update the display and RGB LED.
* Handle interruptions and errors.
* Keep the application functional if the hardware disconnects.

Do not duplicate the AI agent, speech recognition system, knowledge base, or TTS pipeline unnecessarily.

If an existing component is not yet implemented, create a clear interface and document the missing integration.

# 15. INTEGRATION AND TESTING ORDER

Create separate tests that allow me to connect and test one component at a time.

Recommended order:

TEST 1:
ESP32 board, serial output, and Wi-Fi.

TEST 2:
Onboard RGB LED.

TEST 3:
ST7789 display.

TEST 4:
INMP441 microphone.

TEST 5:
MAX98357A amplifier and speaker.

TEST 6:
Buttons and optional external LEDs.

TEST 7:
PC-to-ESP32 communication.

TEST 8:
Microphone audio transport.

TEST 9:
Speaker audio transport.

TEST 10:
Full BUDDY AI integration.

Each test must have:

* Its own test sketch or clear test mode.
* A wiring reference.
* Expected output.
* Troubleshooting steps.
* A clear pass/fail criterion.

Do not connect every component at once.

Do not assume a component works because the firmware compiles.

# 16. REQUIRED DOCUMENTATION

Create:

docs/BUDDY_WIRING_GUIDE.md
docs/BUDDY_PIN_MAP.md
docs/BUDDY_POWER_GUIDE.md
docs/BUDDY_HARDWARE_TEST_PLAN.md
docs/BUDDY_HARDWARE_TROUBLESHOOTING.md

Include:

* Master wiring table.
* GPIO assignments.
* Power connections.
* Voltage requirements.
* Signal directions.
* Breadboard setup.
* Required libraries.
* Firmware upload instructions.
* Test sketches.
* Expected results.
* Common mistakes.
* Safe connection and disconnection procedures.

Provide a clear step-by-step guide for a beginner.

If diagrams can be generated accurately, include a pin-to-pin diagram. If the exact board layout is unknown, use a clearly labelled logical wiring diagram rather than inventing physical pin positions.

# 17. FINAL REVIEW

Before declaring the implementation ready:

1. Verify that every assigned GPIO is unique where required.
2. Verify that the onboard RGB LED pin remains GPIO 48 unless a verified conflict exists.
3. Check I²S signal directions.
4. Check SPI signal assignments.
5. Check power and ground arrangements.
6. Check all component voltage requirements.
7. Check library compatibility.
8. Compile the firmware if the required toolchain is available.
9. Run PC-side tests where possible.
10. Record all unverified assumptions.
11. Identify anything that requires physical testing.
12. Preserve the existing AI application.

Do not claim that the physical wiring has been verified.

# DELIVERABLES

I want:

* A verified GPIO allocation plan.
* A master wiring table.
* A power and voltage guide.
* Complete firmware source files.
* Independent component test programs.
* PC integration modules.
* Setup instructions.
* Troubleshooting documentation.
* A list of files created or changed.
* A clear report of what is ready and what still needs verification.

Start by inspecting the existing repository and verifying the hardware documentation. Then prepare the pin map and wiring documentation before finalizing the firmware.
