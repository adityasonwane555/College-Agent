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
 * RobotMouth renders an animated mouth element that responds visually to conversational states.
 */
export const RobotMouth: React.FC<RobotMouthProps> = ({ state }) => {
  return (
    <div className="robot-mouth-container">
      <div className={`robot-mouth-line state-${state}`} />
    </div>
  );
};
