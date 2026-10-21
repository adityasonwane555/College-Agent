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


# Active WebSocket clients tracking
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
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
    # Startup: Seed database and ingest sample documents
    print("Initializing Buddy Database and Sample College Documents...")
    seed_database()
    sample_docs_dir = DATA_DIR / "sample_documents"
    ingest_sample_documents(sample_docs_dir)
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
