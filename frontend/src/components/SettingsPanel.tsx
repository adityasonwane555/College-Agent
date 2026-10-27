import React, { useState, useEffect, useRef } from 'react';
import type { AppConfig, HealthStatus } from '../types';
import { X, Cpu, Mic, Volume2, Globe, Server, CheckCircle2, AlertTriangle, RefreshCw, Radio } from 'lucide-react';

interface SettingsPanelProps {
  config: AppConfig | null;
  health: HealthStatus | null;
  onClose: () => void;
  audioInputDevices?: MediaDeviceInfo[];
  selectedInputDeviceId?: string;
  onSelectInputDevice?: (deviceId: string) => void;
  activeMicLabel?: string;
  onRefreshDevices?: () => void;
  audioOutputTarget?: 'robot' | 'laptop' | 'both';
  onSelectOutputTarget?: (target: 'robot' | 'laptop' | 'both') => void;
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({
  config,
  health,
  onClose,
  audioInputDevices = [],
  selectedInputDeviceId = 'default',
  onSelectInputDevice,
  activeMicLabel,
  onRefreshDevices,
  audioOutputTarget = 'robot',
  onSelectOutputTarget
}) => {
  const [isTestingMic, setIsTestingMic] = useState(false);
  const [micVolume, setMicVolume] = useState(0);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  const stopMicTest = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(t => t.stop());
      mediaStreamRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    setIsTestingMic(false);
    setMicVolume(0);
  };

