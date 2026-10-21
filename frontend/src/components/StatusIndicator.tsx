import React from 'react';
import type { RobotState } from '../types';

interface StatusIndicatorProps {
  state: RobotState;
  customMessage?: string;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({ state, customMessage }) => {
  const getDefaultMessage = () => {
    switch (state) {
      case 'listening':
        return "I'm listening... Speak into your microphone";
      case 'thinking':
        return "Let me check the college records...";
      case 'speaking':
        return "Buddy is speaking...";
      case 'happy':
        return "Glad I could help you! Anything else?";
      case 'error':
        return "I encountered an issue. Please try again.";
      case 'idle':
      default:
        return "Hi! I'm Buddy. Ask me about departments, faculty, rooms, or events!";
    }
  };

  const getBadgeStyle = () => {
    switch (state) {
      case 'listening':
        return { bg: 'rgba(0, 240, 255, 0.15)', text: '#00f0ff', border: 'rgba(0, 240, 255, 0.4)' };
      case 'thinking':
        return { bg: 'rgba(168, 85, 247, 0.15)', text: '#c084fc', border: 'rgba(168, 85, 247, 0.4)' };
      case 'speaking':
        return { bg: 'rgba(56, 189, 248, 0.15)', text: '#38bdf8', border: 'rgba(56, 189, 248, 0.4)' };
      case 'happy':
        return { bg: 'rgba(16, 185, 129, 0.15)', text: '#34d399', border: 'rgba(16, 185, 129, 0.4)' };
      case 'error':
        return { bg: 'rgba(244, 63, 94, 0.15)', text: '#f87171', border: 'rgba(244, 63, 94, 0.4)' };
      default:
        return { bg: 'rgba(255, 255, 255, 0.05)', text: '#94a3b8', border: 'rgba(255, 255, 255, 0.1)' };
    }
  };

  const badge = getBadgeStyle();

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '8px',
      margin: '12px 0 16px 0',
      textAlign: 'center'
    }}>
      <div style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding: '4px 12px',
        borderRadius: '20px',
        background: badge.bg,
        border: `1px solid ${badge.border}`,
        color: badge.text,
        fontSize: '11px',
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.08em'
      }}>
        <span style={{
          width: '7px',
          height: '7px',
          borderRadius: '50%',
          backgroundColor: badge.text,
          boxShadow: `0 0 8px ${badge.text}`
        }} />
        {state}
      </div>

      <div style={{
        fontSize: '17px',
        fontWeight: 500,
        color: '#f1f5f9',
        maxWidth: '550px',
        lineHeight: 1.4
      }}>
        {customMessage || getDefaultMessage()}
      </div>
    </div>
  );
};
