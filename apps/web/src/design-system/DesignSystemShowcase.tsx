import React, { useState } from 'react';
import {
  ThemeProvider,
  useTheme,
  Button,
  TextInput,
  SearchInput,
  Select,
  Card,
  Sidebar,
  Toolbar,
  EvidenceChip,
  StatusBadge,
  LoadingState,
  EmptyState,
  ErrorState,
  ForbiddenState,
  OfflineState,
  Icon,
  type SidebarItem,
} from './index';
import { createTranslator } from '@aicte-fdr/i18n';

const NAV_ITEMS: SidebarItem[] = [
  { key: 'dashboard', label: 'Dashboard', icon: 'dashboard' },
  { key: 'institutions', label: 'Institutions', icon: 'institution' },
  { key: 'instruments', label: 'Instruments', icon: 'instrument' },
  { key: 'verification', label: 'Verification', icon: 'checklist' },
  { key: 'notifications', label: 'Notifications', icon: 'notifications' },
  { key: 'audit', label: 'Audit log', icon: 'audit' },
  { key: 'settings', label: 'Settings', icon: 'settings' },
];

const EVIDENCE_ATTRS = ['declared', 'extracted', 'bankConfirmed', 'ledgerReconciled', 'inconclusive', 'rejected'] as const;
const STATUS_TONES = ['ok', 'warn', 'info', 'error', 'pending', 'neutral'] as const;

function ThemeControls() {
  const { mode, setMode, reduceTransparency, setReduceTransparency } = useTheme();
  return (
    <div className="ds-showcase__row" style={{ marginBottom: 8 }}>
      <Select
        label="Theme"
        value={mode}
        onChange={(e) => setMode(e.target.value as any)}
        options={[
          { value: 'dark', label: 'Dark (hero)' },
          { value: 'light', label: 'Light' },
          { value: 'system', label: 'System' },
        ]}
      />
      <Button
        variant={reduceTransparency ? 'filled' : 'outline'}
        onClick={() => setReduceTransparency(!reduceTransparency)}
      >
        Reduce transparency: {reduceTransparency ? 'On' : 'Off'}
      </Button>
    </div>
  );
}

function ShowcaseBody() {
  const [active, setActive] = useState('dashboard');
  const [locale, setLocale] = useState<'en' | 'hi' | 'ta'>('en');
  const t = createTranslator(locale);

  return (
    <div className="ds-showcase ds-root">
      <Sidebar items={NAV_ITEMS} activeKey={active} onSelect={setActive} tinted />
      <div className="ds-showcase__main">
        <Toolbar>
          <strong>{t('app.name')}</strong>
          <div style={{ flex: 1 }} />
          <Select
            label="Locale"
            value={locale}
            onChange={(e) => setLocale(e.target.value as any)}
            options={[
              { value: 'en', label: 'English' },
              { value: 'hi', label: 'हिन्दी (machine-draft)' },
              { value: 'ta', label: 'தமிழ் (machine-draft)' },
            ]}
          />
          <Button variant="text" iconOnly aria-label="Notifications">
            <Icon name="notifications" />
          </Button>
        </Toolbar>

        <ThemeControls />

        <section className="ds-showcase__section">
          <h2 className="ds-showcase__heading">Buttons</h2>
          <div className="ds-showcase__row">
            <Button variant="filled">Filled</Button>
            <Button variant="tonal">Tonal</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="text">Text</Button>
            <Button variant="destructive">Destructive</Button>
            <Button variant="outline" disabled>Disabled</Button>
            <Button variant="filled" iconOnly aria-label="Add"><Icon name="add" /></Button>
          </div>
        </section>

        <section className="ds-showcase__section">
          <h2 className="ds-showcase__heading">Inputs</h2>
          <div className="ds-showcase__row">
            <TextInput label="Institution name" placeholder="e.g. Delhi Global Technical Campus" />
            <TextInput label="Deposit amount" amount placeholder="35,00,000" />
            <SearchInput label="Search" />
            <Select label="Bank" options={[{ value: 'sbi', label: 'State Bank of India' }, { value: 'axis', label: 'Axis Bank' }]} />
            <TextInput label="UTR" errorText="UTR must be 16–22 characters" />
          </div>
        </section>

        <section className="ds-showcase__section">
          <h2 className="ds-showcase__heading">Cards / surfaces (solid, never glass)</h2>
          <div className="ds-showcase__row">
            <Card style={{ width: 280 }}>
              <strong>Card title</strong>
              <p className="ds-showcase__sub">Solid surface, never glass</p>
            </Card>
            <Card elevated style={{ width: 280 }}>
              <strong>Elevated surface</strong>
              <p className="ds-showcase__sub">surface-high tonal step</p>
            </Card>
          </div>
        </section>

        <section className="ds-showcase__section">
          <h2 className="ds-showcase__heading">Evidence-attribute chips</h2>
          <p className="ds-showcase__sub">{t('evidence.declared')} / {t('evidence.bankConfirmed')} — distinct shape + icon, never colour alone.</p>
          <div className="ds-showcase__row">
            {EVIDENCE_ATTRS.map((a) => <EvidenceChip key={a} attribute={a} source="Demo source, 12 Sep 2026" />)}
          </div>
        </section>

        <section className="ds-showcase__section">
          <h2 className="ds-showcase__heading">Status badges</h2>
          <div className="ds-showcase__row">
            {STATUS_TONES.map((tone) => <StatusBadge key={tone} tone={tone} label={t(`status.${tone}`)} />)}
          </div>
        </section>

        <section className="ds-showcase__section">
          <h2 className="ds-showcase__heading">Data-view states</h2>
          <div className="ds-showcase__row" style={{ alignItems: 'stretch' }}>
            <Card style={{ width: 280 }}><LoadingState /></Card>
            <Card style={{ width: 280 }}><EmptyState title={t('state.empty.title')} body={t('state.empty.body')} actionLabel="Add instrument" onAction={() => {}} /></Card>
            <Card style={{ width: 280 }}><ErrorState title={t('state.error.title')} body="The server could not be reached." correlationId="c-9f31ab2e" onRetry={() => {}} /></Card>
            <Card style={{ width: 280 }}><ForbiddenState /></Card>
            <Card style={{ width: 280 }}><OfflineState what="Bank verifier" /></Card>
          </div>
        </section>
      </div>
    </div>
  );
}

/**
 * Internal, dev-only primitives showcase (`/_design-system`). Not linked
 * from app navigation and not part of any real screen — it exists so the
 * `design-reviewer` subagent and humans can see every primitive, in both
 * themes and with reduced transparency, before any real screen is built.
 */
export function DesignSystemShowcase() {
  return (
    <ThemeProvider>
      <ShowcaseBody />
    </ThemeProvider>
  );
}
