/**
 * BUDDY AI 2.0 — Listening Waveform Visualizer Component
 *
 * Architecture & Visual Feedback:
 *   - CSS-Animated Frequency Spectrum:
 *       - Renders a 7-bar rhythmic audio waveform to visually signal active microphone listening states to users.
 *   - Hardware LED Symmetry:
 *       - Parallels the cyan/blue undulating breath pattern emitted by the ESP32-S3 onboard WS2812 RGB LED ring.
 *   - Lightweight DOM Implementation:
 *       - Uses pure CSS keyframe height animations without requiring continuous Web Audio API FFT computations.
 */

import React from 'react';

interface ListeningWaveformProps {
  barCount?: number;
  isActive?: boolean;
  className?: string;
}

/**
 * Produces an accessible ARIA label for screen readers.
 */
export const getWaveformAriaLabel = (isActive: boolean): string => {
  return isActive ? 'Microphone audio listening visualizer active' : 'Audio visualizer idle';
};

/**
 * Animated waveform bars indicating active speech recording and voice detection.
 */
export const ListeningWaveform: React.FC<ListeningWaveformProps> = ({
  barCount = 7,
  isActive = true,
  className = ''
}) => {
  const bars = Array.from({ length: barCount }, (_, i) => i);

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={getWaveformAriaLabel(isActive)}
      className={`waveform-bars ${className}`.trim()}
    >
      {bars.map((barIndex) => (
        <div key={barIndex} className="waveform-bar" />
      ))}
    </div>
  );
};

