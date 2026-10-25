import React, { useId } from 'react';
import Svg, {
  Defs,
  LinearGradient,
  RadialGradient,
  Stop,
  Path,
  Rect,
  Circle,
  Ellipse,
  Line,
  G,
} from 'react-native-svg';
import { View, StyleSheet, type ViewStyle } from 'react-native';

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
  style?: ViewStyle;
}

/**
 * Kosh Mascot (React Native / Mobile) — Original soft-3D shield-coin character (DESIGN_SPEC §8).
 * Cobalt shield-coin body with white rounded face plate, small dot eyes, and subtle mouth/accessories.
 */
export const Kosh: React.FC<KoshProps> = ({
  size = 110,
  pose = 'smile',
  peek = false,
  avatarIndex,
  style,
}) => {
  const rawId = useId();
  const uid = rawId ? rawId.replace(/[^a-zA-Z0-9]/g, '') : 'm';

  const effectivePose: KoshPose =
    avatarIndex !== undefined
      ? (['smile', 'wow', 'calm', 'celebrate'][avatarIndex % 4] as KoshPose)
      : pose;

  const isPeek = peek || effectivePose === 'peek';

  const mouthPath = {
    smile: 'M50 71 Q60 80 70 71',
    wow: 'M54 70 Q60 79 66 70 Q60 65 54 70 Z',
    calm: 'M52 72 L68 72',
    peek: 'M50 71 Q60 80 70 71',
    search: 'M52 71 Q60 77 68 71',
    document: 'M52 72 L68 72',
    lock: 'M52 72 L68 72',
    offline: 'M52 74 Q60 69 68 74',
    error: 'M52 74 Q60 68 68 74',
    celebrate: 'M48 68 Q60 82 72 68 Z',
  }[effectivePose] || 'M50 71 Q60 80 70 71';

  let accessory = null;
  if (effectivePose === 'search') {
    accessory = (
      <G transform="translate(68, 62) scale(0.7)">
        <Circle cx="11" cy="11" r="7" fill="none" stroke="#2d63cf" strokeWidth="2.5" />
        <Line x1="16" y1="16" x2="22" y2="22" stroke="#2d63cf" strokeWidth="2.5" strokeLinecap="round" />
      </G>
    );
  } else if (effectivePose === 'document') {
    accessory = (
      <G transform="translate(68, 64) scale(0.65)">
        <Rect x="2" y="2" width="16" height="20" rx="2" fill="#ffffff" stroke="#2d63cf" strokeWidth="2" />
        <Line x1="6" y1="7" x2="14" y2="7" stroke="#3b78d8" strokeWidth="1.5" />
        <Line x1="6" y1="11" x2="14" y2="11" stroke="#3b78d8" strokeWidth="1.5" />
      </G>
    );
  } else if (effectivePose === 'lock') {
    accessory = (
      <G transform="translate(70, 66) scale(0.6)">
        <Rect x="4" y="9" width="16" height="13" rx="2" fill="#2d63cf" />
        <Path d="M7 9 V6 A5 5 0 0 1 17 6 V9" fill="none" stroke="#2d63cf" strokeWidth="2.2" />
      </G>
    );
  } else if (effectivePose === 'celebrate') {
    accessory = (
      <G>
        <Circle cx="24" cy="20" r="3" fill="#ffb7c2" />
        <Circle cx="96" cy="24" r="3" fill="#ffb938" />
        <Circle cx="18" cy="46" r="2.5" fill="#3b78d8" />
        <Circle cx="102" cy="48" r="2.5" fill="#3ddc97" />
      </G>
    );
  }

  return (
    <View style={[styles.container, { width: size, height: size }, style]}>
      <Svg width={size} height={size} viewBox="0 0 120 120">
        <Defs>
          <LinearGradient id={`b-${uid}`} x1="10%" y1="0%" x2="90%" y2="100%">
            <Stop offset="0%" stopColor="#8fb4ff" />
            <Stop offset="55%" stopColor="#3b78d8" />
            <Stop offset="100%" stopColor="#2556b8" />
          </LinearGradient>
          <RadialGradient id={`h-${uid}`} cx="30%" cy="20%" r="60%">
            <Stop offset="0%" stopColor="#ffffff" stopOpacity={0.75} />
            <Stop offset="100%" stopColor="#ffffff" stopOpacity={0} />
          </RadialGradient>
          <LinearGradient id={`f-${uid}`} x1="0%" y1="0%" x2="0%" y2="100%">
            <Stop offset="0%" stopColor="#ffffff" />
            <Stop offset="100%" stopColor="#e6edff" />
          </LinearGradient>
        </Defs>

        {/* Shadow */}
        <Ellipse cx="60" cy="112" rx="32" ry="5" fill="#2556b8" opacity={0.16} />

        {/* Shield Body */}
        <Path
          d="M60 8 L101 23 V55 C101 85 83 102 60 110 C37 102 19 85 19 55 V23 Z"
          fill={`url(#b-${uid})`}
        />
        <Path
          d="M60 8 L101 23 V55 C101 85 83 102 60 110 C37 102 19 85 19 55 V23 Z"
          fill={`url(#h-${uid})`}
        />
        <Path
          d="M60 8 L101 23 V55 C101 85 83 102 60 110"
          fill="none"
          stroke="#1d47a0"
          strokeOpacity={0.25}
          strokeWidth="2"
        />

        {/* Face Plate */}
        <Rect x="29" y="34" width="62" height="50" rx="22" fill={`url(#f-${uid})`} />

        {/* Eyes with highlights */}
        <Ellipse cx="46" cy="55" rx="5.2" ry="6.6" fill="#16213f" />
        <Ellipse cx="74" cy="55" rx="5.2" ry="6.6" fill="#16213f" />
        <Circle cx="47.8" cy="52.6" r="1.9" fill="#ffffff" />
        <Circle cx="75.8" cy="52.6" r="1.9" fill="#ffffff" />

        {/* Rosy cheeks */}
        <Circle cx="37" cy="66" r="4.2" fill="#ffb7c2" opacity={0.55} />
        <Circle cx="83" cy="66" r="4.2" fill="#ffb7c2" opacity={0.55} />

        {/* Mouth */}
        <Path
          d={mouthPath}
          fill="none"
          stroke="#16213f"
          strokeWidth="3.2"
          strokeLinecap="round"
        />

        {/* Peeking hands */}
        {isPeek && (
          <G>
            <Rect x="14" y="88" width="26" height="16" rx="8" fill="#2d63cf" />
            <Rect x="80" y="88" width="26" height="16" rx="8" fill="#2d63cf" />
          </G>
        )}

        {/* Accessory overlay */}
        {accessory}

        {/* Top right sparkle */}
        <Path
          d="M101 14 L103.6 19.4 L109 22 L103.6 24.6 L101 30 L98.4 24.6 L93 22 L98.4 19.4 Z"
          fill="#dbe6ff"
        />
      </Svg>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
});
