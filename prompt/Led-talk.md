# PROJECT: BUDDY AI — Speech-Reactive Onboard RGB LED

You are an expert embedded systems engineer and Python AI integration developer. Your task is to implement a reliable, fully integrated speech-reactive RGB LED system for my college reception robot, BUDDY AI.

Do not just explain the implementation. Inspect my existing project, understand its architecture, implement the necessary code, test it where possible, and provide clear instructions for running it.

## 1. HARDWARE CONFIGURATION

My hardware is:

* Microcontroller: ESP32-S3 N16R8.
* Flash: 16 MB.
* PSRAM: 8 MB.
* Development environment: Arduino IDE and ESP32 Arduino core.
* Board profile: ESP32S3 Dev Module.
* USB connection: I use the COM/UART port for uploading and serial debugging.
* Onboard RGB LED: WS2812-compatible addressable RGB LED.
* The LED has been successfully controlled using the ESP32 Arduino core function `rgbLedWrite()`.
* The GPIO used by my currently working LED test is GPIO 48.
* The computer runs Windows.
* My PC has an NVIDIA RTX 4060 with 8 GB VRAM and 16 GB system RAM.

IMPORTANT HARDWARE RULES:

1. Use GPIO 48 as the initial LED data pin because my test using `rgbLedWrite(48, ...)` successfully turned the LED red.
2. Do not randomly change GPIO pins.
3. Do not assume a different RGB LED library is required. First verify that `rgbLedWrite()` works with my installed ESP32 Arduino core.
4. Use the built-in `rgbLedWrite()` function for the onboard LED unless inspection establishes a compatibility problem.
5. Do not modify unrelated board settings, PSRAM settings, boot configuration, or existing hardware drivers.
6. Keep the LED brightness at a safe, moderate level.
7. Do not interfere with the small red power/status indicator.
8. Avoid blocking delays in the main LED control loop.

## 2. PRIMARY OBJECTIVE

Make the onboard WS2812 LED react automatically to BUDDY's actual AI interaction state.

Required states:

* BOOTING
* IDLE
* LISTENING
* THINKING
* SPEAKING
* INTERRUPTED
* ERROR

The LED must be controlled by the PC application through Wi-Fi.

The PC is responsible for AI processing, speech recognition, language model interaction, and text-to-speech generation.

The ESP32-S3 is responsible for receiving state updates and rendering smooth LED animations.

Do not run the AI language model or TTS model on the ESP32.

## 3. INSPECT THE EXISTING PROJECT FIRST

Before writing or modifying code:

1. Inspect all project folders and existing source files.
2. Identify the main application entry point.
3. Identify the current AI agent framework.
4. Identify the speech recognition implementation.
5. Identify the text-to-speech implementation.
6. Identify the actual audio playback mechanism.
7. Identify how the application determines that the agent has started and finished speaking.
8. Identify the current Wi-Fi, server, and API architecture.
9. Check whether an ESP32 firmware sketch already exists.
10. Identify dependencies, environment variables, and run commands.

Preserve the existing architecture whenever practical.

Do not replace the entire application with a new implementation.

Do not invent file names, framework names, API functions, or existing integration points without inspecting the repository.

If a required component does not exist yet, create a minimal, clearly documented integration layer.

If you cannot determine the current TTS or playback implementation, explain what you discovered and build a modular integration that can be connected to it later.

## 4. SYSTEM ARCHITECTURE

Implement the following architecture:

PC BUDDY application
|
| Detect interaction state
|
| Send state updates over Wi-Fi
v
ESP32-S3 HTTP server or WebSocket server
|
| Validate incoming state
v
Non-blocking LED state machine
|
v
Onboard WS2812 RGB LED

Choose HTTP or WebSocket after inspecting the existing project.

For the first implementation, prefer a simple HTTP interface if that makes integration easier. A persistent WebSocket connection is acceptable if the project already uses one.

Do not introduce unnecessary infrastructure.

The ESP32 must not need internet access to communicate with the PC. Communication should work on the same local Wi-Fi network.

