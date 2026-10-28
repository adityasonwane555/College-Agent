import React, { useState, useEffect, useCallback } from 'react';
import type { RobotState, ChatMessage, HealthStatus, AppConfig } from './types';
import { api } from './services/api';
import { useVoice } from './hooks/useVoice';
import { RobotFace } from './components/RobotFace';
import { StatusIndicator } from './components/StatusIndicator';
import { VoiceControls } from './components/VoiceControls';
import { ConversationPanel } from './components/ConversationPanel';
import { SettingsPanel } from './components/SettingsPanel';
import { AdminPanel } from './components/AdminPanel';
import { Send, Settings, ShieldCheck, Sparkles } from 'lucide-react';
import './styles/global.css';
import './styles/robot.css';

const SUGGESTIONS = [
  "What is our college name and heritage?",
  "Who is the Principal and where is his office?",
  "Tell me about B.Tech admissions under DTE Code 6794.",
  "Which engineering branches are offered at APCOER?",
  "What companies visit for campus placements?"
];

export const App: React.FC = () => {
  const [robotState, setRobotState] = useState<RobotState>('idle');
  const [statusText, setStatusText] = useState<string>('');
  const [inputText, setInputText] = useState<string>('');
  const [sessionId, setSessionId] = useState<string>(() => 'sess_' + Math.random().toString(36).substring(2, 9));
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [config, setConfig] = useState<AppConfig | null>(null);

  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isAdminOpen, setIsAdminOpen] = useState(false);

  // Load backend health and config on mount
  const refreshSystemData = useCallback(async (): Promise<boolean> => {
    try {
      const [h, c] = await Promise.all([api.getHealth(), api.getConfig()]);
      setHealth(h);
      setConfig(c);
      return true;
    } catch (e) {
      console.warn("Backend not reachable yet:", e);
      setHealth(null);
      return false;
    }
  }, []);

  useEffect(() => {
    let active = true;
    let timer: number;

    const poll = async () => {
      const ok = await refreshSystemData();
      if (!active) return;
      // Fast retry (2.5s) if backend is still connecting/offline, otherwise standard refresh (10s)
      timer = window.setTimeout(poll, ok ? 10000 : 2500);
    };

    poll();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [refreshSystemData]);

  // Voice Interaction Hook
  const {
    isRecording,
    isSpeaking,
    isMuted,
    startRecording,
    stopRecording,
    stopSpeaking,
    toggleMute,
    speak,
    audioInputDevices,
    selectedInputDeviceId,
    changeAudioInputDevice,
    activeMicLabel,
    refreshAudioDevices,
    audioOutputTarget,
    setAudioOutputTarget,
    audioInputSource,
    setAudioInputSource
  } = useVoice({
    onTranscriptionComplete: (text) => {
      handleSendMessage(text);
    },
    onStateChange: (newState) => {
      setRobotState(newState as RobotState);
    },
    onError: (errMessage) => {
      setStatusText(errMessage);
      setRobotState('error');
      setTimeout(() => setRobotState('idle'), 4000);
    }
  });

  // Handle User Message Submission
  const handleSendMessage = async (msgText: string) => {
    const trimmed = msgText.trim();
    if (!trimmed) return;

    setInputText('');
    stopSpeaking(false);

    const userMsg: ChatMessage = {
      id: 'usr_' + Date.now(),
      sender: 'user',
      text: trimmed,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setRobotState('thinking');
    api.setLedState('THINKING');
    setStatusText("Consulting college records & documents...");

    try {
      const res = await api.sendChatMessage(trimmed, sessionId);

      const botMsg: ChatMessage = {
        id: 'bot_' + Date.now(),
        sender: 'assistant',
        text: res.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        citations: res.citations,
        isSimulated: res.is_simulated
      };

      setMessages((prev) => [...prev, botMsg]);

      // Voice output (asynchronously streams without blocking UI)
      if (res.tts && res.tts.enabled) {
        speak(res.response, res.tts.audio_url);
      } else {
        setRobotState('happy');
        setStatusText("Here is what I found!");
        api.setLedState('IDLE');
        setTimeout(() => {
          setRobotState('idle');
          setStatusText('');
        }, 2000);
      }
    } catch (err: any) {
      setRobotState('error');
      api.setLedState('ERROR');
      setStatusText(err.message || "Failed to reach Buddy backend.");
      setTimeout(() => {
        setRobotState('idle');
        api.setLedState('IDLE');
        setStatusText('');
      }, 4000);
    }
  };

  const handleClearSession = () => {
    setMessages([]);
    setSessionId('sess_' + Math.random().toString(36).substring(2, 9));
    setRobotState('idle');
    setStatusText('');
  };

  return (
    <div style={{
      position: 'relative',
      width: '100vw',
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden'
    }}>
      {/* Background Ambience */}
      <div className="kiosk-background" />
      <div className="kiosk-grid-overlay" />

      {/* Top Header Bar */}
      <header style={{
        position: 'relative',
        zIndex: 10,
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '16px 28px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.06)'
      }}>
        {/* Brand / Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #0284c7 0%, #00f0ff 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 15px rgba(0, 240, 255, 0.4)'
          }}>
            <Sparkles size={18} color="#04101e" />
          </div>
          <div>
            <h1 style={{ fontSize: '18px', fontWeight: 800, letterSpacing: '0.05em', color: '#f8fafc', lineHeight: 1.1 }}>
              BUDDY
            </h1>
            <span style={{ fontSize: '11px', color: '#38bdf8', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              Smart AI College Reception
            </span>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            onClick={() => setIsAdminOpen(true)}
            className="btn-secondary"
            style={{ fontSize: '13px', padding: '6px 14px' }}
          >
            <ShieldCheck size={15} color="#38bdf8" />
            Admin
          </button>
          <button
            onClick={() => setIsSettingsOpen(true)}
            className="btn-secondary"
            style={{ fontSize: '13px', padding: '6px 14px' }}
          >
            <Settings size={15} color="#00f0ff" />
            Settings
          </button>
        </div>
      </header>

      {/* Main Kiosk Content Area */}
      <main style={{
        flex: 1,
        position: 'relative',
        zIndex: 10,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '10px 24px 16px 24px',
        overflowY: 'auto'
      }}>
        {/* Animated Robot Face */}
        <div style={{ margin: 'auto 0 0 0' }}>
          <RobotFace state={robotState} />
          <StatusIndicator state={robotState} customMessage={statusText} />
        </div>

        {/* Conversation Transcript */}
        <div style={{ width: '100%', maxWidth: '720px', margin: '4px 0' }}>
          <ConversationPanel messages={messages} onClearSession={handleClearSession} />
        </div>

        {/* Voice Push-to-Talk Controls */}
        <VoiceControls
          isRecording={isRecording}
          isSpeaking={isSpeaking}
          isMuted={isMuted}
          onStartRecord={startRecording}
          onStopRecord={stopRecording}
          onStopSpeaking={stopSpeaking}
          onToggleMute={toggleMute}
          activeMicLabel={activeMicLabel}
          onOpenSettings={() => setIsSettingsOpen(true)}
          audioOutputTarget={audioOutputTarget}
          onSelectOutputTarget={setAudioOutputTarget}
          audioInputSource={audioInputSource}
          onSelectInputSource={setAudioInputSource}
        />

        {/* Suggestion Chips */}
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
          maxWidth: '780px',
          margin: '6px 0 10px 0'
        }}>
          {SUGGESTIONS.map((chip, idx) => (
            <button
              key={idx}
              onClick={() => handleSendMessage(chip)}
              style={{
                background: 'rgba(15, 23, 42, 0.65)',
                border: '1px solid rgba(56, 189, 248, 0.2)',
                borderRadius: '16px',
                padding: '5px 12px',
                color: '#cbd5e1',
                fontSize: '12px',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              className="glow-border"
            >
              {chip}
            </button>
          ))}
        </div>

        {/* Text Input Box Alternative */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage(inputText);
          }}
          style={{
            width: '100%',
            maxWidth: '720px',
            display: 'flex',
            gap: '10px',
            margin: '0 0 auto 0'
          }}
        >
          <input
            type="text"
            placeholder="Type your college question here or use the microphone..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            disabled={robotState === 'thinking'}
            style={{
              flex: 1,
              padding: '12px 18px',
              borderRadius: '14px',
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              color: '#f8fafc',
              fontSize: '14px',
              outline: 'none',
              boxShadow: 'inset 0 2px 4px rgba(0, 0, 0, 0.3)'
            }}
          />
          <button
            type="submit"
            disabled={!inputText.trim() || robotState === 'thinking'}
            className="btn-primary"
            style={{ padding: '0 20px', borderRadius: '14px' }}
          >
            <Send size={16} />
            <span>Send</span>
          </button>
        </form>
      </main>

      {/* Footer System Status Bar */}
      <footer style={{
        position: 'relative',
        zIndex: 10,
        flexShrink: 0,
        padding: '8px 24px',
        borderTop: '1px solid rgba(255, 255, 255, 0.06)',
        background: 'rgba(5, 8, 16, 0.85)',
        backdropFilter: 'blur(10px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontSize: '11px',
        color: '#64748b'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span>
            AI: <strong style={{ color: health?.ollama.running ? '#34d399' : '#fbbf24' }}>
              {health?.ollama.running ? `Local (${config?.model_name})` : 'Simulated Reception'}
            </strong>
          </span>
          <span>
            Voice: <strong style={{ color: health?.whisper.installed ? '#38bdf8' : '#94a3b8' }}>
              {health?.whisper.installed ? 'faster-whisper' : 'Web Speech'}
            </strong>
          </span>
          <span>
            Server: <strong style={{ color: health?.status === 'online' ? '#34d399' : '#f87171' }}>
              {health?.status === 'online' ? 'Online (127.0.0.1:8000)' : 'Connecting...'}
            </strong>
          </span>
          <span>
            Docs: <strong style={{ color: '#00f0ff' }}>{health?.documents_indexed ?? 0} Indexed</strong>
          </span>
        </div>

        <div>
          ESP32 IoT Bridge: <span style={{ color: '#64748b' }}>Standby (Ready for Hardware)</span>
        </div>
      </footer>

      {/* Modals */}
      {isSettingsOpen && (
        <SettingsPanel
          config={config}
          health={health}
          onClose={() => setIsSettingsOpen(false)}
          audioInputDevices={audioInputDevices}
          selectedInputDeviceId={selectedInputDeviceId}
          onSelectInputDevice={changeAudioInputDevice}
          activeMicLabel={activeMicLabel}
          onRefreshDevices={refreshAudioDevices}
          audioOutputTarget={audioOutputTarget}
          onSelectOutputTarget={setAudioOutputTarget}
          audioInputSource={audioInputSource}
          onSelectInputSource={setAudioInputSource}
        />
      )}

      {isAdminOpen && (
        <AdminPanel
          onClose={() => setIsAdminOpen(false)}
          onDataModified={refreshSystemData}
        />
      )}
    </div>
  );
};

export default App;