  const startMicTest = async () => {
    stopMicTest();
    try {
      const constraints: MediaStreamConstraints = {
        audio: (selectedInputDeviceId && selectedInputDeviceId !== 'default')
          ? { deviceId: { exact: selectedInputDeviceId } }
          : true
      };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      mediaStreamRef.current = stream;

      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      audioContextRef.current = audioCtx;
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);

      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      setIsTestingMic(true);

      const updateMeter = () => {
        analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const average = sum / dataArray.length;
        setMicVolume(Math.min(100, Math.round((average / 128) * 100)));
        animationFrameRef.current = requestAnimationFrame(updateMeter);
      };
      updateMeter();
    } catch (err) {
      console.error("Microphone test error:", err);
      alert("Could not access the selected microphone for testing. Please ensure browser permissions are allowed.");
      stopMicTest();
    }
  };

  useEffect(() => {
    return () => {
      stopMicTest();
    };
  }, []);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content glass-panel" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          paddingBottom: '14px',
          marginBottom: '20px'
        }}>
          <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Server size={20} color="#00f0ff" />
            Buddy System Settings & Health
          </h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Diagnostic Status Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '20px' }}>
          {/* Ollama Status */}
          <div style={{
            padding: '12px',
            borderRadius: '12px',
            background: 'rgba(15, 23, 42, 0.6)',
            border: '1px solid rgba(255, 255, 255, 0.08)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', fontWeight: 600, color: '#38bdf8' }}>
              <Cpu size={15} />
              Local Ollama AI
            </div>
            <div style={{ marginTop: '6px', fontSize: '12px', color: '#cbd5e1' }}>
              {health?.ollama.running ? (
                <span style={{ color: '#34d399', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <CheckCircle2 size={13} /> Connected ({health.ollama.configured_model})
                </span>
              ) : (
                <span style={{ color: '#fbbf24', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <AlertTriangle size={13} /> Fallback AI Active (Ollama offline)
                </span>
              )}
            </div>
          </div>

          {/* Voice Recognition Status */}
          <div style={{
            padding: '12px',
            borderRadius: '12px',
            background: 'rgba(15, 23, 42, 0.6)',
            border: '1px solid rgba(255, 255, 255, 0.08)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', fontWeight: 600, color: '#00f0ff' }}>
              <Mic size={15} />
              Speech Engine
            </div>
            <div style={{ marginTop: '6px', fontSize: '12px', color: '#cbd5e1' }}>
              {health?.whisper.installed ? (
                <span style={{ color: '#34d399', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <CheckCircle2 size={13} /> faster-whisper ({health.whisper.model})
                </span>
              ) : (
                <span style={{ color: '#94a3b8' }}>Web Speech API fallback</span>
              )}
            </div>
          </div>

          {/* Hardware ESP32-S3 RGB LED Status */}
          <div style={{
            gridColumn: '1 / -1',
            padding: '12px',
            borderRadius: '12px',
            background: 'rgba(15, 23, 42, 0.6)',
            border: '1px solid rgba(255, 255, 255, 0.08)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', fontWeight: 600, color: '#c084fc' }}>
                <Server size={15} />
                ESP32-S3 Hardware RGB LED (GPIO 48)
              </div>
              <span style={{ fontSize: '11px', color: '#a855f7', background: 'rgba(168, 85, 247, 0.15)', padding: '2px 8px', borderRadius: '12px' }}>
                Wi-Fi Synced
              </span>
            </div>
            <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>
              Automatically synchronizes with Speech (Purple), Thinking (Amber), Listening (Blue), and Idle (Cyan).
            </div>
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              <button
                type="button"
                onClick={() => fetch('http://127.0.0.1:8000/api/hardware/led-state', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ state: 'SPEAKING', amplitude: 0.8 }) }).catch(() => {})}
                style={{ padding: '4px 10px', fontSize: '11px', borderRadius: '6px', background: '#a855f7', color: '#fff', border: 'none', cursor: 'pointer' }}
              >
                Test Purple (Speaking)
              </button>
              <button
                type="button"
                onClick={() => fetch('http://127.0.0.1:8000/api/hardware/led-state', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ state: 'THINKING' }) }).catch(() => {})}
                style={{ padding: '4px 10px', fontSize: '11px', borderRadius: '6px', background: '#f59e0b', color: '#fff', border: 'none', cursor: 'pointer' }}
              >
                Test Amber (Thinking)
              </button>
              <button
                type="button"
                onClick={() => fetch('http://127.0.0.1:8000/api/hardware/led-state', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ state: 'LISTENING' }) }).catch(() => {})}
                style={{ padding: '4px 10px', fontSize: '11px', borderRadius: '6px', background: '#0284c7', color: '#fff', border: 'none', cursor: 'pointer' }}
              >
                Test Blue (Listening)
              </button>
              <button
                type="button"
                onClick={() => fetch('http://127.0.0.1:8000/api/hardware/led-state', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ state: 'IDLE' }) }).catch(() => {})}
                style={{ padding: '4px 10px', fontSize: '11px', borderRadius: '6px', background: '#06b6d4', color: '#fff', border: 'none', cursor: 'pointer' }}
              >
                Test Cyan (Idle)
              </button>
            </div>
          </div>
        </div>

        {/* Audio Input Device (Microphone) Selector & Live Test */}
        <div style={{
          padding: '16px',
          borderRadius: '12px',
          background: 'rgba(15, 23, 42, 0.75)',
          border: '1px solid rgba(0, 240, 255, 0.25)',
          marginBottom: '20px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', fontWeight: 700, color: '#00f0ff' }}>
              <Mic size={17} />
              Audio Input Microphone
            </div>
            {onRefreshDevices && (
              <button
                type="button"
                onClick={onRefreshDevices}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontSize: '11px',
                  color: '#94a3b8',
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '6px',
                  padding: '3px 8px',
                  cursor: 'pointer'
                }}
                title="Refresh detected audio devices"
              >
                <RefreshCw size={12} />
                Refresh List
              </button>
            )}
          </div>

          <div style={{ fontSize: '12px', color: '#cbd5e1', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span>Active:</span>
            <span style={{
              color: '#38bdf8',
              fontWeight: 600,
              background: 'rgba(56, 189, 248, 0.1)',
              padding: '2px 8px',
              borderRadius: '6px',
              border: '1px solid rgba(56, 189, 248, 0.2)'
            }}>
              {activeMicLabel || 'Default Microphone'}
            </span>
          </div>

          <select
            value={selectedInputDeviceId || 'default'}
            onChange={(e) => {
              if (onSelectInputDevice) {
                onSelectInputDevice(e.target.value);
              }
            }}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: '8px',
              background: 'rgba(15, 23, 42, 0.9)',
              border: '1px solid rgba(0, 240, 255, 0.35)',
              color: '#f8fafc',
              fontSize: '13px',
              outline: 'none',
              cursor: 'pointer',
              marginBottom: '10px'
            }}
          >
            <option value="default">Default System Microphone</option>
            {audioInputDevices && audioInputDevices.map((dev, idx) => (
              <option key={dev.deviceId || idx} value={dev.deviceId}>
                {dev.label || `Microphone ${idx + 1} (${dev.deviceId.slice(0, 8)}...)`}
              </option>
            ))}
          </select>

          {/* Live Mic Test Meter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '6px' }}>
            <button
              type="button"
              onClick={isTestingMic ? stopMicTest : startMicTest}
              style={{
                padding: '6px 14px',
                fontSize: '12px',
                fontWeight: 600,
                borderRadius: '8px',
                background: isTestingMic ? '#ef4444' : 'rgba(0, 240, 255, 0.15)',
                color: isTestingMic ? '#ffffff' : '#00f0ff',
                border: isTestingMic ? '1px solid #f87171' : '1px solid rgba(0, 240, 255, 0.4)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <Radio size={14} />
              {isTestingMic ? 'Stop Test' : 'Test Microphone'}
            </button>

            {isTestingMic && (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{
                  flex: 1,
                  height: '10px',
                  background: 'rgba(15, 23, 42, 0.8)',
                  borderRadius: '5px',
                  overflow: 'hidden',
                  border: '1px solid rgba(255, 255, 255, 0.1)'
                }}>
                  <div style={{
                    width: `${micVolume}%`,
                    height: '100%',
                    background: micVolume > 60 ? '#ef4444' : micVolume > 25 ? '#34d399' : '#00f0ff',
                    transition: 'width 0.05s ease'
                  }} />
                </div>
                <span style={{ fontSize: '11px', color: '#94a3b8', minWidth: '32px' }}>{micVolume}%</span>
              </div>
            )}
          </div>
        </div>

        {/* Audio Output Destination (Robot Speaker vs Laptop) */}
        <div style={{
          padding: '16px',
          borderRadius: '12px',
          background: 'rgba(15, 23, 42, 0.75)',
          border: '1px solid rgba(168, 85, 247, 0.3)',
          marginBottom: '20px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', fontWeight: 700, color: '#c084fc' }}>
              <Volume2 size={17} />
              Speaker Audio Output Destination
            </div>
            <button
              type="button"
              onClick={() => fetch('http://127.0.0.1:8000/api/hardware/chime', { method: 'POST' }).catch(() => {})}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '11px',
                color: '#c084fc',
                background: 'rgba(168, 85, 247, 0.15)',
                border: '1px solid rgba(168, 85, 247, 0.35)',
                borderRadius: '6px',
                padding: '4px 10px',
                cursor: 'pointer'
              }}
              title="Plays test chime on robot MAX98357A speaker"
            >
              🔔 Test Robot Speaker
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
            <button
              type="button"
              onClick={() => onSelectOutputTarget && onSelectOutputTarget('robot')}
              style={{
                padding: '10px 8px',
                borderRadius: '8px',
                border: audioOutputTarget === 'robot' ? '1px solid #c084fc' : '1px solid rgba(255, 255, 255, 0.08)',
                background: audioOutputTarget === 'robot' ? 'rgba(168, 85, 247, 0.25)' : 'rgba(15, 23, 42, 0.6)',
                color: audioOutputTarget === 'robot' ? '#f8fafc' : '#94a3b8',
                fontWeight: audioOutputTarget === 'robot' ? 700 : 500,
                fontSize: '12px',
                cursor: 'pointer',
                textAlign: 'center'
              }}
            >
              🤖 Robot Speaker<br />
              <span style={{ fontSize: '10px', color: audioOutputTarget === 'robot' ? '#38bdf8' : '#64748b' }}>
                (MAX98357A via Wi-Fi)
              </span>
            </button>

            <button
              type="button"
              onClick={() => onSelectOutputTarget && onSelectOutputTarget('laptop')}
              style={{
                padding: '10px 8px',
                borderRadius: '8px',
                border: audioOutputTarget === 'laptop' ? '1px solid #38bdf8' : '1px solid rgba(255, 255, 255, 0.08)',
                background: audioOutputTarget === 'laptop' ? 'rgba(56, 189, 248, 0.2)' : 'rgba(15, 23, 42, 0.6)',
                color: audioOutputTarget === 'laptop' ? '#f8fafc' : '#94a3b8',
                fontWeight: audioOutputTarget === 'laptop' ? 700 : 500,
                fontSize: '12px',
                cursor: 'pointer',
                textAlign: 'center'
              }}
            >
              💻 Laptop Speakers<br />
              <span style={{ fontSize: '10px', color: audioOutputTarget === 'laptop' ? '#38bdf8' : '#64748b' }}>
                (Browser Sound)
              </span>
            </button>

            <button
              type="button"
              onClick={() => onSelectOutputTarget && onSelectOutputTarget('both')}
              style={{
                padding: '10px 8px',
                borderRadius: '8px',
                border: audioOutputTarget === 'both' ? '1px solid #34d399' : '1px solid rgba(255, 255, 255, 0.08)',
                background: audioOutputTarget === 'both' ? 'rgba(52, 211, 153, 0.2)' : 'rgba(15, 23, 42, 0.6)',
                color: audioOutputTarget === 'both' ? '#f8fafc' : '#94a3b8',
                fontWeight: audioOutputTarget === 'both' ? 700 : 500,
                fontSize: '12px',
                cursor: 'pointer',
                textAlign: 'center'
              }}
            >
              🔊 Both (Sync)<br />
              <span style={{ fontSize: '10px', color: audioOutputTarget === 'both' ? '#34d399' : '#64748b' }}>
                (Robot + Laptop)
              </span>
            </button>
          </div>
          <div style={{ fontSize: '11px', color: '#64748b', marginTop: '8px' }}>
            {audioOutputTarget === 'robot'
              ? '✅ Robot Speaker active. Laptop browser audio is silenced so speech comes exclusively from the robot mouth.'
              : audioOutputTarget === 'laptop'
              ? 'Laptop speakers active. Audio plays through PC default sound device.'
              : 'Both active. Audio plays from both PC and Robot speaker simultaneously.'}
          </div>
        </div>

        {/* Configuration Overview */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ fontSize: '12px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>
              AI Model Family & Name
            </label>
            <input
              type="text"
              readOnly
              value={config?.model_name || 'qwen3:8b'}
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '8px',
                background: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#f8fafc',
                marginTop: '4px',
                fontSize: '13px'
              }}
            />
            <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>
              Configured via environment variable <code>OLLAMA_MODEL</code>.
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '12px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>
                STT Language
              </label>
              <input
                type="text"
                readOnly
                value={config?.stt_language || 'en'}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  background: 'rgba(15, 23, 42, 0.8)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  color: '#f8fafc',
                  marginTop: '4px',
                  fontSize: '13px'
                }}
              />
            </div>
            <div>
              <label style={{ fontSize: '12px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>
                STT Model Size
              </label>
              <input
                type="text"
                readOnly
                value={config?.stt_model || 'base'}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  background: 'rgba(15, 23, 42, 0.8)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  color: '#f8fafc',
                  marginTop: '4px',
                  fontSize: '13px'
                }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
              padding: '12px',
              borderRadius: '10px',
              background: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid rgba(255, 255, 255, 0.08)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Volume2 size={16} color="#38bdf8" /> Voice Synthesis
                </span>
                <span style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  color: config?.tts_enabled ? '#34d399' : '#f87171',
                  padding: '2px 8px',
                  borderRadius: '6px',
                  background: config?.tts_enabled ? 'rgba(52, 211, 153, 0.1)' : 'rgba(248, 113, 113, 0.1)'
                }}>
                  {config?.tts_enabled ? 'FISH AUDIO' : 'DISABLED'}
                </span>
              </div>
              <span style={{ fontSize: '11px', color: '#94a3b8' }}>S2 Pro (Q5_K_M GGUF)</span>
            </div>

            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px',
              borderRadius: '10px',
              background: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid rgba(255, 255, 255, 0.08)'
            }}>
              <span style={{ fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Globe size={16} color="#a855f7" /> Web Search
              </span>
              <span style={{
                fontSize: '11px',
                fontWeight: 600,
                color: config?.web_search_enabled ? '#34d399' : '#94a3b8',
                padding: '2px 8px',
                borderRadius: '6px',
                background: config?.web_search_enabled ? 'rgba(52, 211, 153, 0.1)' : 'rgba(148, 163, 184, 0.1)'
              }}>
                {config?.web_search_enabled ? 'ENABLED' : 'DISABLED'}
              </span>
            </div>
          </div>
        </div>

        <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'flex-end' }}>
          <button onClick={onClose} className="btn-primary" style={{ padding: '8px 20px', fontSize: '13px' }}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