## 5. LED ANIMATION DESIGN

Create attractive, smooth animations that make BUDDY feel alive.

Use the following behavior:

### BOOTING

* Brief cyan animation.
* Fade into IDLE.
* Do not block startup for long.

### IDLE

* Very dim cyan or blue.
* Slow, gentle breathing effect.
* Brightness should remain low enough not to be distracting.

### LISTENING

* Blue breathing pulse.
* Faster pulse than IDLE.
* Clearly communicate that BUDDY is listening to a person.

### THINKING

* Warm amber/yellow breathing effect.
* Use a subtle moving or pulsing brightness pattern.
* Avoid rapid flashing.

### SPEAKING

* Purple/magenta animated breathing.
* Make the LED brighten and dim smoothly while BUDDY's voice is playing.
* Add subtle color variation between purple and magenta.
* Use a smooth animation rather than simply switching the LED on and off.
* Keep the effect responsive to incoming state changes.

### INTERRUPTED

* Brief, gentle orange transition.
* Then return to IDLE.

### ERROR

* Red pulsing pattern.
* Avoid excessively rapid flashing.
* Return to a safe state when the error is cleared.

### COMPLETED SPEECH

* Optional short green or cyan acknowledgement.
* Then transition to IDLE.

Since there is only one onboard RGB LED, design animations that work well on a single pixel.

Do not implement multi-pixel effects that require additional LEDs.

## 6. IMPORTANT: USE REAL SPEECH PLAYBACK EVENTS

The SPEAKING state must correspond to actual audible TTS playback.

Do not set SPEAKING merely because:

* The LLM begins generating text.
* The TTS model begins synthesizing audio.
* A response string has been created.
* A network request begins.

Correct sequence:

1. User finishes speaking.
2. PC application processes the request.
3. LED enters THINKING.
4. TTS produces the response audio.
5. Audio playback starts.
6. LED enters SPEAKING.
7. LED remains in SPEAKING throughout actual audio playback.
8. Audio playback finishes.
9. LED briefly acknowledges completion if appropriate.
10. LED returns to IDLE.

If TTS streams audio in chunks, keep SPEAKING active throughout the complete playback session, not only while each chunk is generated.

If playback is interrupted by the user, send INTERRUPTED or transition to LISTENING as appropriate.

If audio playback fails, clear SPEAKING and transition to ERROR or IDLE.

Use actual playback start and completion callbacks wherever the existing audio library supports them.

If no playback callbacks exist, wrap the existing playback operation with a reliable start/finish lifecycle.

Do not use guessed audio durations as the primary way to detect when speech ends.

Do not monitor the computer's microphone or use voice-activity detection to guess when the PC is speaking if the application already knows when it starts and stops audio playback.

## 7. ESP32 FIRMWARE REQUIREMENTS

Create or update an Arduino firmware sketch for the ESP32-S3.

Suggested file:
`firmware/buddy_rgb_controller/buddy_rgb_controller.ino`

Adapt this path to the actual repository structure if needed.

Firmware requirements:

1. Connect to the configured local Wi-Fi network.
2. Use configuration constants or a clearly documented configuration file for Wi-Fi credentials.
3. Never commit real Wi-Fi passwords to source control.
4. Start a lightweight local HTTP or WebSocket server.
5. Accept LED state updates from the PC.
6. Validate incoming states.
7. Reject malformed or unknown state values.
8. Implement the LED animation state machine.
9. Use `rgbLedWrite(48, red, green, blue)` or the verified equivalent.
10. Use a non-blocking animation loop based on `millis()`.
11. Keep the device responsive while animations run.
12. Support repeated state changes without restarting the ESP32.
13. Automatically recover from temporary Wi-Fi disconnections.
14. Do not reboot continuously when the PC disconnects.
15. Return to IDLE after a configurable timeout without valid updates.
16. Include serial logs for startup, Wi-Fi status, server startup, received states, and errors.
17. Avoid printing Wi-Fi passwords or API keys.
18. Do not print excessive logs during every animation frame.
19. Provide an endpoint to inspect device status.
20. Include a test endpoint that allows manually setting the LED state.

