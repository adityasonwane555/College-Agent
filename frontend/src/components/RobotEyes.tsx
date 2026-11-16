/**
 * BUDDY AI 2.0 — Procedural Robot Eyes & Blink State Machine Component
 *
 * Architecture & Facial Animation:
 *   - Autonomous Natural Blinking:
 *       - Schedules randomized eyelid closure intervals between 2.5s and 6.0s with an authentic 180ms blink duration.
 *   - Emotion & State Styling:
 *       - Applies dynamic CSS classes (`eye-state-${state}`) altering pupil dilation, eye shape, and glow intensity:
 *         * 'listening' -> Widened alert pupils with cyan specular highlights.
 *         * 'thinking'  -> Upward saccadic gaze drift simulating cognitive reasoning.
 *         * 'speaking'  -> Expressive vertical expansion synchronized with mouth movement.
 *         * 'happy'     -> Crescent-shaped upward arcs.
 *         * 'error'     -> Cross or furrowed brow shapes.
 *   - Twin-Display Parity:
 *       - Visual counterpart to the 240x240 pixel ST7789 SPI TFT display mounted on the physical robot head.
 */

import React, { useState, useEffect } from 'react';
import type { RobotState } from '../types';

interface RobotEyesProps {
  state: RobotState;
}

/**
 * Procedurally animated robot eyes with autonomous stochastic blinking and emotional states.
 */
export const RobotEyes: React.FC<RobotEyesProps> = ({ state }) => {
  const [isBlinking, setIsBlinking] = useState(false);

  // Periodic natural blinking
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    const scheduleBlink = () => {
      const delay = Math.random() * 3500 + 2500; // blink every 2.5 - 6.0 seconds
      timer = setTimeout(() => {
        setIsBlinking(true);
        setTimeout(() => {
          setIsBlinking(false);
          scheduleBlink();
        }, 180);
      }, delay);
    };

    scheduleBlink();
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className={`robot-eyes-row eye-state-${state}`}>
      {/* Left Eye */}
      <div className={`robot-eye ${isBlinking ? 'blinking' : ''}`}>
        <div className="robot-eye-pupil" />
      </div>

      {/* Right Eye */}
      <div className={`robot-eye ${isBlinking ? 'blinking' : ''}`}>
        <div className="robot-eye-pupil" />
      </div>
    </div>
  );
};
