# 🐟 BUDDY-Fish-TTS — Fish Audio S2 Pro Local Deployment

This project provides an offline, local text-to-speech (TTS) engine using **Fish Audio S2 Pro** quantized with **GGUF** and powered by the native C++ **`s2.cpp`** inference engine.

It is designed for the **BUDDY Smart AI College Reception Robot**, providing rich, human-like voice synthesis without relying on paid cloud APIs.

---

## 💻 Hardware Verification & Specifications

| Hardware Component | Detected System Spec | S2 Pro Compatibility |
| :--- | :--- | :--- |
| **Operating System** | Windows 11 (AMD64) | Full MSVC / Win32 Support |
| **GPU** | NVIDIA GeForce RTX 4060 Laptop | 8188 MiB (8 GB) Dedicated VRAM |
| **Driver & CUDA** | Driver 592.82 (CUDA 13.1 Capable) | High-speed OpenMP & CUDA capable |
| **System RAM** | 16 GB (15,599 MB) | Sufficient for GGUF runtime buffers |
| **C++ Build Tools** | Visual Studio 2022 Build Tools (MSVC 19.44) | Native compilation verified |
| **CMake** | CMake 3.31.6 (MSVC) | Native build verified |

---

## 🎯 Model Configuration: `s2-pro-q5_k_m.gguf`

- **Base Architecture**: Fish Audio S2 Pro (~4.56B Dual-AR parameters).
- **Quantization Variant**: `s2-pro-q5_k_m.gguf` (~3.8 GB download).
- **Hugging Face Repository**: [`rodrigomt/s2-pro-gguf`](https://huggingface.co/rodrigomt/s2-pro-gguf)
- **Engine Binary**: [`rodrigomatta/s2.cpp`](https://github.com/rodrigomatta/s2.cpp) (compiled to `s2.cpp/build/Release/s2.exe`).
- **Memory Footprint**:
  - Model weights: ~3.8 GB
  - Codec & KV cache: ~1.5 - 2.0 GB
  - Total runtime allocation: ~5.3 - 5.8 GB (Safely fits inside 8 GB VRAM).
- **License**: **Fish Audio Research License** (free for research & non-commercial use).

---

## 📁 Project Structure

```
BUDDY-Fish-TTS/
├── README.md                      # Comprehensive documentation
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment configuration template
├── .gitignore                     # Ignores model weights and output WAVs
│
├── app/
│   ├── __init__.py                # Module initialization
│   ├── config.py                  # Pydantic configuration settings
│   ├── tts_engine.py              # Reusable FishTTSEngine Python interface
│   ├── generate_speech.py         # CLI synthesis tool
│   └── server.py                  # FastAPI service for Buddy & ESP32
│
├── scripts/
│   ├── check_environment.ps1      # PowerShell hardware diagnostics
│   ├── install.ps1                # Automated CMake build & setup script
│   ├── download_model.py          # Hugging Face downloader
│   └── test_tts.ps1               # Standardized reception benchmark test
│
├── models/
│   ├── README.md                  # Model details and license
│   ├── tokenizer.json             # 13 MB vocabulary tokenizer
│   └── s2-pro-q5_k_m.gguf         # 3.8 GB GGUF model weights
│
├── tests/
│   ├── test_imports.py            # Import sanity tests
│   └── test_tts_interface.py      # Input validation & interface unit tests
│
├── output/                        # Generated output WAV files
└── logs/                          # Runtime logs
```

---

## 🚀 Quick Start Guide

### 1. Run Environment Diagnostics
Verify that your GPU, compiler, and paths are ready:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_environment.ps1
```

### 2. Build the C++ Engine (If not already compiled)
```powershell
powershell -ExecutionPolicy Bypass -File scripts\install.ps1
```

### 3. Download the S2 Pro Quantized Weights
```powershell
python scripts\download_model.py
```
*Or via curl:*
```powershell
curl.exe -L -C - -o models\s2-pro-q5_k_m.gguf "https://huggingface.co/rodrigomt/s2-pro-gguf/resolve/main/s2-pro-q5_k_m.gguf"
```

### 4. Run the Standardized Reception Voice Benchmark
Executes the official test prompt:
> *"Hello! Welcome to Anantrao Pawar College of Engineering and Research. I am Buddy, your AI college receptionist. How can I help you today?"*

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test_tts.ps1
```
Add `-PlayAudio` to immediately play the synthesized audio through your computer's speakers:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\test_tts.ps1 -PlayAudio
```

### 📊 Verified Benchmark Results

| Test Prompt | Language | Output File | Audio Duration | Generation Time | RTF | Sample Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Reception Benchmark**: *"Hello! Welcome to Anantrao Pawar College of Engineering and Research. I am Buddy, your AI college receptionist. How can I help you today?"* | English | `output/buddy_test.wav` | **9.27 s** | 217.81 s | 23.5x | 44,100 Hz |
| **Multilingual Test**: *"नमस्ते! मैं आपकी किस प्रकार सहायता कर सकता हूँ?"* | Hindi | `output/hindi_test.wav` | **4.93 s** | 75.67 s | 15.35x | 44,100 Hz |
| **Multilingual Test**: *"नमस्कार! मी आपली कशी मदत करू शकतो?"* | Marathi | `output/marathi_test.wav` | **5.00 s** | 72.94 s | 14.59x | 44,100 Hz |

All outputs are saved as 44.1 kHz, 32-bit floating point WAV files with clean waveform dynamics.

---

## 🐍 Reusable Python Interface (`FishTTSEngine`)

You can import and use `FishTTSEngine` in any Python script:

```python
from app.tts_engine import FishTTSEngine

# Initialize engine
engine = FishTTSEngine()

# Synthesize speech
result = engine.generate(
    text="Welcome to the Computer Science Department.",
    output_path="output/welcome.wav"
)

print(f"Generated: {result['output_path']}")
print(f"Duration:  {result['duration_seconds']}s")
print(f"Latency:   {result['generation_time_seconds']}s")
print(f"RTF:       {result['real_time_factor']}x")
```

---

## 🌐 FastAPI & Future ESP32 Integration

### Running the Local Speech API Server
```powershell
..\.venv\Scripts\uvicorn.exe app.server:app --host 127.0.0.1 --port 8000 --reload
```

### Endpoints:
- `GET /health`: Health and VRAM diagnostic metrics.
- `POST /tts`: Synthesize speech from JSON payload:
  ```json
  {
    "text": "Hello! Where would you like to go?"
  }
  ```
  Returns:
  ```json
  {
    "success": true,
    "audio_url": "/audio/speech_1729512345.wav",
    "duration_seconds": 3.8,
    "generation_time_seconds": 1.9,
    "real_time_factor": 0.5,
    "file_size_bytes": 335200
  }
  ```

### ESP32-S3 Retrieval Workflow (Future Phase):
1. **User Speaks**: User presses the physical button on the ESP32 reception kiosk.
2. **PC Generates**: The PC runs the LLM tool-calling agent and generates speech using `FishTTSEngine`.
3. **ESP32 Streams**: The ESP32-S3 connects over local Wi-Fi, requests `GET /audio/{filename}`, and streams the PCM/WAV buffer via I2S to an external MAX98357A amplifier and speaker.
4. **No Model on ESP32**: The ESP32 remains lightweight and cost-effective; all 4.56B parameter inference happens locally on the RTX 4060 PC.
