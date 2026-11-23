import React from 'react';
import './BiToolLogo.css';

export const BiToolLogo = ({ size = 36, color = '#09090b', className = '' }) => {
  return (
    <div
      className={`bi-logo-container ${className}`}
      style={{
        width: size,
        height: size,
        '--logo-color': color,
      }}
      title="बी - TOOL"
      aria-label="बी - TOOL Animated Logo"
    >
      <svg
        viewBox="0 0 100 100"
        fill="currentColor"
        xmlns="http://www.w3.org/2000/svg"
        className="bi-logo-svg"
      >
        {/* 5 Animated Soundwave / Equalizer Bars */}
        <rect className="bar bar-1" x="17" y="34" width="10" height="26" rx="5" />
        <rect className="bar bar-2" x="31" y="22" width="10" height="50" rx="5" />
        <rect className="bar bar-3" x="45" y="10" width="10" height="74" rx="5" />
        <rect className="bar bar-4" x="59" y="22" width="10" height="50" rx="5" />
        <rect className="bar bar-5" x="73" y="34" width="10" height="26" rx="5" />
      </svg>
    </div>
  );
};

export default BiToolLogo;

