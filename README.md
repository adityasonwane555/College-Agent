# 🤖 BUDDY — Smart AI College Reception Robot

BUDDY is a complete, locally hosted AI desktop assistant prototype for a future **Smart AI College Reception Robot**. It features an adorable, expressive animated face, speech-to-text, local LLM agent tool-calling, verified college document retrieval with source citations, structured database records (departments, faculty, rooms, events, FAQs), voice synthesis, and a protected administrative console.

---

## 🌟 Key Features

1. **Expressive Animated Robot Face (BUDDY)**:
   - Modern kiosk aesthetic with dark navy/charcoal styling and cyber-cyan/violet glow.
   - Distinct reactive animation states:
     - **IDLE**: Natural periodic blinking, eye saccades, breathing float motion.
     - **LISTENING**: Attentive wide eyes, dynamic dancing audio waveform, recording indicator.
     - **THINKING**: Celestial spinning halo ring, upward contemplative eye glance.
     - **SPEAKING**: Rhythmic mouth oscillation synced with voice synthesis.
     - **HAPPY**: Arched crescent smiling eyes, glowing blush LEDs after successful answers.
     - **ERROR**: Sympathetic expression with informative error display.

2. **Official College Information Tools (SQLite)**:
   - `search_faq(query)`
   - `get_department(name)`
   - `get_room(room_name)`
   - `get_faculty(name)`
   - `get_college_hours()`
   - `get_upcoming_events()`
   - `get_announcements()`
   - `search_college_documents(query)`

3. **BUDDY 2.0 Universal Ingestion & Hybrid RAG**:
   - Ingests all major document types: PDF, DOCX, XLSX, CSV, PPTX, TXT, Markdown, JSON, YAML, HTML, Source Code, ZIP Archives, Images, Audio.
   - Extracts structured facts (events, schedules, activities, speakers) with cryptographic duplicate detection and versioning.
   - Persistent Hybrid Retrieval: Combines SQLite structured tables, SQLite FTS5 Full-Text search, and local multilingual vector memory.
   - 100% capable offline operation using local Ollama (`qwen2.5:3b`) with factual grounding and circuit breakers.
   - Detailed Guide: [BUDDY 2.0 Architecture & Knowledge Guide](docs/BUDDY_2.0_ARCHITECTURE_AND_KNOWLEDGE_GUIDE.md).

4. **Speech Recognition & Text-To-Speech**:
   - Push-to-talk microphone workflow with browser audio capture.
   - Local offline speech-to-text with `faster-whisper` (CPU/GPU acceleration configurable).
   - High-fidelity offline speech synthesis via **Fish Audio S2 Pro (Q5_K_M GGUF)** powered by native `s2.cpp` with persistent server acceleration.

5. **Multi-turn Context & Session Isolation**:
   - Maintains conversation history within an isolated session ID (handles follow-up questions such as *"Which floor is it on?"*).
   - Prevents one user's conversation from leaking into another.

6. **Optional Web Search with SSRF Hardening**:
   - SearXNG integration (disabled by default via `WEB_SEARCH_ENABLED=false`).
   - Strict IP validation blocking loopback, RFC 1918 private subnets, and cloud metadata endpoints (`169.254.169.254`).

7. **Protected Administrator Console**:
   - Password-authenticated admin interface.
   - Add/edit FAQs, Departments, Events, and upload new college documents.

8. **Future ESP32 IoT Readiness**:
   - Decoupled REST & WebSocket API architecture (`/ws/status`) ready to stream robot states and concise responses to an ESP32 hardware robot.

---

## 🏗️ Architecture & Project Structure

