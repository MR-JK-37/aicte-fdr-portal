import React from 'react';
import { evidenceChip } from '@aicte-fdr/design-tokens';
import { Icon, type IconName } from './Icon';

export type EvidenceAttribute = keyof typeof evidenceChip;

const SHAPE_CLASS: Record<string, string> = {
  outlined: 'pill pill-neutral',
  dashed: 'pill pill-pending',
  filled: 'pill pill-ok',
  warning: 'pill pill-warn',
  stop: 'pill pill-error',
};

const ICON_MAP: Record<string, IconName> = {
  declared: 'declared',
  scan: 'scan',
  verified: 'verified',
  link: 'link',
  help: 'help',
  blocked: 'blocked',
  edit_note: 'declared',
  document_scanner: 'scan',
  block: 'blocked',
};

export interface EvidenceChipProps {
  attribute: EvidenceAttribute;
  source?: string;
  className?: string;
}

/**
 * Evidence-attribute chip — distinct shape + icon + label per attribute (DESIGN_SPEC §2 / §5).
 * Never colour alone.
 */
export function EvidenceChip({ attribute, source, className = '' }: EvidenceChipProps) {
  const def = evidenceChip[attribute];
  if (!def) return null;

  const shapeClass =
    attribute === 'ledgerReconciled' ? 'pill pill-info' : SHAPE_CLASS[def.shape] || 'pill pill-neutral';
  const iconName = ICON_MAP[def.iconKey] ?? 'help';

  return (
    <span
      className={`${shapeClass} ${className}`}
      title={source ? `${def.label} — ${source}` : def.label}
      data-testid="evidence-chip"
    >
      <Icon name={iconName} size={13} />
      <span>{def.label}</span>
    </span>
  );
}
