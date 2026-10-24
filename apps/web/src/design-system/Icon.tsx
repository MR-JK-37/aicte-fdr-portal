import React from 'react';
import {
  LayoutDashboard,
  Landmark,
  FileText,
  FolderOpen,
  BadgeCheck,
  ListChecks,
  Bell,
  BellRing,
  Clock,
  Calendar,
  Inbox,
  Search,
  ListFilter,
  FileUp,
  ScanLine,
  QrCode,
  Lock,
  Fingerprint,
  Shield,
  History,
  Settings,
  User,
  LogOut,
  TriangleAlert,
  OctagonX,
  CircleCheck,
  CircleX,
  Hourglass,
  RefreshCw,
  CloudOff,
  Link as LinkIcon,
  FilePenLine,
  CircleHelp,
  Ban,
  Receipt,
  ChartBar,
  Download,
  Share,
  Plus,
  Languages,
  Smartphone,
  BookOpen,
  ScrollText,
  type LucideProps,
} from 'lucide-react';

/**
 * One open icon family for the web: Lucide ("regular"/outline weight),
 * chosen per MASTER_PROMPT §13.2's "spike picks one" instruction (the
 * repo already depended on lucide-react before this phase; Phosphor was
 * the alternative — Lucide wins here because it ships as individual
 * tree-shaken ES module icons with a stroke width that already sits close
 * to 1.5px, matching the "sit near SF Symbols' weight" rule, with no extra
 * install needed). SF Symbols and Material Symbols must NEVER be used on
 * web (DESIGN_SPEC.md §8 rule + licence restriction).
 *
 * Components reference a LOGICAL KEY (closed enum below), never a raw
 * lucide icon, so the whole app can never accidentally mix icon families
 * and so a future icon-set swap touches exactly this one file.
 * Keys mirror the table in design/DESIGN_SPEC.md §8 exactly.
 */
const ICONS = {
  dashboard: LayoutDashboard,
  institution: Landmark,
  instrument: FileText,
  documents: FolderOpen,
  verified: BadgeCheck,
  checklist: ListChecks,
  notifications: Bell,
  notifications_active: BellRing,
  deadline: Clock,
  calendar: Calendar,
  inbox: Inbox,
  search: Search,
  filter: ListFilter,
  upload: FileUp,
  scan: ScanLine,
  qr: QrCode,
  lock: Lock,
  biometric: Fingerprint,
  security: Shield,
  history: History,
  settings: Settings,
  profile: User,
  sign_out: LogOut,
  warning: TriangleAlert,
  error: OctagonX,
  success: CircleCheck,
  failed: CircleX,
  pending: Hourglass,
  sync: RefreshCw,
  offline: CloudOff,
  link: LinkIcon,
  declared: FilePenLine,
  help: CircleHelp,
  blocked: Ban,
  receipt: Receipt,
  report: ChartBar,
  download: Download,
  share: Share,
  add: Plus,
  language: Languages,
  devices: Smartphone,
  policy: BookOpen,
  audit: ScrollText,
} as const;

export type IconName = keyof typeof ICONS;

export interface IconProps extends Omit<LucideProps, 'ref'> {
  name: IconName;
  /** Accessible label. Omit (default) to mark the icon decorative (aria-hidden) when it always sits next to a text label — never the case for status, which must announce state via the label next to it, not the icon alone. */
  label?: string;
}

export function Icon({ name, label, size = 20, strokeWidth = 1.5, ...rest }: IconProps) {
  const Cmp = ICONS[name];
  if (!Cmp) {
    // Closed enum: a typo here is a compile error in TS call sites, but
    // guard at runtime too for any dynamic `name` coming from data.
    return null;
  }
  return (
    <Cmp
      size={size}
      strokeWidth={strokeWidth}
      aria-hidden={label ? undefined : true}
      aria-label={label}
      role={label ? 'img' : undefined}
      {...rest}
    />
  );
}
