/**
 * BUDDY AI 2.0 — Frontend TypeScript Type Definitions
 *
 * Architecture & Client Contracts:
 *   - Robot Visual & Emotional States:
 *       - Defines canonical facial expression and LED modes: 'idle' | 'listening' | 'thinking' | 'speaking' | 'happy' | 'error'.
 *   - Grounding & Citations:
 *       - Structures attribution references attached to agent answers (source document, page, section, snippet).
 *   - Telemetry & System Config:
 *       - Models backend health status across Ollama, Whisper, TTS, and relational databases.
 *   - Institutional Entities:
 *       - Types for academic departments, campus events, announcements, and FAQs mirrored from SQLite schemas.
 */

/**
 * Visual and operational state machine for the robot face and hardware LED indicators.
 */
export type RobotState = 'idle' | 'listening' | 'thinking' | 'speaking' | 'happy' | 'error';

/**
 * Verifiable institutional citation reference linking answers to ingested documents.
 */
export interface Citation {
  source: string;
  page?: number;
  section?: string;
  relevance_score?: number;
  snippet: string;
}

/**
 * Individual chat message entry rendered in the conversation log.
 */
export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  citations?: Citation[];
  isSimulated?: boolean;
}

/**
 * Operational telemetry report returned by the backend /api/health endpoint.
 */
export interface HealthStatus {
  status: string;
  service: string;
  database: string;
  ollama: {
    running: boolean;
    models: string[];
    configured_model: string;
    model_available: boolean;
    message: string;
  };
  whisper: {
    installed: boolean;
    model: string;
    device: string;
  };
  tts: {
    enabled: boolean;
    piper_voice_configured: boolean;
  };
  documents_indexed: number;
  web_search_enabled: boolean;
}

/**
 * Public runtime configurations exposed by the backend /api/config route.
 */
export interface AppConfig {
  model_name: string;
  stt_language: string;
  stt_model: string;
  tts_enabled: boolean;
  web_search_enabled: boolean;
  mock_fallback_active: boolean;
}

/**
 * Academic or administrative department directory record.
 */
export interface Department {
  id?: number;
  name: string;
  code: string;
  block: string;
  floor: string;
  hod: string;
  contact_email: string;
  description: string;
}

/**
 * Campus calendar event or symposium record.
 */
export interface CollegeEvent {
  id?: number;
  title: string;
  date: string;
  time: string;
  venue: string;
  description: string;
  organizer: string;
}

/**
 * Official administrative notice or circular.
 */
export interface CollegeAnnouncement {
  id?: number;
  title: string;
  content: string;
  date_posted: string;
  priority: string;
}

/**
 * Curated frequently asked question and official response.
 */
export interface FAQ {
  id?: number;
  question: string;
  answer: string;
  category: string;
}

/**
 * Metadata record for an ingested knowledge base document.
 */
export interface DocumentMeta {
  id?: number;
  filename: string;
  title: string;
  total_pages: number;
  uploaded_at: string;
  chunk_count: number;
}
