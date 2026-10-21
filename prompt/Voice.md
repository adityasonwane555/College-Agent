PROJECT: Install and Run Fish Audio S2 Pro Locally for BUDDY AI Robot

ROLE
You are a senior machine learning engineer and Windows GPU deployment specialist.
Work directly in my project workspace using the terminal and available tools.
Install, configure, test, and document a local text-to-speech system using
Fish Audio S2 Pro.

Do not merely explain the steps. Inspect my computer, execute the steps you
can safely perform, troubleshoot errors, and verify the result.

==================================================
1. MY COMPUTER
==================================================

Operating system: Windows
GPU: NVIDIA GeForce RTX 4060
Dedicated GPU memory: 8188 MiB (8 GB)
System RAM: 15,599 MB (approximately 16 GB)
NVIDIA driver: 592.82
Driver-reported CUDA version: 13.1

This is a relatively memory-constrained GPU for the full Fish Audio S2 Pro
model. Do not assume that the full model fits in VRAM.

==================================================
2. PRIMARY OBJECTIVE
==================================================

Get Fish Audio S2 Pro generating natural speech locally on my computer.

The system should:
- Accept a text string.
- Generate speech.
- Save the generated speech as a WAV file, or another documented audio
  format if WAV is not natively supported.
- Play the generated speech for testing.
- Prefer local inference over paid cloud APIs.
- Use my NVIDIA GPU where supported.
- Report generation time, audio duration, GPU memory usage, and errors.
- Provide a reusable Python interface for future integration with BUDDY.

Do not begin by developing the entire robot application.
First make the TTS engine work independently.

==================================================
3. VERIFY THE MODEL AND IMPLEMENTATION FIRST
==================================================

Investigate the current official Fish Audio S2 Pro documentation and
the community quantized implementations.

Official documentation:
https://speech.fish.audio/
https://speech.fish.audio/install/
https://fish.audio/s2/

Potential community repository:
https://huggingface.co/rodrigomt/s2-pro-gguf

Potential inference repository:
https://github.com/rodrigomatta/s2.cpp

IMPORTANT:
These community repositories are candidates to investigate, not guaranteed
working dependencies.

Before installing:
1. Verify that the repositories exist and are accessible.
2. Inspect their README files and latest instructions.
3. Confirm whether the implementation supports Windows.
4. Confirm whether the quantized model format is genuinely supported.
5. Check whether inference supports NVIDIA CUDA and GPU offloading.
6. Check the current model license and usage restrictions.
7. Determine whether the implementation is compatible with an RTX 4060
   with 8 GB VRAM and 16 GB system RAM.
8. Determine the required model files, tokenizer, configuration files,
   and any other required assets.
9. Verify that the model architecture is actually supported by the runtime.

Do not download arbitrary executables or run untrusted installation scripts.

Do not assume that a GGUF file is usable simply because it exists.
Verify that the inference engine supports the specific architecture and
quantization format.

If a candidate repository is unavailable, unsupported, or incompatible,
find the best documented alternative and explain why you selected it.

==================================================
4. INSPECT MY ENVIRONMENT
==================================================

Start by checking:

- Windows version
- Python availability and version
- Git availability
- CMake availability
- NVIDIA GPU and driver
- Available GPU memory
- Available disk space
- Existing CUDA toolkit, if installed
- Visual Studio C++ build tools, if required

Useful commands include:

nvidia-smi
python --version
py --version
git --version
cmake --version
where python
where git

Use commands appropriate for Windows PowerShell or Command Prompt.

Do not assume the CUDA toolkit is installed just because nvidia-smi
reports a CUDA version.

Do not unnecessarily reinstall NVIDIA drivers.

If a dependency is missing, explain what is missing and install it only
when the installation method is reliable and appropriate.

==================================================
5. CHOOSE A MODEL CONFIGURATION
==================================================

Investigate quantized S2 Pro configurations suitable for my hardware.

Potential candidates:
- Q6_K
- Q5_K_M
- Q4_K_M
- Other officially documented or technically compatible quantizations

Do not choose solely by the model file's download size.

Estimate the total runtime memory requirements, including:
- Model weights
- Runtime allocations
- Audio-generation caches
- GPU buffers
- Context or sequence buffers
- Any additional model components

Start with the highest-quality configuration that is realistically
compatible with the hardware.

If Q6_K is too demanding, test a smaller compatible configuration.

Avoid exhausting VRAM or system RAM.

Monitor GPU memory usage during inference.

Do not claim that quantization preserves the full model's quality.
Explain any known quality trade-offs.

If no verified compatible local implementation can run on my hardware,
stop before performing a large download and present the available options.

==================================================
6. INSTALLATION REQUIREMENTS
==================================================

Use an isolated Python virtual environment if Python is required.

Keep all project files in a clearly named workspace folder such as:

BUDDY-Fish-TTS/

Use a structure similar to:

BUDDY-Fish-TTS/
    README.md
    requirements.txt
    .gitignore
    .env.example
    scripts/
        check_environment.ps1
        install.ps1
        test_tts.ps1
    app/
        __init__.py
        tts_engine.py
        generate_speech.py
        config.py
    tests/
        test_imports.py
        test_tts_interface.py
    models/
        README.md
    output/
        .gitkeep
    logs/
        .gitkeep

Adapt this structure if the chosen inference engine requires a different
layout.

Do not put multi-gigabyte model weights into Git.

Do not store API keys or secrets in source code.

Do not install packages globally when an isolated environment is practical.

Pin compatible dependency versions where appropriate.

Avoid upgrading packages indiscriminately if doing so could break CUDA,
PyTorch, or other dependencies.

==================================================
7. IMPLEMENT A REUSABLE TTS INTERFACE
==================================================

