export type RobotState = 'idle' | 'listening' | 'thinking' | 'speaking' | 'happy' | 'error';

export interface Citation {
  source: string;
  page?: number;
  section?: string;
  relevance_score?: number;
  snippet: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  citations?: Citation[];
  isSimulated?: boolean;
}

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

export interface AppConfig {
  model_name: string;
  stt_language: string;
  stt_model: string;
  tts_enabled: boolean;
  web_search_enabled: boolean;
  mock_fallback_active: boolean;
}

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

export interface CollegeEvent {
  id?: number;
  title: string;
  date: string;
  time: string;
  venue: string;
  description: string;
  organizer: string;
}

export interface CollegeAnnouncement {
  id?: number;
  title: string;
  content: string;
  date_posted: string;
  priority: string;
}

export interface FAQ {
  id?: number;
  question: string;
  answer: string;
  category: string;
}

export interface DocumentMeta {
  id?: number;
  filename: string;
  title: string;
  total_pages: number;
  uploaded_at: string;
  chunk_count: number;
}
