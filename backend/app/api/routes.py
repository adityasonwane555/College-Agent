import shutil
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..config import settings, UPLOAD_DIR
from ..database.repository import repo
from ..database.models import (
    FAQModel, DepartmentModel, RoomModel, FacultyModel,
    EventModel, AnnouncementModel, CitationModel
)
from ..documents.ingestion import ingest_text_file, ingest_pdf_file
from ..services.ollama_service import check_ollama_status
from ..agent.orchestrator import orchestrator
from ..voice.transcription import transcribe_audio_file, is_whisper_installed
from ..voice.synthesis import synthesize_speech, is_fish_tts_server_alive
from ..voice.audio_utils import AUDIO_DIR
from ..security.authentication import authenticate_admin, verify_admin_token
from ..hardware.rgb_controller import rgb_controller
from ..hardware.esp32_client import esp32_client

router = APIRouter(prefix="/api")


# --- Request / Response Models ---
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    citations: List[CitationModel]
    is_simulated: bool
    tts: Optional[Dict[str, Any]] = None


class SpeakRequest(BaseModel):
    text: str


class LedStateRequest(BaseModel):
    state: str
    amplitude: Optional[float] = 0.0
    bass: Optional[float] = None
    mid: Optional[float] = None
    treble: Optional[float] = None


class DisplayMessageRequest(BaseModel):
    title: str
    body: str


class AdminLoginRequest(BaseModel):
    username: str
    password: str


# --- Health & Config Endpoints ---
@router.get("/health")
async def health_check():
    ollama_stat = await check_ollama_status()
    whisper_ready = is_whisper_installed()
    docs = repo.list_documents()
    
    return {
        "status": "online",
        "service": "BUDDY Reception Agent",
        "database": "connected",
        "ollama": ollama_stat,
        "whisper": {
            "installed": whisper_ready,
            "model": settings.STT_MODEL,
            "device": settings.STT_DEVICE
        },
        "tts": {
            "enabled": settings.TTS_ENABLED,
            "engine": "Fish Audio S2 Pro (Q5_K_M GGUF)",
            "server_active": is_fish_tts_server_alive()
        },
        "documents_indexed": len(docs),
        "web_search_enabled": settings.WEB_SEARCH_ENABLED
    }


@router.get("/config")
def get_public_config():
    return {
        "model_name": settings.OLLAMA_MODEL,
        "stt_language": settings.STT_LANGUAGE,
        "stt_model": settings.STT_MODEL,
        "tts_enabled": settings.TTS_ENABLED,
        "web_search_enabled": settings.WEB_SEARCH_ENABLED,
        "mock_fallback_active": settings.MOCK_AI_FALLBACK
    }


def _stream_audio_to_esp32_bg(audio_path_str: str):
    """Decodes and streams TTS audio file to the ESP32 MAX98357A speaker."""
    try:
        p = Path(audio_path_str)
        if p.exists():
            data = p.read_bytes()
            esp32_client.stream_wav_to_speaker(data)
    except Exception as e:
        print(f"[ESP32 Speaker Stream] Error: {e}")


# --- Chat Endpoint ---
@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest, background_tasks: BackgroundTasks):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Notify hardware LED that reasoning/search has started
    rgb_controller.set_state("THINKING")

    result = await orchestrator.run(
        user_message=req.message,
        session_id=req.session_id
    )

    tts_meta: Dict[str, Any] = {
        "enabled": settings.TTS_ENABLED,
        "engine": getattr(settings, "TTS_ENGINE", "edge_tts"),
        "audio_url": None
    }
    if settings.TTS_ENABLED:
        try:
            synth = synthesize_speech(result["response"])
            if synth.get("enabled") and synth.get("audio_url"):
                tts_meta["audio_url"] = synth.get("audio_url")
                if synth.get("file_path"):
                    background_tasks.add_task(_stream_audio_to_esp32_bg, synth["file_path"])
        except Exception as e:
            print(f"[Chat] Pre-synthesis error: {e}")

    return ChatResponse(
        response=result["response"],
        session_id=result["session_id"],
        citations=result["citations"],
        is_simulated=result["is_simulated"],
        tts=tts_meta
    )


# --- Voice Endpoints ---
@router.post("/voice/transcribe")
async def transcribe_voice(audio: UploadFile = File(...)):
    if not audio:
        raise HTTPException(status_code=400, detail="No audio file received.")

    # Notify hardware LED that audio transcription has started
    rgb_controller.set_state("THINKING")

    suffix = Path(audio.filename or "recording.wav").suffix or ".wav"
    temp_path = AUDIO_DIR / f"rec_{uuid.uuid4().hex[:8]}{suffix}"

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)

    try:
        res = transcribe_audio_file(temp_path)
        return res
    finally:
        # Clean up temp upload file
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass


@router.post("/voice/record-esp32")
async def record_esp32_mic(seconds: int = 4):
    """
    Triggers an on-demand audio capture from the ESP32 INMP441 microphone over Wi-Fi,
    persists the 16kHz WAV file, and runs Faster-Whisper GPU speech recognition.
    """
    if seconds < 1:
        seconds = 1
    if seconds > 10:
        seconds = 10

    # Notify hardware LED that listening has started
    rgb_controller.set_state("LISTENING")

    wav_bytes = esp32_client.fetch_mic_recording(seconds=seconds)
    if not wav_bytes or len(wav_bytes) <= 44:
        rgb_controller.set_state("IDLE")
        return {"success": False, "text": "", "error": "No audio received from ESP32 INMP441 microphone. Please ensure the board is online."}

    # Notify hardware LED that reasoning/transcription has started
    rgb_controller.set_state("THINKING")

    temp_path = AUDIO_DIR / f"esp32_mic_{uuid.uuid4().hex[:8]}.wav"
    try:
        temp_path.write_bytes(wav_bytes)
        res = transcribe_audio_file(temp_path)
        return res
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass


