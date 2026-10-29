import type {
  HealthStatus, AppConfig, Department, CollegeEvent,
  CollegeAnnouncement, FAQ, DocumentMeta, Citation
} from '../types';

const rawHost = typeof window !== 'undefined' && window.location.hostname ? window.location.hostname : '127.0.0.1';
export const API_HOST = rawHost === 'localhost' ? '127.0.0.1' : rawHost;
export const API_BASE = `http://${API_HOST}:8000/api`;

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
  async getHealth(): Promise<HealthStatus> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error(`Health check failed (${res.status})`);
    return res.json();
  },

  async getConfig(): Promise<AppConfig> {
    const res = await fetch(`${API_BASE}/config`);
    if (!res.ok) throw new Error(`Config fetch failed (${res.status})`);
    return res.json();
  },

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

  async recordEsp32Mic(seconds: number = 4): Promise<{ success: boolean; text: string; error?: string }> {
    const res = await fetch(`${API_BASE}/voice/record-esp32?seconds=${seconds}`, {
      method: 'POST'
    });
    if (!res.ok) {
      throw new Error(`ESP32 mic recording failed (${res.status})`);
    }
    return res.json();
  },

  async synthesizeSpeech(text: string) {
    const res = await fetch(`${API_BASE}/voice/speak`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    if (!res.ok) throw new Error(`Speech synthesis failed (${res.status})`);
    return res.json();
  },

  // Hardware ESP32-S3 RGB LED Control
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

  async stopVoice(targetState: string = 'IDLE'): Promise<{ ok: boolean }> {
    try {
      const stateParam = encodeURIComponent(targetState);
      const res = await fetch(`${API_BASE}/hardware/stop-voice?target_state=${stateParam}`, { method: 'POST' });
      return res.json();
    } catch {
      return { ok: false };
    }
  },

  async getLedStatus(): Promise<{ ok: boolean; state?: string; is_connected?: boolean }> {
    try {
      const res = await fetch(`${API_BASE}/hardware/led-status`);
      return res.json();
    } catch {
      return { ok: false, is_connected: false };
    }
  },

  async pingLed(): Promise<{ ok: boolean; message?: string }> {
    try {
      const res = await fetch(`${API_BASE}/hardware/led-ping`, { method: 'POST' });
      return res.json();
    } catch (e: any) {
      return { ok: false, message: e.message };
    }
  },

  // College Data
  async getDepartments(): Promise<Department[]> {
    const res = await fetch(`${API_BASE}/college/departments`);
    return res.json();
  },

  async getEvents(): Promise<CollegeEvent[]> {
    const res = await fetch(`${API_BASE}/college/events`);
    return res.json();
  },

  async getAnnouncements(): Promise<CollegeAnnouncement[]> {
    const res = await fetch(`${API_BASE}/college/announcements`);
    return res.json();
  },

  async getHours(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/college/hours`);
    return res.json();
  },

  async getFaqs(): Promise<FAQ[]> {
    const res = await fetch(`${API_BASE}/college/faqs`);
    return res.json();
  },

  // Documents
  async listDocuments(): Promise<DocumentMeta[]> {
    const res = await fetch(`${API_BASE}/documents/list`);
    return res.json();
  },

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

  async listPendingUpdates(token: string) {
    const res = await fetch(`${API_BASE}/admin/knowledge/pending`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to load pending updates');
    return res.json();
  },

  async approvePendingUpdate(id: number, token: string) {
    const res = await fetch(`${API_BASE}/admin/knowledge/approve/${id}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to approve update');
    return res.json();
  },

  async rejectPendingUpdate(id: number, token: string) {
    const res = await fetch(`${API_BASE}/admin/knowledge/reject/${id}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to reject update');
    return res.json();
  },

  async rebuildIndexes(token: string) {
    const res = await fetch(`${API_BASE}/admin/indexes/rebuild`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to rebuild indexes');
    return res.json();
  },

  async getDiagnostics(token: string) {
    const res = await fetch(`${API_BASE}/admin/diagnostics`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Failed to fetch diagnostics');
    return res.json();
  }
};