Use a simple, consistent JSON format.

Example request:

POST /api/state

{
"state": "SPEAKING"
}

Other valid states:

* BOOTING
* IDLE
* LISTENING
* THINKING
* SPEAKING
* INTERRUPTED
* ERROR

Example successful response:

{
"ok": true,
"state": "SPEAKING"
}

Provide an endpoint such as:

GET /api/status

Example response:

{
"ok": true,
"state": "SPEAKING",
"device": "BUDDY-ESP32-S3"
}

Add a health-check endpoint:

GET /health

It should return a small JSON response indicating that the controller is alive.

If the existing project uses WebSockets, provide equivalent state messages and status reporting.

## 8. PC APPLICATION INTEGRATION

Create a small, reusable controller module in the language and framework already used by the project.

If the application is Python, an example module name is:

`buddy/hardware/rgb_controller.py`

Adapt this to the actual project structure.

Expose functions similar to:

* `set_led_state("IDLE")`
* `set_led_state("LISTENING")`
* `set_led_state("THINKING")`
* `set_led_state("SPEAKING")`
* `set_led_state("INTERRUPTED")`
* `set_led_state("ERROR")`

Add asynchronous versions if the application uses asyncio.

Requirements:

1. Use the ESP32 IP address discovered from its serial output, DHCP lease, or a configurable environment variable.
2. Do not hardcode an unverified IP address.
3. Provide a clear configuration option such as `BUDDY_ESP32_URL`.
4. Set reasonable connection and request timeouts.
5. Do not block the AI response-generation or audio-playback thread while sending LED updates.
6. Handle ESP32 disconnections gracefully.
7. Log LED communication failures without crashing the main AI agent.
8. Retry transient errors with bounded backoff.
9. Avoid sending identical state updates excessively.
10. Ensure that a failed LED request does not prevent BUDDY from speaking.
11. Provide a test command that changes the LED state without running the full AI agent.

If the PC uses Python and HTTP, use an existing HTTP client if one is already installed. Otherwise, choose a lightweight dependency and document its installation.

Do not add a heavy framework for this feature.

## 9. CONNECT THE STATES TO THE EXISTING AI LIFECYCLE

Inspect the current conversation flow and connect state changes at the correct points.

Use the following logical integration:

* Before microphone capture starts: LISTENING.
* When user input is finalized and processing begins: THINKING.
* While the model generates its answer: THINKING.
* While TTS audio is being generated: THINKING.
* Immediately before actual audio playback begins: SPEAKING.
* While audio is playing: SPEAKING.
* When playback completes successfully: return to IDLE.
* When playback is cancelled by user interruption: INTERRUPTED, then LISTENING if a new listening session begins.
* When a recoverable operation fails: ERROR or IDLE according to the application's existing error-handling conventions.

Do not let a slow HTTP request delay speech playback.

Use asynchronous calls or a background worker as appropriate.

Make state transitions explicit and avoid race conditions between TTS generation, playback completion, cancellation, and new user requests.

If the agent already has event hooks or lifecycle callbacks, use them instead of adding a parallel state-management system.

## 10. OPTIONAL AUDIO-REACTIVE EFFECT

If practical and if it does not compromise reliability, add an optional enhancement that varies LED brightness according to the amplitude of the audio currently being played.

Only implement this if the PC application has access to the actual outgoing playback audio samples.

Requirements:

* Do not capture or analyze unrelated microphone audio.
* Do not transmit raw speech audio to the ESP32 just to animate the LED.
* Send only a small normalized amplitude value or intensity indicator.
* Rate-limit updates to a reasonable frequency, such as 10–20 updates per second.
* Smooth the amplitude values on the ESP32 to avoid jitter.
* Keep the basic SPEAKING animation functional if audio-amplitude information is unavailable.
* Make the feature optional and configurable.

The basic implementation must not depend on this enhancement.

