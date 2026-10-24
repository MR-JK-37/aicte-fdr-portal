import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { evidenceChip } from '@aicte-fdr/design-tokens';
import { useAppTheme } from './theme';
import { Icon, type IconName } from './Icon';

export type EvidenceAttribute = keyof typeof evidenceChip;

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
  source?: string;
}

/**
 * Evidence-attribute chip, platform-rendered RN version of the web
 * component. Shape is expressed via border style (solid/dashed/none +
 * fill), never colour alone — same rule, same token source
 * (@aicte-fdr/design-tokens' `evidenceChip`), DESIGN_SPEC §13.1.
 */
export function EvidenceChip({ attribute, source }: EvidenceChipProps) {
  const { tone } = useAppTheme();
  const def = evidenceChip[attribute];
  const iconName = ICON_MAP[def.iconKey] ?? 'help';

  const style = {
    outlined: { borderWidth: 1.5, borderColor: tone.outline, borderStyle: 'solid' as const, backgroundColor: 'transparent' },
    dashed: { borderWidth: 1.5, borderColor: tone.outline, borderStyle: 'dashed' as const, backgroundColor: 'transparent' },
    filled: attribute === 'ledgerReconciled'
      ? { borderWidth: 0, backgroundColor: `${tone.info}26` }
      : { borderWidth: 0, backgroundColor: `${tone.ok}26` },
    warning: { borderWidth: 1.5, borderColor: tone.warn, borderStyle: 'dashed' as const, backgroundColor: `${tone.warn}1a` },
    stop: { borderWidth: 1.5, borderColor: tone.error, borderStyle: 'solid' as const, backgroundColor: `${tone.error}26` },
  }[def.shape];

  const textColor = {
    outlined: tone.text1,
    dashed: tone.text2,
    filled: attribute === 'ledgerReconciled' ? tone.info : tone.ok,
    warning: tone.warn,
    stop: tone.error,
  }[def.shape];

  return (
    <View style={[styles.chip, style]} accessibilityLabel={source ? `${def.label} — ${source}` : def.label}>
      <Icon name={iconName} size={14} color={textColor} />
      <Text style={[styles.label, { color: textColor }]}>{def.label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  chip: { flexDirection: 'row', alignItems: 'center', gap: 4, height: 26, paddingHorizontal: 10, borderRadius: 999, alignSelf: 'flex-start' },
  label: { fontSize: 12, fontWeight: '600' },
});
