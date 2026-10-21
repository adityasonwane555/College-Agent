"""
FastAPI Server Integration for BUDDY-Fish-TTS.
Provides REST API endpoints for speech synthesis and audio streaming.
"""

import time
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .tts_engine import FishTTSEngine
from .config import tts_config, OUTPUT_DIR

app = FastAPI(
    title="BUDDY Fish Audio S2 Pro TTS Service",
    description="Local offline speech generation service for the BUDDY Robot.",
    version="1.0.0"
)

engine = FishTTSEngine()


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000, description="Text to synthesize")
    prompt_audio: Optional[str] = Field(None, description="Path to voice reference audio for cloning")
    prompt_text: Optional[str] = Field(None, description="Transcript of the voice reference audio")
    temperature: Optional[float] = Field(0.7, ge=0.1, le=1.5, description="Sampling temperature")


class TTSResponse(BaseModel):
    success: bool
    audio_url: str
    duration_seconds: float
    generation_time_seconds: float
    real_time_factor: float
    file_size_bytes: int


@app.get("/health")
def health_check():
    status = engine.get_status()
    return {
        "status": "online" if status["ready"] else "degraded",
        "details": status
    }


@app.post("/tts", response_model=TTSResponse)
def synthesize_speech_endpoint(req: TTSRequest):
    try:
        out_filename = f"speech_{int(time.time() * 1000)}.wav"
        out_path = OUTPUT_DIR / out_filename

        result = engine.generate(
            text=req.text,
            output_path=str(out_path),
            prompt_audio=req.prompt_audio,
            prompt_text=req.prompt_text,
            temperature=req.temperature
        )

        return TTSResponse(
            success=True,
            audio_url=f"/audio/{out_filename}",
            duration_seconds=result["duration_seconds"],
            generation_time_seconds=result["generation_time_seconds"],
            real_time_factor=result["real_time_factor"],
            file_size_bytes=result["file_size_bytes"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech synthesis error: {str(e)}"
        )


@app.get("/audio/{filename}")
def serve_audio(filename: str):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found.")
    return FileResponse(file_path, media_type="audio/wav")
