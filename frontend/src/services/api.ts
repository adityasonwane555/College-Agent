/**
 * BUDDY AI 2.0 — Frontend API Client & Communication Layer
 *
 * Architecture & Features:
 *   - Dynamic Host Resolution:
 *       - Dynamically detects runtime browser window hostname or falls back to '127.0.0.1' (port 8000).
 *   - Audio Target Routing:
 *       - Dispatches audio output target ('browser', 'robot', or 'both') via local storage persistence.
 *   - Multimodal Endpoints:
 *       - Chat query dispatch with grounded RAG citations and TTS metadata.
 *       - Speech-to-Text file uploading & ESP32 I2S on-demand mic triggers.
 *       - TTS synthesis with Edge-TTS and Fish Audio integration.
 *       - Real-time ESP32-S3 RGB LED animations and non-blocking failure tolerance.
 *   - Knowledge Lifecycle & Administration:
 *       - Document upload with JWT authorization, pending review approval/rejection, and index rebuilding.
 */

import type {
  HealthStatus, AppConfig, Department, CollegeEvent,
  CollegeAnnouncement, FAQ, DocumentMeta, Citation
} from '../types';

const rawHost = typeof window !== 'undefined' && window.location.hostname ? window.location.hostname : '127.0.0.1';
export const API_HOST = rawHost === 'localhost' ? '127.0.0.1' : rawHost;
export const API_BASE = `http://${API_HOST}:8000/api`;

/**
 * Structured chat response returned by the backend reception agent.
 */
export interface ChatApiResponse {
  response: string;
  session_id: string;
  citations: Citation[];
  is_simulated: boolean;
  tts?: {
    enabled: boolean;
    method: string;
    audio_url?: string;
    text?: string;
    message?: string;
  };
}

