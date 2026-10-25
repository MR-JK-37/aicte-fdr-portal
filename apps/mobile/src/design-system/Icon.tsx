import React from 'react';
import { Platform, Text } from 'react-native';
import { SymbolView, type SymbolViewProps } from 'expo-symbols';
import { MsIcon } from 'material-symbols-react-native';
import * as outlined400 from '@material-symbols-react-native/outlined-400';

/**
 * One logical icon key, resolved per-platform:
 *  - Android -> Material Symbols (outlined, weight 400) via `material-symbols-react-native`,
 *    per docs/spikes/S-07.md's recommendation (per-icon tree-shaken SVG imports;
 *    static weight instead of runtime variable-axis manipulation, since RN's
 *    font-variation-settings support is unverified for RN 0.88).
 *  - iOS      -> SF Symbols via `expo-symbols`' `SymbolView`, per docs/spikes/S-03.md.
 *    `fallback` is REQUIRED per that spike's finding (expo-symbols renders
 *    nothing without one if the symbol name doesn't resolve on-device).
 * Never import a MaterialIcons/FontAwesome/etc. icon or a raw SF Symbol name
 * outside this file — DESIGN_SPEC.md §8/§13.3: "Material Symbols only" on
 * Android, SF Symbols only on iOS, and both resolve from this one closed
 * enum so a CI icon-import lint rule (tracked, not yet wired — see README)
 * has exactly one file to allow-list.
 */
export const ICON_NAMES = [
  'dashboard', 'institution', 'instrument', 'documents', 'verified',
  'checklist', 'notifications', 'notifications_active', 'deadline', 'calendar',
  'inbox', 'search', 'filter', 'upload', 'scan', 'qr', 'lock', 'biometric',
  'security', 'history', 'settings', 'profile', 'sign_out', 'warning', 'error',
  'success', 'failed', 'pending', 'sync', 'offline', 'link', 'declared',
  'help', 'blocked', 'receipt', 'report', 'download', 'share', 'add',
  'language', 'devices', 'policy', 'audit', 'chat', 'send',
] as const;

export type IconName = typeof ICON_NAMES[number];

const MATERIAL: Record<IconName, { icon: typeof outlined400.msDashboard; fill: typeof outlined400.msDashboardFill }> = {
  dashboard: { icon: outlined400.msDashboard, fill: outlined400.msDashboardFill },
  institution: { icon: outlined400.msAccountBalance, fill: outlined400.msAccountBalanceFill },
  instrument: { icon: outlined400.msDescription, fill: outlined400.msDescriptionFill },
  documents: { icon: outlined400.msFolderOpen, fill: outlined400.msFolderOpenFill },
  verified: { icon: outlined400.msVerified, fill: outlined400.msVerified },
  checklist: { icon: outlined400.msFactCheck, fill: outlined400.msFactCheckFill },
  notifications: { icon: outlined400.msNotifications, fill: outlined400.msNotifications },
  notifications_active: { icon: outlined400.msNotificationsActive, fill: outlined400.msNotificationsActive },
  deadline: { icon: outlined400.msSchedule, fill: outlined400.msSchedule },
  calendar: { icon: outlined400.msCalendarMonth, fill: outlined400.msCalendarMonthFill },
  inbox: { icon: outlined400.msInbox, fill: outlined400.msInboxFill },
  search: { icon: outlined400.msSearch, fill: outlined400.msSearch },
  filter: { icon: outlined400.msFilterList, fill: outlined400.msFilterListFill },
  upload: { icon: outlined400.msUploadFile, fill: outlined400.msUploadFile },
  scan: { icon: outlined400.msDocumentScanner, fill: outlined400.msDocumentScannerFill },
  qr: { icon: outlined400.msQrCodeScanner, fill: outlined400.msQrCodeScanner },
  lock: { icon: outlined400.msLock, fill: outlined400.msLock },
  biometric: { icon: outlined400.msFingerprint, fill: outlined400.msFingerprintFill },
  security: { icon: outlined400.msShield, fill: outlined400.msShield },
  history: { icon: outlined400.msHistory, fill: outlined400.msHistoryFill },
  settings: { icon: outlined400.msSettings, fill: outlined400.msSettings },
  profile: { icon: outlined400.msPerson, fill: outlined400.msPerson },
  sign_out: { icon: outlined400.msLogout, fill: outlined400.msLogoutFill },
  warning: { icon: outlined400.msWarning, fill: outlined400.msWarning },
  error: { icon: outlined400.msError, fill: outlined400.msError },
  success: { icon: outlined400.msCheckCircle, fill: outlined400.msCheckCircleFill },
  failed: { icon: outlined400.msCancel, fill: outlined400.msCancel },
  pending: { icon: outlined400.msHourglassTop, fill: outlined400.msHourglassTopFill },
  sync: { icon: outlined400.msSync, fill: outlined400.msSync },
  offline: { icon: outlined400.msCloudOff, fill: outlined400.msCloudOffFill },
  link: { icon: outlined400.msLink, fill: outlined400.msLink },
  declared: { icon: outlined400.msEditNote, fill: outlined400.msEditNoteFill },
  help: { icon: outlined400.msHelp, fill: outlined400.msHelp },
  blocked: { icon: outlined400.msBlock, fill: outlined400.msBlock },
  receipt: { icon: outlined400.msReceiptLong, fill: outlined400.msReceiptLong },
  report: { icon: outlined400.msBarChart, fill: outlined400.msBarChartFill },
  download: { icon: outlined400.msDownload, fill: outlined400.msDownload },
  share: { icon: outlined400.msShare, fill: outlined400.msShare },
  add: { icon: outlined400.msAdd, fill: outlined400.msAdd },
  language: { icon: outlined400.msTranslate, fill: outlined400.msTranslate },
  devices: { icon: outlined400.msDevices, fill: outlined400.msDevices },
  policy: { icon: outlined400.msPolicy, fill: outlined400.msPolicy },
  audit: { icon: outlined400.msManageSearchFill ?? outlined400.msManageSearch, fill: outlined400.msManageSearchFill },
  chat: { icon: outlined400.msChat, fill: outlined400.msChatFill },
  send: { icon: outlined400.msSend, fill: outlined400.msSendFill },
};