Create a Python module exposing an interface similar to:

class FishTTSEngine:
    def load(self):
        ...

    def generate(
        self,
        text: str,
        output_path: str
    ):
        ...

    def get_status(self):
        ...

    def unload(self):
        ...

Adapt the actual implementation to the selected runtime's real API.

Do not create fake methods that claim to work without calling the model.

Requirements:
- Validate that text is nonempty.
- Validate the output path.
- Handle missing model files clearly.
- Handle GPU out-of-memory errors.
- Report initialization and inference failures.
- Allow the model to be loaded once and reused when supported.
- Save generated audio in a documented format.
- Return useful metadata, including duration and generation time.
- Support a configurable output directory.
- Do not require internet access for inference after all required files
  have been downloaded, unless the selected implementation genuinely
  requires an online service.

Keep the inference layer separate from the future BUDDY web server.

==================================================
8. CREATE A TEST SCRIPT
==================================================

Create a script that:

1. Checks the installation.
2. Loads the selected model.
3. Generates speech from:

   "Hello! Welcome to Anantrao Pawar College of Engineering and Research.
   I am Buddy, your AI college receptionist. How can I help you today?"

4. Saves the result to:

   output/buddy_test.wav

5. Plays the audio only if playback is available and enabled.
6. Prints:
   - Selected model and quantization
   - Runtime and dependency versions
   - Whether CUDA/GPU acceleration is active
   - Initial and peak GPU memory usage, where measurable
   - Speech generation time
   - Output file path
   - Audio duration
   - Any warnings or errors

If the actual output format is not WAV, use the correct extension and
document the format instead of creating a misleading WAV file.

Do not report a successful test unless actual speech audio has been
generated and the file has been verified.

==================================================
9. VOICE QUALITY AND LANGUAGE TESTS
==================================================

After the first successful English test, create optional test sentences
for:

English:
"Good morning! How can I help you?"

Hindi:
"नमस्ते! मैं आपकी किस प्रकार सहायता कर सकता हूँ?"

Marathi:
"नमस्कार! मी आपली कशी मदत करू शकतो?"

Run each language test only if the selected model and runtime support it.

Do not assume Marathi support from Hindi support.

Report whether each language:
- Is officially supported
- Generates intelligible speech
- Has pronunciation issues
- Requires a different voice or configuration

Do not invent language-support claims.

==================================================
10. PREPARE FOR BUDDY INTEGRATION
==================================================

After the standalone TTS test succeeds, prepare an integration example
that can later be called by a local Python FastAPI server.

Example conceptual endpoint:

POST /tts

Request:
{
  "text": "Welcome to the college."
}

Response:
- Generated audio, or
- A documented JSON response with a URL/path for the audio

Requirements:
- Keep inference local.
- Validate input.
- Set a sensible maximum text length.
- Handle generation failures.
- Avoid loading the model again for every request if possible.
- Do not expose the service to the public internet by default.
- Bind to localhost for the initial test.
- Explain how the ESP32-S3 could retrieve generated audio over the
  local Wi-Fi network in a later development phase.

Do not start implementing ESP32 firmware yet.

The ESP32 will not run the 4-billion-parameter TTS model.
The PC will generate speech, and the robot will play the returned audio.

==================================================
11. SECURITY, LICENSE AND COST
==================================================

Use local inference as the primary target.

Do not silently switch to a paid API.

Do not request or expose API keys unless an API fallback is explicitly
approved by me.

Check and document the model license and inference engine license
separately.

Do not assume an open model is unrestricted for commercial use.

Do not use a voice clone without the voice owner's permission.

Do not download models from unknown mirrors.

Estimate the download size and required disk space before downloading.

==================================================
12. TROUBLESHOOTING
==================================================

Handle common problems, including:
- Python not installed
- Missing Git or CMake
- Missing C++ compiler
- CUDA runtime incompatibility
- PyTorch CUDA unavailable
- Model architecture not supported
- Quantized model incompatibility
- CUDA out-of-memory
- System RAM exhaustion
- Missing tokenizer or configuration
- Unsupported language
- Audio generation failures
- Missing audio playback dependencies

For each failure:
1. Capture the real error.
2. Identify the likely cause.
3. Apply the smallest safe correction.
4. Retry the affected test.
5. Record the resolution in README.md.

Never hide an error and print "success" anyway.

==================================================
13. FINAL ACCEPTANCE CRITERIA
==================================================

The task is complete only when:

[ ] The selected model and inference engine are verified.
[ ] The license and supported hardware are documented.
[ ] Installation instructions are reproducible.
[ ] The environment checks are implemented.
[ ] The model loads successfully, or a verified blocker is documented.
[ ] The test script generates real speech when compatible hardware
    and dependencies permit.
[ ] The output audio file exists and is valid.
[ ] Performance and GPU memory use are measured where possible.
[ ] The reusable Python TTS interface is implemented.
[ ] The README explains how to run everything.
[ ] The next steps for FastAPI and ESP32 integration are documented.

==================================================
14. WORKING STYLE
==================================================

Work in small, verifiable stages.

First inspect the machine and verify the repositories.

Then propose the model configuration and approximate download size.

Before downloading multiple gigabytes, report:
- Which model variant you selected
- Why it is compatible with the runtime
- Expected memory requirements
- Any licensing restrictions
- Any uncertainty about Windows support

Proceed with safe installations that do not require major destructive
changes. Ask me before installing large optional dependencies, changing
system-wide configuration, or downloading unexpectedly large files.

Do not stop after writing a plan if the tools allow you to execute it.

If a step cannot be completed, tell me exactly what failed and give me
the next concrete command or action.

Start by inspecting the environment and verifying the repositories.