```
Buddy/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, lifespan, CORS, WebSockets
│   │   ├── config.py                # Pydantic environment configuration
│   │   ├── api/
│   │   │   └── routes.py            # REST endpoints (chat, voice, college, admin)
│   │   ├── agent/
│   │   │   ├── orchestrator.py      # Multi-turn tool calling loop & sessions
│   │   │   ├── prompts.py           # Buddy's reception system prompt
│   │   │   └── tool_registry.py     # Tool schemas & function dispatcher
│   │   ├── tools/
│   │   │   ├── college_tools.py     # SQLite & document search tools
│   │   │   └── web_tools.py         # SearXNG web search tool
│   │   ├── database/
│   │   │   ├── models.py            # Pydantic & database schemas
│   │   │   ├── repository.py        # SQLite database repository
│   │   │   └── seed.py              # Sample DEMO DATA seeder
│   │   ├── documents/
│   │   │   ├── ingestion.py         # PDF & TXT parser with page tracking
│   │   │   └── retrieval.py         # Term scoring & citation generator
│   │   ├── voice/
│   │   │   ├── transcription.py     # faster-whisper local STT
│   │   │   ├── synthesis.py         # Piper & browser speech fallback
│   │   │   └── audio_utils.py       # WAV file handlers
│   │   ├── security/
│   │   │   ├── authentication.py    # Admin tokens & credentials
│   │   │   └── url_validation.py    # SSRF protection
│   │   ├── services/
│   │   │   └── ollama_service.py    # Ollama client with fallback AI
│   │   └── tests/                   # 16 unit & integration tests
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx                  # Main Kiosk interface
│   │   ├── components/
│   │   │   ├── RobotFace.tsx        # Robot head & visor assembly
│   │   │   ├── RobotEyes.tsx        # Reactive blinking & pupil gaze
│   │   │   ├── RobotMouth.tsx       # Speaking oscillation & expressions
│   │   │   ├── ListeningWaveform.tsx# Dancing frequency bars
│   │   │   ├── StatusIndicator.tsx  # Dynamic status pill
│   │   │   ├── ConversationPanel.tsx# Transcript & citation cards
│   │   │   ├── VoiceControls.tsx    # Push-to-talk mic & volume toggles
│   │   │   ├── SettingsPanel.tsx    # Diagnostic & config modal
│   │   │   └── AdminPanel.tsx       # Auth-protected college record editor
│   │   ├── hooks/
│   │   │   └── useVoice.ts          # MediaRecorder & audio playback
│   │   ├── services/
│   │   │   └── api.ts               # Backend API client
│   │   └── styles/
│   │       ├── global.css           # Glassmorphism cyber-kiosk theme
│   │       └── robot.css            # Expressive animations
│   └── package.json
│
├── data/
│   ├── sample_documents/            # College Prospectus & Campus Guide
│   └── buddy.db                     # SQLite database (auto-generated)
│
├── scripts/
│   ├── setup_check.py               # Diagnostic verification utility
│   └── start_dev.py                 # Concurrently starts backend & frontend
├── .env.example
├── pytest.ini
└── README.md
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python**: 3.10 or newer (tested on Python 3.13)
- **Node.js**: v18+ and `npm`
- **Ollama** *(Optional for local LLM)*: [https://ollama.com](https://ollama.com)

### 1. Verify Environment & Setup
Run the diagnostic utility to verify prerequisites:
```powershell
.venv\Scripts\python.exe scripts\setup_check.py
```

### 2. Start Both Servers (One Command)
Run the launcher script to start both the FastAPI backend and Vite frontend concurrently:
```powershell
.venv\Scripts\python.exe scripts\start_dev.py
```

Alternatively, start them in two separate terminal tabs:

**Tab 1 (FastAPI Backend):**
```powershell
cd backend
..\.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Tab 2 (Vite Frontend):**
```powershell
cd frontend
npm run dev
```

