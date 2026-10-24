import React from 'react';
import { evidenceChip } from '@aicte-fdr/design-tokens';
import { Icon, type IconName } from './Icon';

export type EvidenceAttribute = keyof typeof evidenceChip;

const SHAPE_CLASS: Record<string, string> = {
  outlined: 'ds-evidence-chip--outlined',
  dashed: 'ds-evidence-chip--dashed',
  filled: 'ds-evidence-chip--filled-ok',
  warning: 'ds-evidence-chip--warning',
  stop: 'ds-evidence-chip--stop',
};

// `verified`/`link` logical icon keys from tokens map to this web Icon's enum.
const ICON_MAP: Record<string, IconName> = {
  edit_note: 'declared',
  document_scanner: 'scan',
  verified: 'verified',
  link: 'link',
  help: 'help',
  block: 'blocked',
};

export interface EvidenceChipProps {
  attribute: EvidenceAttribute;
  /** Optional source detail shown as a title tooltip, e.g. "State Bank of India letter, 12 Sep 2026". */
  source?: string;
}

/**
 * Evidence-attribute chip — distinct shape + icon + label per attribute
 * (DESIGN_SPEC §13.1 / CLAUDE.md non-negotiable #3: never collapse evidence
 * into one colour/score). `ledgerReconciled` reuses the "filled" family but
 * with a link icon and the info tone, so it's still visually distinct from
 * bank-confirmed even though both are "filled".
 */
export function EvidenceChip({ attribute, source }: EvidenceChipProps) {
  const def = evidenceChip[attribute];
  const shapeClass = attribute === 'ledgerReconciled' ? 'ds-evidence-chip--filled-link' : SHAPE_CLASS[def.shape];
  const iconName = ICON_MAP[def.iconKey] ?? 'help';
  return (
    <span
      className={`ds-evidence-chip ${shapeClass}`}
      title={source ? `${def.label} — ${source}` : def.label}
    >
      <Icon name={iconName} size={14} />
      {def.label}
    </span>
  );
}
