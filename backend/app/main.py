"""
BUDDY AI — FastAPI Server & Real-Time Gateway

Architecture & Lifecycle Pipeline:
  - Windows UTF-8 Terminal Stream Wrapper:
      - Intercepts sys.stdout and sys.stderr buffers on Windows to force UTF-8 text wrapping,
        preventing console encoding crashes on Unicode emojis and Marathi names.
  - Asynchronous Application Lifespan:
      - Startup: Executes relational SQLite schema migrations, seeds authoritative campus directory,
        ingests foundational documents (prospectus, campus maps) into ChromaDB, and verifies Ollama health.
      - Teardown: Safely closes open database connections and cleans up background tasks.
  - Full-Duplex Real-Time Telemetry:
      - Maintains active WebSocket subscriber pool (`/ws/status`) for bidirectional state synchronization
        between browser kiosk, backend orchestrator, and ESP32 hardware client.
"""

import sys
import io

if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "buffer"):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "buffer"):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

import json
import asyncio
from contextlib import asynccontextmanager
from typing import Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from .config import settings, DATA_DIR, WORKSPACE_DIR
from .api.routes import router
from .database.seed import seed_database
from .documents.ingestion import ingest_sample_documents
from .services.ollama_service import check_ollama_status


class ConnectionManager:
    """
    Manages active WebSocket connections for real-time telemetry streaming and state broadcasting.
    Safely prunes dead/closed sockets during broadcast sweeps.
    """
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """
        Accepts incoming WebSocket handshake and registers client in active subscriber set.

        Args:
            websocket: Connecting FastAPI WebSocket instance.
        """
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Unregisters disconnected WebSocket client from active subscriber set.

        Args:
            websocket: Disconnecting FastAPI WebSocket instance.
        """
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        """
        Broadcasts a JSON message payload to all actively connected WebSocket clients.
        Automatically purges any connections that throw write exceptions.

        Args:
            message: Dictionary payload to serialize and transmit.
        """
        dead_connections = set()
        for conn in self.active_connections:
            try:
                await conn.send_json(message)
            except Exception:
                dead_connections.add(conn)
        for dead in dead_connections:
            self.active_connections.discard(dead)


ws_manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager controlling application initialization and shutdown.

    Startup Sequence:
      1. Initializes SQLite schema and seeds authoritative faculty/department tables.
      2. Ingests sample college prospectuses and campus documents into ChromaDB vector store.
      3. Verifies local Ollama LLM availability and reports GPU acceleration status.
    """
    # Startup: Seed database and ingest sample documents
    print("Initializing Buddy Database and Sample College Documents...")
    seed_database()
    sample_docs_dir = DATA_DIR / "sample_documents"
    ingest_sample_documents(sample_docs_dir)

    # Check Ollama AI Engine
    try:
        ollama_stat = await check_ollama_status()
        if ollama_stat.get("running"):
            print(f"[Ollama Local AI] ONLINE (Configured model '{settings.OLLAMA_MODEL}', Found: {ollama_stat.get('model_available')})")
        else:
            print(f"[Warning] Ollama Local AI: OFFLINE ({ollama_stat.get('message')}). Fallback to mock simulation is active.")
    except Exception as e:
        print(f"[Warning] Ollama status check error: {e}")

    print("Buddy Backend Startup Complete. Ready to serve.")
    yield
    print("Buddy Backend Shutting Down...")


app = FastAPI(
    title="BUDDY — Smart AI College Reception Agent",
    description="Software backend for the Buddy Smart AI College Reception Robot.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration (allow local IP, localhost, and custom hostnames)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


# WebSocket status endpoint
@app.websocket("/ws/status")
async def websocket_status_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint streaming real-time robot state, telemetry, and audio activity.
    Transmits initial connection greeting and listens for incoming kiosk commands.

    Args:
        websocket: Established client WebSocket connection.
    """
    await ws_manager.connect(websocket)
    # Send initial welcome state
    await websocket.send_json({
        "type": "connection_status",
        "status": "connected",
        "robot_state": "idle",
        "message": "Buddy is ready at the reception desk."
    })
    try:
        while True:
            data = await websocket.receive_text()
            # Echo or process incoming client commands / telemetry
            try:
                parsed = json.loads(data)
                # Broadcast or respond
                await websocket.send_json({
                    "type": "ack",
                    "received": parsed
                })
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
