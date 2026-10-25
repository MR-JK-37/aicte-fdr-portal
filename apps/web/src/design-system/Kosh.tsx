import React, { useId } from 'react';

export type KoshPose =
  | 'smile'
  | 'wow'
  | 'calm'
  | 'peek'
  | 'search'
  | 'document'
  | 'lock'
  | 'offline'
  | 'error'
  | 'celebrate';

export interface KoshProps {
  size?: number;
  pose?: KoshPose;
  peek?: boolean;
  avatarIndex?: number;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * Kosh Mascot — Original soft-3D shield-coin character (DESIGN_SPEC §8).
 * Cobalt shield-coin body with white rounded face plate, small dot eyes, and subtle mouth/accessories.
 */
export const Kosh: React.FC<KoshProps> = ({
  size = 110,
  pose = 'smile',
  peek = false,
  avatarIndex,
  className,
  style,
}) => {
  const uid = useId().replace(/:/g, '');

  // If avatarIndex is provided (0..11), map to combinations of moods and tints
  const effectivePose: KoshPose =
    avatarIndex !== undefined
      ? (['smile', 'wow', 'calm', 'celebrate'][avatarIndex % 4] as KoshPose)
      : pose;

  const isPeek = peek || effectivePose === 'peek';

  const mouthPath = {
    smile: 'M50 71q10 9 20 0',
    wow: 'M54 70q6 9 12 0q-6-5-12 0z',
    calm: 'M52 72h16',
    peek: 'M50 71q10 9 20 0',
    search: 'M52 71q8 6 16 0',
    document: 'M52 72h16',
    lock: 'M52 72h16',
    offline: 'M52 74q8 -5 16 0',
    error: 'M52 74q8 -6 16 0',
    celebrate: 'M48 68q12 14 24 0z',
  }[effectivePose] || 'M50 71q10 9 20 0';

  // Specific accessory overlays per pose
  let accessory = null;
  if (effectivePose === 'search') {
    accessory = (
      <g transform="translate(68, 62) scale(0.7)">
        <circle cx="11" cy="11" r="7" fill="none" stroke="#2d63cf" strokeWidth="2.5" />
        <line x1="16" y1="16" x2="22" y2="22" stroke="#2d63cf" strokeWidth="2.5" strokeLinecap="round" />
      </g>
    );
  } else if (effectivePose === 'document') {
    accessory = (
      <g transform="translate(68, 64) scale(0.65)">
        <rect x="2" y="2" width="16" height="20" rx="2" fill="#ffffff" stroke="#2d63cf" strokeWidth="2" />
        <line x1="6" y1="7" x2="14" y2="7" stroke="#3b78d8" strokeWidth="1.5" />
        <line x1="6" y1="11" x2="14" y2="11" stroke="#3b78d8" strokeWidth="1.5" />
      </g>
    );
  } else if (effectivePose === 'lock') {
    accessory = (
      <g transform="translate(70, 66) scale(0.6)">
        <rect x="4" y="9" width="16" height="13" rx="2" fill="#2d63cf" />
        <path d="M7 9V6a5 5 0 0110 0v3" fill="none" stroke="#2d63cf" strokeWidth="2.2" />
      </g>
    );
  } else if (effectivePose === 'celebrate') {
    accessory = (
      <g>
        <circle cx="24" cy="20" r="3" fill="#ffb7c2" />
        <circle cx="96" cy="24" r="3" fill="#ffb938" />
        <circle cx="18" cy="46" r="2.5" fill="#3b78d8" />
        <circle cx="102" cy="48" r="2.5" fill="#3ddc97" />
      </g>
    );
  }

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 120 120"
      aria-hidden="true"
      data-testid="kosh-svg"
      className={className}
      style={{ display: 'inline-block', flexShrink: 0, ...style }}
    >
      <defs>
        <linearGradient id={`b-${uid}`} x1=".1" y1="0" x2=".9" y2="1">
          <stop offset="0" stopColor="#8fb4ff" />
          <stop offset=".55" stopColor="#3b78d8" />
          <stop offset="1" stopColor="#2556b8" />
        </linearGradient>
        <radialGradient id={`h-${uid}`} cx=".3" cy=".2" r=".6">
          <stop offset="0" stopColor="#ffffff" stopOpacity=".75" />
          <stop offset="1" stopColor="#ffffff" stopOpacity="0" />
        </radialGradient>
        <linearGradient id={`f-${uid}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#ffffff" />
          <stop offset="1" stopColor="#e6edff" />
        </linearGradient>
      </defs>

      {/* Shadow */}
      <ellipse cx="60" cy="112" rx="32" ry="5" fill="#2556b8" opacity="0.16" />

      {/* Shield Body */}
      <path
        d="M60 8l41 15v32c0 30-18 47-41 55C37 102 19 85 19 55V23z"
        fill={`url(#b-${uid})`}
      />
      <path
        d="M60 8l41 15v32c0 30-18 47-41 55C37 102 19 85 19 55V23z"
        fill={`url(#h-${uid})`}
      />
      <path
        d="M60 8l41 15v32c0 30-18 47-41 55"
        fill="none"
        stroke="#1d47a0"
        strokeOpacity="0.25"
        strokeWidth="2"
      />

      {/* Face Plate */}
      <rect x="29" y="34" width="62" height="50" rx="22" fill={`url(#f-${uid})`} />

      {/* Eyes with highlights */}
      <ellipse cx="46" cy="55" rx="5.2" ry="6.6" fill="#16213f" />
      <ellipse cx="74" cy="55" rx="5.2" ry="6.6" fill="#16213f" />
      <circle cx="47.8" cy="52.6" r="1.9" fill="#ffffff" />
      <circle cx="75.8" cy="52.6" r="1.9" fill="#ffffff" />

      {/* Rosy cheeks */}
      <circle cx="37" cy="66" r="4.2" fill="#ffb7c2" opacity="0.55" />
      <circle cx="83" cy="66" r="4.2" fill="#ffb7c2" opacity="0.55" />

      {/* Mouth */}
      <path
        d={mouthPath}
        fill="none"
        stroke="#16213f"
        strokeWidth="3.2"
        strokeLinecap="round"
      />

      {/* Peeking hands */}
      {isPeek && (
        <g>
          <rect x="14" y="88" width="26" height="16" rx="8" fill="#2d63cf" />
          <rect x="80" y="88" width="26" height="16" rx="8" fill="#2d63cf" />
        </g>
      )}

      {/* Accessory overlay */}
      {accessory}

      {/* Top right sparkle */}
      <path
        d="M101 14l2.6 5.4 5.4 2.6-5.4 2.6L101 30l-2.6-5.4L93 22l5.4-2.6z"
        fill="#dbe6ff"
      />
    </svg>
  );
};
