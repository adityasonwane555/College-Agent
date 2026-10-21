import React, { useState, useEffect } from 'react';
import type { RobotState } from '../types';

interface RobotEyesProps {
  state: RobotState;
}

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
