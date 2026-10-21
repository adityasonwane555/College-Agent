import React from 'react';
import type { RobotState } from '../types';

interface RobotMouthProps {
  state: RobotState;
}

export const RobotMouth: React.FC<RobotMouthProps> = ({ state }) => {
  return (
    <div className="robot-mouth-container">
      <div className={`robot-mouth-line state-${state}`} />
    </div>
  );
};
