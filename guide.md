# 📖 BUDDY — Complete User & Administrator Guide

Welcome to the comprehensive operational manual for **BUDDY**, your Smart College Reception AI Robot! This guide covers everything from running the application to tuning the AI models and customizing system settings.

---

## 📑 Table of Contents
1. [Quick Start — How to Run BUDDY](#1-quick-start--how-to-run-buddy)
2. [Component Architecture & Ports](#2-component-architecture--ports)
3. [Tuning the AI Models](#3-tuning-the-ai-models)
   - [A. LLM Reasoning Model (Ollama)](#a-llm-reasoning-model-ollama)
   - [B. Speech Recognition / STT (faster-whisper)](#b-speech-recognition--stt-faster-whisper)
   - [C. Text-to-Speech / TTS (Fish Audio S2 Pro)](#c-text-to-speech--tts-fish-audio-s2-pro)
4. [Customizing System Settings](#4-customizing-system-settings)
   - [Environment Configuration (.env)](#environment-configuration-env)
   - [Kiosk UI Settings Panel](#kiosk-ui-settings-panel)
   - [Admin Management Console](#admin-management-console)
5. [Hardware & GPU Optimization (NVIDIA RTX vs. AMD)](#5-hardware--gpu-optimization-nvidia-rtx-vs-amd)
6. [Troubleshooting & FAQs](#6-troubleshooting--faqs)

---

## 1. Quick Start — How to Run BUDDY

### Method A: One-Command Development Launcher (Recommended)
You can launch both the backend API and frontend kiosk concurrently with a single script:

```powershell
# Open terminal in project root
.\.venv\Scripts\python.exe scripts\start_dev.py
```

- **Frontend Kiosk URL**: [http://localhost:5173](http://localhost:5173)
- **Backend API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

### Method B: Manual Step-by-Step Launch (Multi-Terminal)

If you prefer starting each service individually in separate terminal windows:

#### Terminal 1 — Fish Audio S2 Pro Server (Voice Engine on NVIDIA RTX 4060 GPU)
```powershell
cd "e:\Drive D Clone\Made_By_Me\Robots\Buddy"
.\BUDDY-Fish-TTS\s2.cpp\build\Release\s2.exe -m BUDDY-Fish-TTS\models\s2-pro-q5_k_m.gguf -t BUDDY-Fish-TTS\models\tokenizer.json --server -H 127.0.0.1 -P 3030 -v 1 -ngl 36
```
> **GPU Acceleration**: `-v 1` targets the **NVIDIA GeForce RTX 4060 Laptop GPU** via Vulkan 1.4 compute, and `-ngl 36` offloads all 36 transformer layers into VRAM (~3.1 GB). If launched automatically by the backend, it also automatically uses these GPU flags.

#### Terminal 2 — FastAPI Backend
```powershell
cd "e:\Drive D Clone\Made_By_Me\Robots\Buddy\backend"
..\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Terminal 3 — React Frontend Kiosk
```powershell
cd "e:\Drive D Clone\Made_By_Me\Robots\Buddy\frontend"
npm run dev
```

Then open your browser to **`http://localhost:5173`**.

---

## 2. Component Architecture & Ports

| Service | Address | Technology | Purpose |
| :--- | :--- | :--- | :--- |
| **Kiosk UI** | `http://localhost:5173` | React, TypeScript, TailwindCSS/Vanilla CSS | Interactive visitor interface with animated robot avatar |
| **Backend API** | `http://127.0.0.1:8000` | FastAPI, Python 3.13 | Orchestration, RAG database search, tool execution |
| **Voice Server** | `http://127.0.0.1:3030` | `s2.cpp`, GGUF | Neural TTS using Fish Audio S2 Pro |
| **Ollama LLM** *(Optional)* | `http://localhost:11434` | Ollama | Local multi-turn conversational reasoning |

---

## 3. Tuning the AI Models

BUDDY employs a three-tier AI pipeline: **Reasoning (LLM)**, **Hearing (STT)**, and **Speaking (TTS)**. All three can be customized.

### A. LLM Reasoning Model (Ollama)

Configuration file: `backend/app/config.py` or `.env`

```ini
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:8b
OLLAMA_TIMEOUT_SECONDS=60.0
MOCK_AI_FALLBACK=true
```

#### How to Switch Models:
1. Install your preferred model via Ollama:
   ```powershell
   ollama pull qwen3:8b
   # or
   ollama pull llama3.1:8b
   # or
   ollama pull mistral:7b
   ```
2. Update `OLLAMA_MODEL` in your `.env` file:
   ```ini
   OLLAMA_MODEL=llama3.1:8b
   ```
3. Restart the backend.

#### Tuning Model Creativity & System Prompts:
- **System Prompt**: Edit [`backend/app/services/ollama_service.py`](file:///e:/Drive%20D%20Clone/Made_By_Me/Robots/Buddy/backend/app/services/ollama_service.py) in `build_system_prompt()`. You can adjust Buddy's tone (e.g., more humorous, strictly formal, or concise).
- **Temperature**: In `call_ollama_chat()`, change `"options": {"temperature": 0.2}`. Lower values (`0.1 - 0.3`) yield factual, grounded reception answers. Higher values (`0.6 - 0.8`) yield creative, conversational phrasing.

---

### B. Speech Recognition / STT (faster-whisper)

Configuration file: `backend/app/config.py` or `.env`

```ini
STT_MODEL=base
STT_DEVICE=cuda
STT_LANGUAGE=en
```

#### Tuning Options:
- **`STT_DEVICE`**:
  - `cuda`: Offloads Whisper transcription to your **NVIDIA GeForce RTX 4060** using `float16`. Yields instant transcription (< 300ms).
  - `cpu`: Runs on CPU with `int8` quantization if no discrete GPU is available.
- **`STT_MODEL`**:
  - `tiny`: Ultra-fast (~75 MB RAM), best for low-spec devices.
  - `base` *(Default)*: Excellent balance between speed and English word accuracy (~145 MB).
  - `small`: Higher accuracy for noisy environments (~460 MB).
- **`STT_LANGUAGE`**:
  - `en` for English only.
  - Set to `auto` to automatically transcribe multilingual speech.

---

### C. Text-to-Speech / TTS (Fish Audio S2 Pro)

Implementation file: [`backend/app/voice/synthesis.py`](file:///e:/Drive%20D%20Clone/Made_By_Me/Robots/Buddy/backend/app/voice/synthesis.py)

#### Tuning Synthesis Parameters:
In `synthesize_speech()`:
- **Temperature (`temperature: 0.7`)**:
  - `0.5`: Steady, clear, and uniform tone.
  - `0.7` *(Default)*: Natural expressive human intonation.
  - `0.85`: Highly dynamic and cheerful inflection.
- **Token Budget (`max_new_tokens`)**:
  - Dynamically scaled based on word count: `min(max(word_count * 12 + 80, 180), 700)`.
  - Ensures the full sentence is read without cutting off mid-sentence.
- **PCM16 Audio Conversion**:
  - Fish Audio produces 32-bit float audio natively. BUDDY automatically converts output to **16-bit PCM WAV (44.1 kHz)** to ensure all browsers play it natively without falling back to robotic voices.

#### Custom Voice Cloning:
You can synthesize speech using a custom cloned voice sample:
```powershell
.\BUDDY-Fish-TTS\s2.cpp\build\Release\s2.exe `
  -m BUDDY-Fish-TTS\models\s2-pro-q5_k_m.gguf `
  -t BUDDY-Fish-TTS\models\tokenizer.json `
  -pa "path\to\reference_sample.wav" `
  -pt "Exact transcript of reference sample" `
  -text "Hello, welcome to our campus!" `
  -o "output.wav"
```

---

## 4. Customizing System Settings

### Environment Configuration (.env)

Create a `.env` file in the project root to override any default settings:

```ini
# --- LLM Settings ---
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:8b
MOCK_AI_FALLBACK=true

# --- Database ---
DATABASE_PATH=./data/buddy.db

# --- Speech Recognition ---
STT_MODEL=base
STT_DEVICE=cuda
STT_LANGUAGE=en

# --- Text To Speech ---
TTS_ENABLED=true
FISH_TTS_SERVER_URL=http://127.0.0.1:3030

# --- Administrator Console ---
ADMIN_USERNAME=admin
ADMIN_PASSWORD=buddyadmin2026
ADMIN_TOKEN_SECRET=buddy-secret-token-key-2026

# --- Web & Networking ---
FRONTEND_ORIGIN=http://localhost:5173
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
```

---

### Kiosk UI Settings Panel

Visitors or kiosk operators can customize the UI in real time:
1. Click the **Gear (⚙️) icon** in the top-right header of the kiosk.
2. In the **Settings Modal**, you can:
   - **Switch Themes**:
     - *Futuristic Blue* (Default)
     - *Neon Emerald*
     - *Cosmic Purple*
     - *Sleek Dark Mode*
   - **Adjust Speech Volume**: Slider from 0% to 100%.
   - **Mute / Unmute Audio**: Toggle voice output on/off.
   - **Inspect Voice Status**: Check whether Fish Audio S2 Pro is active.

---

### Admin Management Console

Campus administrators can manage the knowledge base without touching any code:

1. Click the **Admin** button in the top-right corner.
2. Enter the administrator credentials:
   - **Username**: `admin` *(or value in `.env`)*
   - **Password**: `buddyadmin2026` *(or value in `.env`)*
3. Use the tabs in the Admin Modal:
   - **Add Department**: Name, code (e.g. `CSE`), building name, floor, wing, and Head of Department (HOD) details.
   - **Add FAQ**: Question, answer, and category tag.
   - **Add College Event**: Title, date, venue, and description.
   - **Upload Prospectus Documents**: Upload `.txt` or `.pdf` files. BUDDY will index them and cite them when answering queries!

---

## 5. Hardware & GPU Optimization (NVIDIA RTX 4060 + AMD)

BUDDY is fully optimized to harness your **NVIDIA GeForce RTX 4060 Laptop GPU (8 GB VRAM)**:

### 1. Speech Recognition (Whisper STT on CUDA):
- **Backend**: Native CUDA with `float16` precision (`faster-whisper`).
- **Device**: NVIDIA GeForce RTX 4060.
- **Latency**: Sub-second transcription without touching CPU threads.

### 2. Speech Synthesis (Fish Audio S2 Pro TTS on Vulkan):
- **Backend**: Hardware-accelerated Vulkan 1.4 compute backend (`ggml-vulkan.dll`).
- **Device**: `-v 1` (NVIDIA GeForce RTX 4060 Laptop GPU).
- **Layers**: `-ngl 36` (All 36 transformer layers offloaded directly into 3.1 GB of VRAM).
- **Latency**: Rapid GPU generation without pinning 100% of CPU cores.

### 3. LLM Reasoning (Ollama):
- Once Ollama is installed, it automatically detects the NVIDIA GPU and runs models (such as `qwen3:8b`) with full CUDA acceleration.

### 4. Browser GPU Allocation:
- By default, Windows routes web browsers to the integrated AMD Radeon GPU for power efficiency.
- If you want the kiosk UI animations to render on the RTX 4060:
  1. Open Windows **Settings** > **Display** > **Graphics**.
  2. Select your browser (Chrome or Edge) > Click **Options**.
  3. Select **High performance (NVIDIA GeForce RTX 4060)** > Click **Save**.

---

## 6. Troubleshooting & FAQs

### Q: Why is Buddy speaking with a robotic voice instead of Fish Audio?
1. Check that the Fish Audio server is running on `http://127.0.0.1:3030`.
2. Check that the speaker is not muted in the kiosk header.
3. If an audio generation error occurs, the browser gracefully falls back to the browser's speech synthesizer to prevent silent failures. Verify that `data/audio_temp` is writable.

### Q: Why does Ollama show "Offline" in the top header?
- If Ollama is not running on your machine, BUDDY automatically falls back to the **Simulated Reception AI**.
- The simulated AI is fully functional and searches all official database records, departments, and prospectus documents.
- To enable the neural LLM, start Ollama: `ollama run qwen3:8b`.

### Q: How do I reset the college database?
- The database is stored at `data/buddy.db`.
- To reset to initial demo data, delete `data/buddy.db` and restart the backend. The backend will automatically re-create the database with all default departments, faculty, and prospectus documents.
