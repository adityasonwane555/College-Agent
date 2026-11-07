/**
 * BUDDY AI — Robot Face Visual Stage Component
 *
 * Visual & Animation Architecture:
 *   - Twin-Display Synchrony:
 *       Serves as the high-resolution browser kiosk counterpart to the physical ESP32-S3
 *       ST7789 240x240 LCD screen, sharing identical state-driven color schemes and expressions.
 *   - Component Layout & Layers:
 *       1. Outer Helmet & Antenna Ears: Glossy robotic housing with state-reactive LED glow.
 *       2. Thinking Halo: Celestial orbiting particle ring activated exclusively during `thinking` state.
 *       3. Dark Glass Visor Screen: High-contrast OLED/LCD simulation layer housing facial features.
 *       4. Parametric Eyes (`RobotEyes`): Natural sinusoids, specular glints, pupil saccades, and blinking.
 *       5. Soft Glowing Cheeks: Continuous ambient presence glowing warm cyan/peach.
 *       6. Audio-Reactive Mouth (`RobotMouth` vs `ListeningWaveform`): Dynamically switches
 *          to a real-time audio visualizer during `listening` or expressive speech phonemes during `speaking`.
 */

import React from 'react';
import type { RobotState } from '../types';
import { RobotEyes } from './RobotEyes';
import { RobotMouth } from './RobotMouth';
import { ListeningWaveform } from './ListeningWaveform';

interface RobotFaceProps {
  /** Current operating state of the robot (idle, listening, thinking, speaking, error). */
  state: RobotState;
}

/**
 * Renders the interactive robot face stage for the browser reception kiosk.
 * Coordinates state-driven CSS classes for animations, halo effects, and audio-reactive waveforms.
 */
export const RobotFace: React.FC<RobotFaceProps> = ({ state }) => {
  return (
    <div className="robot-stage">
      <div className={`robot-head-wrapper ${state}`}>
        {/* Thinking Halo Ring: Orbiting particle ring rendered during AI reasoning */}
        {state === 'thinking' && <div className="thinking-halo" />}

        {/* Left Antenna Ear: Ambient lateral status node */}
        <div className="robot-antenna left">
          <div className="robot-antenna-tip" />
        </div>

        {/* Outer Helmet: Ergonomic rounded cybernetic frame */}
        <div className={`robot-helmet ${state}`}>
          {/* Dark Glass Visor Screen: Emulates physical ST7789 240x240 LCD screen */}
          <div className="robot-visor">
            {/* Eyes: Dynamic blinking, saccades, and parametric shape morphing */}
            <RobotEyes state={state} />

            {/* Cheeks: Ambient warm glow row */}
            <div className="robot-cheeks-row">
              <div className="robot-cheek" />
              <div className="robot-cheek" />
            </div>

            {/* Mouth or Waveform: Switches between animated lip-sync and live mic waveform */}
            {state === 'listening' ? (
              <div style={{ marginTop: '20px' }}>
                <ListeningWaveform />
              </div>
            ) : (
              <RobotMouth state={state} />
            )}
          </div>
        </div>

        {/* Right Antenna Ear: Ambient lateral status node */}
        <div className="robot-antenna right">
          <div className="robot-antenna-tip" />
        </div>
      </div>
    </div>
  );
};
