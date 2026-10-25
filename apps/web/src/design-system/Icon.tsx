import React from 'react';
import {
  SquaresFour,
  Bank,
  FileText,
  FolderOpen,
  SealCheck,
  ListChecks,
  Bell,
  BellRinging,
  Clock,
  Calendar,
  Tray,
  MagnifyingGlass,
  Funnel,
  UploadSimple,
  Scan,
  QrCode,
  Lock,
  Fingerprint,
  ShieldCheck,
  ClockCounterClockwise,
  Gear,
  User,
  SignOut,
  Warning,
  XCircle,
  CheckCircle,
  Hourglass,
  ArrowsClockwise,
  CloudSlash,
  Link as LinkIcon,
  PencilSimpleLine,
  Question,
  Prohibit,
  Receipt,
  ChartBar,
  DownloadSimple,
  ShareNetwork,
  Plus,
  Translate,
  DeviceMobile,
  BookOpen,
  Scroll,
  CaretRight,
  Check,
  type IconProps as PhosphorProps,
} from '@phosphor-icons/react';

/**
 * Authoritative web icon family: Phosphor Icons (MIT), with `duotone` weight
 * for nav and list icons (azure), and `regular` elsewhere.
 * Keys mirror the table in design/DESIGN_SPEC.md §7 / §8 exactly.
 */
const ICONS = {
  dashboard: SquaresFour,
  institution: Bank,
  instrument: FileText,
  documents: FolderOpen,
  verified: SealCheck,
  checklist: ListChecks,
  notifications: Bell,
  notifications_active: BellRinging,
  deadline: Clock,
  calendar: Calendar,
  inbox: Tray,
  search: MagnifyingGlass,
  filter: Funnel,
  upload: UploadSimple,
  scan: Scan,
  qr: QrCode,
  lock: Lock,
  biometric: Fingerprint,
  security: ShieldCheck,
  history: ClockCounterClockwise,
  settings: Gear,
  profile: User,
  sign_out: SignOut,
  warning: Warning,
  error: XCircle,
  success: CheckCircle,
  failed: XCircle,
  pending: Hourglass,
  sync: ArrowsClockwise,
  offline: CloudSlash,
  link: LinkIcon,
  declared: PencilSimpleLine,
  help: Question,
  blocked: Prohibit,
  receipt: Receipt,
  report: ChartBar,
  download: DownloadSimple,
  share: ShareNetwork,
  add: Plus,
  language: Translate,
  devices: DeviceMobile,
  policy: BookOpen,
  audit: Scroll,
  chev: CaretRight,
  check: Check,
} as const;

export type IconName = keyof typeof ICONS;

export interface IconProps extends Omit<PhosphorProps, 'ref'> {
  name: IconName;
  /** Accessible label. Omit (default) to mark the icon decorative (aria-hidden). */
  label?: string;
  weight?: 'duotone' | 'regular' | 'bold' | 'fill' | 'light' | 'thin';
}

export function Icon({
  name,
  label,
  size = 22,
  weight = 'duotone',
  color,
  className,
  style,
  ...rest
}: IconProps) {
  const Cmp = ICONS[name];
  if (!Cmp) {
    return null;
  }
  return (
    <Cmp
      size={size}
      weight={weight}
      color={color}
      className={className}
      style={style}
      aria-hidden={label ? undefined : true}
      aria-label={label}
      role={label ? 'img' : undefined}
      {...rest}
    />
  );
}
