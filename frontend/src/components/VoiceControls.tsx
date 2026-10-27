import React, { useRef } from 'react';
import { Mic, Volume2, VolumeX, Square } from 'lucide-react';

interface VoiceControlsProps {
  isRecording: boolean;
  isSpeaking: boolean;
  isMuted: boolean;
  onStartRecord: () => void;
  onStopRecord: () => void;
  onStopSpeaking: () => void;
  onToggleMute: () => void;
  activeMicLabel?: string;
  onOpenSettings?: () => void;
  audioOutputTarget?: 'robot' | 'laptop' | 'both';
  onSelectOutputTarget?: (target: 'robot' | 'laptop' | 'both') => void;
}

export const VoiceControls: React.FC<VoiceControlsProps> = ({
  isRecording,
  isSpeaking,
  isMuted,
  onStartRecord,
  onStopRecord,
  onStopSpeaking,
  onToggleMute,
  activeMicLabel,
  onOpenSettings,
  audioOutputTarget = 'both',
  onSelectOutputTarget
}) => {
  const pointerDownTimeRef = useRef<number>(0);
  const isHoldModeRef = useRef<boolean>(false);

  // Pointer Down: start timer for hold-to-talk
  const handlePointerDown = () => {
    pointerDownTimeRef.current = Date.now();
    isHoldModeRef.current = false;
    if (!isRecording) {
      onStartRecord();
    }
  };

  // Pointer Up: if held longer than 350ms, release automatically stops recording
  const handlePointerUp = () => {
    const elapsed = Date.now() - pointerDownTimeRef.current;
    if (elapsed > 350 && isRecording) {
      isHoldModeRef.current = true;
      onStopRecord();
    }
  };

  // Click handler for toggle mode (when tapped quickly)
  const handleClick = () => {
    if (isHoldModeRef.current) {
      isHoldModeRef.current = false;
      return;
    }
    if (isRecording) {
      onStopRecord();
    }
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '8px',
      margin: '6px 0 10px 0'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '14px'
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
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: isMuted ? '#f87171' : '#38bdf8',
            borderColor: isMuted ? 'rgba(239, 68, 68, 0.5)' : 'rgba(56, 189, 248, 0.3)',
            background: isMuted ? 'rgba(239, 68, 68, 0.15)' : 'rgba(15, 23, 42, 0.7)'
          }}
          title={isMuted ? "Unmute Voice (Sound is currently silenced)" : "Mute Assistant Voice"}
        >
          {isMuted ? <VolumeX size={18} /> : <Volume2 size={18} />}
        </button>

        {/* Main Microphone Button: Supports Click-to-Toggle and Hold-to-Talk */}
        {isRecording ? (
          <button
            onClick={handleClick}
            onPointerUp={handlePointerUp}
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
              transition: 'all 0.2s ease',
              userSelect: 'none',
              touchAction: 'none'
            }}
            title="Recording active! Click or release to stop and transcribe"
          >
            <Square size={24} fill="#ffffff" />
          </button>
        ) : (
          <button
            onPointerDown={handlePointerDown}
            onPointerUp={handlePointerUp}
            onClick={handleClick}
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
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              userSelect: 'none',
              touchAction: 'none'
            }}
            title="Push to Talk: Hold to speak, or click once to record"
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
              borderColor: 'rgba(251, 191, 36, 0.4)',
              background: 'rgba(251, 191, 36, 0.15)'
            }}
            title="Interrupt / Stop Speaking"
          >
            <Square size={14} fill="#fbbf24" />
            <span style={{ fontSize: '13px', fontWeight: 600 }}>Stop Voice</span>
          </button>
        )}
      </div>

      {/* Mic & Speaker Status Pills */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '8px',
        flexWrap: 'wrap'
      }}>
        {/* Active Microphone Pill */}
        {activeMicLabel && (
          <div
            onClick={onOpenSettings}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '11px',
              color: '#94a3b8',
              cursor: onOpenSettings ? 'pointer' : 'default',
              padding: '4px 10px',
              borderRadius: '12px',
              background: 'rgba(15, 23, 42, 0.75)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              maxWidth: '240px',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              transition: 'all 0.2s ease',
              userSelect: 'none'
            }}
            title={`Active Microphone: ${activeMicLabel}\nClick to change in Settings`}
          >
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981', display: 'inline-block', flexShrink: 0 }} />
            <span style={{ color: '#cbd5e1', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis' }}>
              Mic: {activeMicLabel}
            </span>
          </div>
        )}

        {/* Speaker Destination Quick Selector */}
        {onSelectOutputTarget && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            background: 'rgba(15, 23, 42, 0.75)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '12px',
            padding: '2px 4px'
          }}>
            <button
              type="button"
              onClick={() => onSelectOutputTarget('both')}
              style={{
                fontSize: '11px',
                padding: '2px 8px',
                borderRadius: '8px',
                border: 'none',
                cursor: 'pointer',
                background: audioOutputTarget === 'both' ? 'rgba(52, 211, 153, 0.25)' : 'transparent',
                color: audioOutputTarget === 'both' ? '#34d399' : '#94a3b8',
                fontWeight: audioOutputTarget === 'both' ? 600 : 400
              }}
              title="Both (Laptop + Robot Speaker in sync)"
            >
              🔊 Both
            </button>
            <button
              type="button"
              onClick={() => onSelectOutputTarget('laptop')}
              style={{
                fontSize: '11px',
                padding: '2px 8px',
                borderRadius: '8px',
                border: 'none',
                cursor: 'pointer',
                background: audioOutputTarget === 'laptop' ? 'rgba(56, 189, 248, 0.25)' : 'transparent',
                color: audioOutputTarget === 'laptop' ? '#38bdf8' : '#94a3b8',
                fontWeight: audioOutputTarget === 'laptop' ? 600 : 400
              }}
              title="Laptop/PC Speakers Only"
            >
              💻 Laptop
            </button>
            <button
              type="button"
              onClick={() => onSelectOutputTarget('robot')}
              style={{
                fontSize: '11px',
                padding: '2px 8px',
                borderRadius: '8px',
                border: 'none',
                cursor: 'pointer',
                background: audioOutputTarget === 'robot' ? 'rgba(168, 85, 247, 0.25)' : 'transparent',
                color: audioOutputTarget === 'robot' ? '#c084fc' : '#94a3b8',
                fontWeight: audioOutputTarget === 'robot' ? 600 : 400
              }}
              title="Robot Hardware Speaker Only (MAX98357A via Wi-Fi)"
            >
              🤖 Robot
            </button>
          </div>
        )}
      </div>

      {isMuted && (
        <div style={{
          fontSize: '11px',
          color: '#f87171',
          background: 'rgba(239, 68, 68, 0.15)',
          padding: '2px 10px',
          borderRadius: '8px',
          border: '1px solid rgba(239, 68, 68, 0.3)'
        }}>
          ⚠️ Voice output is currently muted. Click the speaker icon to unmute.
        </div>
      )}
    </div>
  );
};
