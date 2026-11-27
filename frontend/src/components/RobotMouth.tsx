/**
 * BUDDY AI 2.0 — Robot Mouth Component
 *
 * Architecture & UI Design:
 *   - Conversational Mouth Modulation:
 *       - Renders procedural CSS animated mouth lines matching active robot states.
 *       - Scales and oscillates during 'speaking' mode in synchrony with speech synthesis.
 *   - Emotional State Classes:
 *       - Maps 'idle', 'listening', 'thinking', 'speaking', 'happy', and 'error' to specialized CSS waveforms.
 */

import React from 'react';
import type { RobotState } from '../types';

/**
 * Properties for the RobotMouth component.
 */
interface RobotMouthProps {
  /** Active high-level operational state of the reception robot. */
  state: RobotState;
}

/**
 * Returns an accessible screen reader description for the active mouth animation.
 */
export const getMouthAriaLabel = (state: RobotState): string => {
  switch (state) {
    case 'speaking':
      return 'Robot mouth animated synchronously with active speech';
    case 'happy':
      return 'Robot mouth smiling happily';
    case 'listening':
      return 'Robot mouth resting attentively in listening mode';
    case 'thinking':
      return 'Robot mouth in subtle contemplation';
    case 'error':
      return 'Robot mouth in alert diagnostic posture';
    case 'idle':
    default:
      return 'Robot mouth in calm neutral resting position';
  }
};

/**
 * Determines whether the mouth element is in active vocal modulation.
 */
export const isMouthSpeaking = (state: RobotState): boolean => {
  return state === 'speaking';
};

/**
 * RobotMouth renders an animated mouth element that responds visually to conversational states.
 */
export const RobotMouth: React.FC<RobotMouthProps> = ({ state }) => {
  return (
    <div
      role="presentation"
      aria-label={getMouthAriaLabel(state)}
      className="robot-mouth-container"
    >
      <div className={`robot-mouth-line state-${state}`} />
    </div>
  );
};