Open your browser to: **[http://localhost:5173](http://localhost:5173)**
Interactive API documentation is at: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

---

## 🧠 Local AI Model Setup (Ollama & Qwen3)

BUDDY connects to Ollama running locally at `http://localhost:11434`.

1. Download and install Ollama from [https://ollama.com](https://ollama.com).
2. Download your preferred model (e.g. Qwen 2.5 / 3):
   ```bash
   ollama run qwen3:8b
   ```
   *Or for lower memory / CPU systems:*
   ```bash
   ollama run qwen2.5:3b
   ```
3. Update `.env` if using an alternative model name:
   ```ini
   OLLAMA_MODEL=qwen2.5:3b
   ```

> **Note on Fallback AI**: If Ollama is not running or the model is still downloading, BUDDY's **Simulated Reception AI** automatically activates. It executes the exact same tools and grounded database lookups so you can test the kiosk interface immediately!

---

## 🎙️ Speech Recognition & Voice Setup

- **STT (Speech-to-Text)**: Powered by `faster-whisper`.
  - Configured for **NVIDIA CUDA** acceleration on your **GeForce RTX 4060** (`STT_DEVICE=cuda`, `compute_type=float16`).
  - Automatic fallback to CPU if CUDA is temporarily unavailable.
- **TTS (Text-to-Speech)**: Powered by **Fish Audio S2 Pro** (`s2-pro-q5_k_m.gguf`).
  - Served via persistent low-latency `s2.cpp` server on `http://127.0.0.1:3030`.
  - Automatically converted to standard 16-bit PCM WAV (44.1 kHz) for universal browser playback.
  - Full sentence articulation without word truncation.

---

## 🔒 Administrator Console

Access the Admin Console by clicking the **Admin** button in the top-right corner.
- **Default Username**: `admin`
- **Default Password**: `buddyadmin2026`
*(Change in `.env` before deploying)*

Admins can:
- Add & edit college FAQs
- Register new academic departments & contact details
- Schedule campus events & symposiums
- Upload & index new college PDF / text brochures

---

## 🧪 Running Unit & Integration Tests

The test suite covers database initialization, tool execution, session isolation, SSRF prevention, citation metadata, and endpoint protection.

Run all tests:
```powershell
.venv\Scripts\pytest.exe backend/app/tests -v
```

All 16 tests pass:
```
backend/app/tests/test_agent_tools.py::test_tool_execution_registered PASSED
backend/app/tests/test_agent_tools.py::test_missing_college_information_handling PASSED
backend/app/tests/test_agent_tools.py::test_document_search_citations PASSED
backend/app/tests/test_agent_tools.py::test_session_isolation PASSED
backend/app/tests/test_agent_tools.py::test_orchestrator_run_with_tools PASSED
backend/app/tests/test_api_endpoints.py::test_health_endpoint PASSED
backend/app/tests/test_api_endpoints.py::test_config_endpoint PASSED
backend/app/tests/test_api_endpoints.py::test_chat_endpoint_valid_and_invalid_input PASSED
backend/app/tests/test_api_endpoints.py::test_college_info_endpoints PASSED
backend/app/tests/test_api_endpoints.py::test_admin_endpoint_protection PASSED
backend/app/tests/test_database.py::test_database_initialization PASSED
backend/app/tests/test_database.py::test_faq_retrieval PASSED
backend/app/tests/test_database.py::test_department_lookup_and_missing_info PASSED
backend/app/tests/test_security_and_web.py::test_disabled_web_search PASSED
backend/app/tests/test_security_and_web.py::test_ssrf_url_validation PASSED
backend/app/tests/test_security_and_web.py::test_admin_authentication PASSED
```

---

## 📡 Future ESP32 Robot Integration

The backend is engineered for direct compatibility with an ESP32 robot chassis:
- **WebSocket Endpoint** (`/ws/status`): Broadcasts state transitions (`idle`, `listening`, `thinking`, `speaking`, `happy`, `error`).
- **Concise TTS responses**: Generates clean, short text payloads suitable for low-bandwidth microcontrollers.
- **Hardware Trigger**: ESP32 physical push-button or capacitive touch sensors can trigger recording via simple HTTP POST or WebSocket messages.
