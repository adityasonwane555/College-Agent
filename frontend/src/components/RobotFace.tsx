import React from 'react';
import type { RobotState } from '../types';
import { RobotEyes } from './RobotEyes';
import { RobotMouth } from './RobotMouth';
import { ListeningWaveform } from './ListeningWaveform';

interface RobotFaceProps {
  state: RobotState;
}

export const RobotFace: React.FC<RobotFaceProps> = ({ state }) => {
  return (
    <div className="robot-stage">
      <div className={`robot-head-wrapper ${state}`}>
        {/* Thinking Halo Ring */}
        {state === 'thinking' && <div className="thinking-halo" />}

        {/* Left Antenna Ear */}
        <div className="robot-antenna left">
          <div className="robot-antenna-tip" />
        </div>

        {/* Outer Helmet */}
        <div className={`robot-helmet ${state}`}>
          {/* Dark Glass Visor Screen */}
          <div className="robot-visor">
            {/* Eyes */}
            <RobotEyes state={state} />

            {/* Cheeks */}
            <div className="robot-cheeks-row">
              <div className="robot-cheek" />
              <div className="robot-cheek" />
            </div>

            {/* Mouth or Waveform */}
            {state === 'listening' ? (
              <div style={{ marginTop: '20px' }}>
                <ListeningWaveform />
              </div>
            ) : (
              <RobotMouth state={state} />
            )}
          </div>
        </div>

        {/* Right Antenna Ear */}
        <div className="robot-antenna right">
          <div className="robot-antenna-tip" />
        </div>
      </div>
    </div>
  );
};