/** SF Symbol names, per design/DESIGN_SPEC.md §8's iOS column. */
const SF_SYMBOL: Record<IconName, string> = {
  dashboard: 'square.grid.2x2',
  institution: 'building.columns',
  instrument: 'doc.text',
  documents: 'folder',
  verified: 'checkmark.seal',
  checklist: 'checklist',
  notifications: 'bell',
  notifications_active: 'bell.badge',
  deadline: 'clock',
  calendar: 'calendar',
  inbox: 'tray',
  search: 'magnifyingglass',
  filter: 'line.3.horizontal.decrease',
  upload: 'arrow.up.doc',
  scan: 'doc.viewfinder',
  qr: 'qrcode.viewfinder',
  lock: 'lock',
  biometric: 'faceid',
  security: 'shield',
  history: 'clock.arrow.circlepath',
  settings: 'gearshape',
  profile: 'person',
  sign_out: 'rectangle.portrait.and.arrow.right',
  warning: 'exclamationmark.triangle',
  error: 'xmark.octagon',
  success: 'checkmark.circle',
  failed: 'xmark.circle',
  pending: 'hourglass',
  sync: 'arrow.triangle.2.circlepath',
  offline: 'icloud.slash',
  link: 'link',
  declared: 'square.and.pencil',
  help: 'questionmark.circle',
  blocked: 'nosign',
  receipt: 'doc.plaintext',
  report: 'chart.bar',
  download: 'arrow.down.circle',
  share: 'square.and.arrow.up',
  add: 'plus',
  language: 'globe',
  devices: 'iphone',
  policy: 'text.book.closed',
  audit: 'list.bullet.rectangle',
  chat: 'bubble.left.and.bubble.right',
  send: 'paperplane',
};

export interface IconProps {
  name: IconName;
  size?: number;
  color?: string;
  /** Selected/active nav state: Material FILL=1 on Android (same glyph, filled variant); SF Symbol `.fill` suffix on iOS. */
  filled?: boolean;
}

export function Icon({ name, size = 24, color, filled }: IconProps) {
  if (Platform.OS === 'android') {
    const def = MATERIAL[name];
    const chosen = filled ? def.fill : def.icon;
    return <MsIcon icon={chosen} size={size} color={color} />;
  }
  if (Platform.OS === 'ios') {
    const symbolName = SF_SYMBOL[name] + (filled ? '.fill' : '');
    const props: SymbolViewProps = {
      name: symbolName as SymbolViewProps['name'],
      style: { width: size, height: size },
      tintColor: color,
      // Required per docs/spikes/S-03.md: expo-symbols renders nothing
      // without an explicit fallback if the symbol name doesn't resolve.
      fallback: <Text style={{ fontSize: size * 0.6, color }}>•</Text>,
    };
    return <SymbolView {...props} />;
  }
  // Web preview inside Expo (`expo start --web`) — neither icon set applies
  // (both SF Symbols and Material Symbols are platform-native here); a
  // plain placeholder keeps the dev build runnable without crashing.
  return <Text style={{ fontSize: size * 0.6, color }}>•</Text>;
}