## 11. SECURITY AND RELIABILITY

This is a local prototype for a college reception robot.

Implement reasonable protections:

1. Bind the server to the local network as needed, not to an internet-accessible public endpoint.
2. Validate all incoming data.
3. Limit request sizes.
4. Reject unsupported state values.
5. Never expose Wi-Fi credentials in logs.
6. Avoid unnecessary open ports.
7. Document the PC and ESP32 network requirements.
8. Include a simple shared token option if the local network may contain untrusted devices.
9. Do not expose the ESP32 server to the public internet.
10. Ensure the AI application remains usable if the LED controller is offline.

Do not add complex authentication infrastructure for a single local LED controller.

## 12. TESTING REQUIREMENTS

Provide tests for the following.

### Firmware

* Device boots.
* Wi-Fi connects.
* Server starts.
* `/health` responds.
* `/api/status` responds.
* Each supported state is accepted.
* Unknown states are rejected.
* LED animations run without blocking networking.
* A new state interrupts the previous animation promptly.
* Wi-Fi reconnection works.
* A disconnected PC does not cause endless rebooting.

### PC integration

* The controller sends valid HTTP requests.
* Invalid states are rejected locally.
* A missing ESP32 does not crash the agent.
* Timeouts do not block speech.
* State changes are sent at the correct lifecycle events.
* SPEAKING starts at actual audio playback start.
* SPEAKING ends at actual audio playback completion.
* Interruptions stop or update the speaking state correctly.

### End-to-end

1. Start the ESP32 firmware.
2. Verify its IP address.
3. Start the PC controller.
4. Manually request LISTENING.
5. Confirm the LED changes to blue.
6. Request THINKING.
7. Confirm the LED changes to amber.
8. Request SPEAKING.
9. Confirm the purple animation starts.
10. Request IDLE.
11. Confirm the LED returns to its idle animation.
12. Run a real BUDDY conversation.
13. Confirm the LED automatically follows the actual audio playback lifecycle.

If hardware is unavailable during automated testing, clearly distinguish simulated tests from real hardware tests. Never claim that physical LED behavior has been verified if it has not been tested on the actual device.

## 13. DOCUMENTATION

Create a README for the integration containing:

* Architecture overview.
* Required hardware.
* Required Arduino libraries or ESP32 core version.
* Firmware upload instructions.
* Board configuration.
* Wi-Fi setup instructions.
* How to discover the ESP32 IP address.
* How to configure the PC controller URL.
* How to run the PC application.
* How to test individual LED states.
* How to connect the LED controller to the TTS playback lifecycle.
* Troubleshooting steps.
* Common connection errors.
* Security notes.

Include example commands appropriate to Windows PowerShell.

Do not assume the ESP32 IP address or Wi-Fi credentials.

## 14. DELIVERABLES

Implement the feature in my existing repository.

Provide:

1. Complete ESP32 firmware.
2. PC-side RGB controller module.
3. Integration with the actual AI speech playback lifecycle.
4. Configuration instructions.
5. Tests for the PC-side logic and API behavior.
6. A README with setup and troubleshooting steps.
7. A list of files created or modified.
8. A concise report of what was tested and what still requires physical hardware verification.

Do not merely output code snippets in chat. Make the changes in the actual workspace if access is available.

Before finishing, review the implementation for incorrect GPIO assumptions, blocking animations, Wi-Fi failure handling, incorrect speech lifecycle transitions, and incompatible dependencies.

## 15. IMPLEMENTATION PRIORITIES

Work in this order:

Priority 1:
Make a reliable ESP32 firmware that accepts a state over local Wi-Fi and animates the onboard RGB LED.

Priority 2:
Create and test the PC controller module.

Priority 3:
Integrate state transitions with the actual TTS playback start and completion.

Priority 4:
Add optional audio-amplitude-reactive animation if practical.

Priority 5:
Document the complete setup.

Start by inspecting the existing project and reporting its current architecture. Then implement the feature with minimal disruption to existing functionality.