export const api = {
  /**
   * Retrieves operational health telemetry across Ollama, Whisper, TTS, and database connections.
   */
  async getHealth(): Promise<HealthStatus> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error(`Health check failed (${res.status})`);
    return res.json();
  },

  /**
   * Fetches public application configuration including active AI models and language settings.
   */
  async getConfig(): Promise<AppConfig> {
    const res = await fetch(`${API_BASE}/config`);
    if (!res.ok) throw new Error(`Config fetch failed (${res.status})`);
    return res.json();
  },

  /**
   * Dispatches a user query to the agent orchestrator, forwarding session IDs and audio target preferences.
   */
  async sendChatMessage(message: string, sessionId?: string, audioOutputTarget?: string): Promise<ChatApiResponse> {
    const target = audioOutputTarget || (typeof window !== 'undefined' ? localStorage.getItem('buddy_audio_output_target') || 'both' : 'both');
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        audio_output_target: target
      })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Chat request failed (${res.status})`);
    }
    return res.json();
  },

  /**
   * Uploads recorded client audio (WAV/WebM/OGG) for server-side Faster-Whisper transcription.
   */
  async transcribeAudio(audioBlob: Blob): Promise<{ success: boolean; text: string; error?: string }> {
    const formData = new FormData();
    const type = audioBlob.type || '';
    const filename = type.includes('webm') ? 'recording.webm' : (type.includes('ogg') ? 'recording.ogg' : 'recording.wav');
    formData.append('audio', audioBlob, filename);

    const res = await fetch(`${API_BASE}/voice/transcribe`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      throw new Error(`Audio transcription failed (${res.status})`);
    }
    return res.json();
  },

  /**
   * Triggers the ESP32 INMP441 I2S microphone to capture audio over Wi-Fi and transcribe it on the host.
   */
  async recordEsp32Mic(seconds: number = 4): Promise<{ success: boolean; text: string; error?: string }> {
    const res = await fetch(`${API_BASE}/voice/record-esp32?seconds=${seconds}`, {
      method: 'POST'
    });
    if (!res.ok) {
      throw new Error(`ESP32 mic recording failed (${res.status})`);
    }
    return res.json();
  },

  /**
   * Synthesizes input text to speech using Edge-TTS or Fish Audio.
   */
  async synthesizeSpeech(text: string) {
    const res = await fetch(`${API_BASE}/voice/speak`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    if (!res.ok) throw new Error(`Speech synthesis failed (${res.status})`);
    return res.json();
  },

  /**
   * Updates the ESP32-S3 onboard RGB LED animation state and frequency amplitude bands.
   * Designed to fail silently without disrupting the UI or voice pipeline if the robot is offline.
   */
  async setLedState(
    state: string,
    amplitude: number = 0.0,
    bass?: number,
    mid?: number,
    treble?: number
  ): Promise<void> {
    try {
      await fetch(`${API_BASE}/hardware/led-state`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ state, amplitude, bass, mid, treble })
      });
    } catch {
      // Non-blocking: never disrupt voice or UI if offline
    }
  },

  /**
   * Immediately halts audio playback on the ESP32 speaker and synchronizes display & LED states.
   */
  async stopVoice(targetState: string = 'IDLE'): Promise<{ ok: boolean }> {
    try {
      const stateParam = encodeURIComponent(targetState);
      const res = await fetch(`${API_BASE}/hardware/stop-voice?target_state=${stateParam}`, { method: 'POST' });
      return res.json();
    } catch {
      return { ok: false };
    }
  },

  /**
   * Queries connection status and active animation state of the ESP32 RGB LED ring.
   */
  async getLedStatus(): Promise<{ ok: boolean; state?: string; is_connected?: boolean }> {
    try {
      const res = await fetch(`${API_BASE}/hardware/led-status`);
      return res.json();
    } catch {
      return { ok: false, is_connected: false };
    }
  },

  /**
   * Sends an active ping to verify network reachability of the ESP32 hardware node.
   */
  async pingLed(): Promise<{ ok: boolean; message?: string }> {
    try {
      const res = await fetch(`${API_BASE}/hardware/led-ping`, { method: 'POST' });
      return res.json();
    } catch (e: any) {
      return { ok: false, message: e.message };
    }
  },

  // College Data
  /**
   * Fetches the complete directory of college departments and offices.
   */
  async getDepartments(): Promise<Department[]> {
    const res = await fetch(`${API_BASE}/college/departments`);
    return res.json();
  },

  /**
   * Fetches verified upcoming college events and seminars.
   */
  async getEvents(): Promise<CollegeEvent[]> {
    const res = await fetch(`${API_BASE}/college/events`);
    return res.json();
  },

  /**
   * Fetches campus-wide administrative announcements.
   */
  async getAnnouncements(): Promise<CollegeAnnouncement[]> {
    const res = await fetch(`${API_BASE}/college/announcements`);
    return res.json();
  },

  /**
   * Fetches operational office and campus facility hours.
   */
  async getHours(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/college/hours`);
    return res.json();
  },

  /**
   * Fetches curated frequently asked questions.
   */
  async getFaqs(): Promise<FAQ[]> {
    const res = await fetch(`${API_BASE}/college/faqs`);
    return res.json();
  },

  // Documents
  /**
   * Lists all uploaded and ingested documents in the knowledge base.
   */
  async listDocuments(): Promise<DocumentMeta[]> {
    const res = await fetch(`${API_BASE}/documents/list`);
    return res.json();
  },

  /**
   * Uploads a document to the knowledge repository using administrative bearer authorization.
   */
  async uploadDocument(file: File, token: string) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  // Admin
  /**
   * Authenticates administrative credentials and returns a signed bearer token.
   */
  async adminLogin(username: string, password: string): Promise<string> {
    const res = await fetch(`${API_BASE}/admin/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    if (!res.ok) throw new Error('Invalid administrator credentials.');
    const data = await res.json();
    return data.token;
  },

  /**
   * Creates or updates a curated FAQ item in the database.
   */
  async addFaq(faq: FAQ, token: string) {
    const res = await fetch(`${API_BASE}/admin/faq`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(faq)
    });
    if (!res.ok) throw new Error('Failed to create FAQ');
    return res.json();
  },

  /**
   * Registers or updates a department directory record.
   */
  async addDepartment(dept: Department, token: string) {
    const res = await fetch(`${API_BASE}/admin/department`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(dept)
    });
    if (!res.ok) throw new Error('Failed to save department');
    return res.json();
  },

  /**
   * Publishes a new college event to the campus calendar.
   */
  async addEvent(event: CollegeEvent, token: string) {
    const res = await fetch(`${API_BASE}/admin/event`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(event)
    });
    if (!res.ok) throw new Error('Failed to save event');
    return res.json();
  },

  /**
   * Retrieves all document diffs pending administrative approval.
   */
  async listPendingUpdates(token: string) {
    const res = await fetch(`${API_BASE}/admin/knowledge/pending`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to load pending updates');
    return res.json();
  },

  /**
   * Approves a staged document diff and activates its knowledge chunks.
   */
  async approvePendingUpdate(id: number, token: string) {
    const res = await fetch(`${API_BASE}/admin/knowledge/approve/${id}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to approve update');
    return res.json();
  },

  /**
   * Rejects a staged document diff and purges it from the staging queue.
   */
  async rejectPendingUpdate(id: number, token: string) {
    const res = await fetch(`${API_BASE}/admin/knowledge/reject/${id}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to reject update');
    return res.json();
  },

  /**
   * Forces a complete re-indexing of full-text FTS5 and semantic vector embeddings.
   */
  async rebuildIndexes(token: string) {
    const res = await fetch(`${API_BASE}/admin/indexes/rebuild`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to rebuild indexes');
    return res.json();
  },

  /**
   * Gathers end-to-end system telemetry, provider health, and document counts.
   */
  async getDiagnostics(token: string) {
    const res = await fetch(`${API_BASE}/admin/diagnostics`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to fetch diagnostics');
    return res.json();
  }
};
