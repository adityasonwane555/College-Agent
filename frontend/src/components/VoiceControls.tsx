import React from 'react';
import { Mic, Volume2, VolumeX, Square } from 'lucide-react';

interface VoiceControlsProps {
  isRecording: boolean;
  isSpeaking: boolean;
  isMuted: boolean;
  onStartRecord: () => void;
  onStopRecord: () => void;
  onStopSpeaking: () => void;
  onToggleMute: () => void;
}

export const VoiceControls: React.FC<VoiceControlsProps> = ({
  isRecording,
  isSpeaking,
  isMuted,
  onStartRecord,
  onStopRecord,
  onStopSpeaking,
  onToggleMute
}) => {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '16px',
      margin: '12px 0'
    }}>
      {/* Mute / Unmute Toggle */}
      <button
        onClick={onToggleMute}
        className="btn-secondary"
        style={{
          width: '44px',
          height: '44px',
          borderRadius: '50%',
          padding: 0,
          color: isMuted ? '#f87171' : '#38bdf8'
        }}
        title={isMuted ? "Unmute Voice" : "Mute Voice"}
      >
        {isMuted ? <VolumeX size={18} /> : <Volume2 size={18} />}
      </button>

      {/* Main Microphone Button */}
      {isRecording ? (
        <button
          onClick={onStopRecord}
          style={{
            width: '68px',
            height: '68px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
            border: '2px solid #fecaca',
            color: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            boxShadow: '0 0 25px rgba(239, 68, 68, 0.6)',
            animation: 'pulse 1s infinite alternate',
            transition: 'all 0.2s ease'
          }}
          title="Stop Recording"
        >
          <Square size={24} fill="#ffffff" />
        </button>
      ) : (
        <button
          onClick={onStartRecord}
          style={{
            width: '68px',
            height: '68px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #0284c7 0%, #00f0ff 100%)',
            border: '2px solid rgba(255, 255, 255, 0.4)',
            color: '#04101e',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            boxShadow: '0 0 30px rgba(0, 240, 255, 0.4)',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
          }}
          title="Push to Talk (or Click to Record)"
        >
          <Mic size={28} />
        </button>
      )}

      {/* Stop Speaking Interruption Button */}
      {isSpeaking && (
        <button
          onClick={onStopSpeaking}
          className="btn-secondary"
          style={{
            height: '44px',
            borderRadius: '22px',
            padding: '0 16px',
            color: '#fbbf24',
            borderColor: 'rgba(251, 191, 36, 0.4)'
          }}
          title="Interrupt / Stop Speaking"
        >
          <Square size={14} fill="#fbbf24" />
          <span style={{ fontSize: '13px', fontWeight: 600 }}>Stop Voice</span>
        </button>
      )}
    </div>
  );
};
