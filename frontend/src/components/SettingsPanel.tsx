import React from 'react';
import type { AppConfig, HealthStatus } from '../types';
import { X, Cpu, Mic, Volume2, Globe, Server, CheckCircle2, AlertTriangle } from 'lucide-react';

interface SettingsPanelProps {
  config: AppConfig | null;
  health: HealthStatus | null;
  onClose: () => void;
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({ config, health, onClose }) => {
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