@router.post("/voice/speak")
def speak_endpoint(req: SpeakRequest, background_tasks: BackgroundTasks):
    res = synthesize_speech(req.text)
    if res.get("enabled") and res.get("file_path"):
        background_tasks.add_task(_stream_audio_to_esp32_bg, res["file_path"])
    return res


@router.post("/hardware/stream-audio")
def stream_audio_to_speaker(audio_url: str, background_tasks: BackgroundTasks):
    """Streams an existing audio URL file directly to the ESP32 MAX98357A speaker."""
    filename = Path(audio_url).name
    target = AUDIO_DIR / filename
    if not target.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    background_tasks.add_task(_stream_audio_to_esp32_bg, str(target))
    return {"ok": True, "message": f"Streaming {filename} to ESP32 speaker"}


@router.get("/voice/audio/{filename}")
def serve_audio(filename: str):
    file_path = AUDIO_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found.")
    media_type = "audio/mpeg" if file_path.suffix.lower() == ".mp3" else "audio/wav"
    return FileResponse(file_path, media_type=media_type)


# --- College Information Endpoints ---
@router.get("/college/departments")
def get_departments():
    return repo.list_departments()


@router.get("/college/events")
def get_events():
    return repo.get_upcoming_events()


@router.get("/college/announcements")
def get_announcements():
    return repo.get_announcements()


@router.get("/college/hours")
def get_hours():
    return repo.get_college_hours()


@router.get("/college/faqs")
def get_faqs():
    return repo.list_faqs()


# --- Document Upload & Retrieval ---
@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    authenticated: bool = Depends(verify_admin_token)
):
    filename = file.filename or "document.txt"
    dest_path = UPLOAD_DIR / filename
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if filename.lower().endswith(".pdf"):
        meta, chunks = ingest_pdf_file(dest_path)
    else:
        meta, chunks = ingest_text_file(dest_path)

    return {
        "status": "success",
        "metadata": meta,
        "chunk_count": len(chunks)
    }


@router.get("/documents/list")
def list_documents():
    return repo.list_documents()


# --- Admin Authentication & Management ---
@router.post("/admin/login")
def admin_login(req: AdminLoginRequest):
    token = authenticate_admin(req.username, req.password)
    return {"status": "authenticated", "token": token}


@router.post("/admin/faq")
def add_faq(faq: FAQModel, auth: bool = Depends(verify_admin_token)):
    faq_id = repo.add_faq(faq)
    return {"status": "created", "id": faq_id}


@router.post("/admin/department")
def add_department(dept: DepartmentModel, auth: bool = Depends(verify_admin_token)):
    dept_id = repo.add_department(dept)
    return {"status": "saved", "id": dept_id}


@router.post("/admin/room")
def add_room(room: RoomModel, auth: bool = Depends(verify_admin_token)):
    room_id = repo.add_room(room)
    return {"status": "saved", "id": room_id}


@router.post("/admin/faculty")
def add_faculty(fac: FacultyModel, auth: bool = Depends(verify_admin_token)):
    fac_id = repo.add_faculty(fac)
    return {"status": "saved", "id": fac_id}


@router.post("/admin/event")
def add_event(event: EventModel, auth: bool = Depends(verify_admin_token)):
    event_id = repo.add_event(event)
    return {"status": "saved", "id": event_id}


@router.post("/admin/announcement")
def add_announcement(ann: AnnouncementModel, auth: bool = Depends(verify_admin_token)):
    ann_id = repo.add_announcement(ann)
    return {"status": "saved", "id": ann_id}


# --- Hardware RGB LED Endpoints ---
@router.post("/hardware/led-state")
def set_hardware_led(req: LedStateRequest):
    """Updates the ESP32-S3 onboard RGB LED state over local Wi-Fi."""
    success = rgb_controller.set_state(
        req.state,
        req.amplitude or 0.0,
        req.bass,
        req.mid,
        req.treble
    )
    return {"ok": success, "state": req.state}


@router.get("/hardware/led-status")
def get_hardware_led_status():
    """Returns local controller status and Wi-Fi connection health to the ESP32."""
    return rgb_controller.get_status()


@router.post("/hardware/led-ping")
def ping_hardware_led():
    """Actively pings the ESP32-S3 microcontroller to verify network connectivity."""
    return rgb_controller.test_connection()


@router.post("/hardware/display")
def update_hardware_display(req: DisplayMessageRequest):
    """Sends a title and message to the ST7789 TFT display on the ESP32."""
    success = esp32_client.update_display(req.title, req.body)
    return {"ok": success}


@router.post("/hardware/chime")
def trigger_hardware_chime():
    """Triggers the MAX98357A speaker chime tone test."""
    success = esp32_client.trigger_chime()
    return {"ok": success}


@router.get("/hardware/esp32-health")
def get_esp32_health():
    """Queries the ESP32-S3 microcontroller directly over local Wi-Fi."""
    return esp32_client.check_health()


@router.post("/hardware/stop-voice")
def stop_hardware_voice(reset_state: bool = True):
    """Immediately halts audio playback on ESP32 speaker and optionally resets display and LED to IDLE."""
    if reset_state:
        rgb_controller.set_state("IDLE")
    esp_res = esp32_client.stop_speaker(reset_display=reset_state)
    return {"ok": True, "esp32_stopped": esp_res}

