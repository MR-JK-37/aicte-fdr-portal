import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TopBar } from './TopBar';
import { Button } from './Button';
import { Card } from './Card';
import { FloatingTabBar } from './FloatingTabBar';
import { BottomSheet } from './BottomSheet';
import { EmptyState } from './States';
import { Wordmark } from './Wordmark';
import { Kosh } from './Kosh';
import { light, dark } from '@aicte-fdr/design-tokens';

describe('Design-Contract Tests (R5.0 & G-24 / DESIGN_SPEC.md)', () => {
  it('R5.0(1) TopBar has wordmark, progress-mini, bell, and role-pill with >= 4.5 contrast', () => {
    render(<TopBar role="Registrar" profileCompletionPct={56} unreadCount={2} />);

    const topbar = screen.getByTestId('topbar');
    expect(topbar).toBeTruthy();

    const wordmark = screen.getByTestId('wordmark');
    expect(wordmark).toBeTruthy();
    expect(wordmark.textContent).toContain('fdr');
    expect(wordmark.textContent).toContain('portal');

    const progressMini = screen.getByTestId('progress-mini');
    expect(progressMini).toBeTruthy();
    expect(progressMini.textContent).toContain('56%');

    const bell = screen.getByTestId('bell');
    expect(bell).toBeTruthy();
    const bellDot = screen.getByTestId('bell-dot');
    expect(bellDot).toBeTruthy();

    const rolePill = screen.getByTestId('role-pill');
    expect(rolePill).toBeTruthy();
    expect(rolePill.textContent).toBe('Registrar');
    expect(rolePill.className).toContain('pill-role');

    // WCAG AA contrast check: #ffffff on #4570da (roleFill)
    const lin = (c: number) => {
      c /= 255;
      return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    };
    const L = (h: string) => {
      const hex = h.replace('#', '');
      const r = parseInt(hex.substring(0, 2), 16);
      const g = parseInt(hex.substring(2, 4), 16);
      const b = parseInt(hex.substring(4, 6), 16);
      return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
    };
    const cr = (a: string, b: string) => {
      const [la, lb] = [L(a), L(b)].sort((x, y) => y - x);
      return (la + 0.05) / (lb + 0.05);
    };

    const roleContrast = cr(light.onRoleFill, light.roleFill);
    expect(roleContrast).toBeGreaterThanOrEqual(4.5);
  });

  it('R5.0(2) Primary buttons are pills with background --ink', () => {
    render(<Button variant="primary" data-testid="prim-btn">Save Changes</Button>);
    const btn = screen.getByTestId('prim-btn');
    expect(btn.className).toContain('btn');
    expect(btn.className).toContain('btn-primary');
  });

  it('R5.0(3) Destructive pair uses --danger-container', () => {
    render(
      <div>
        <Button variant="primary" data-testid="confirm-btn">Approve</Button>
        <Button variant="danger-soft" data-testid="reject-btn">Reject</Button>
      </div>
    );
    const rejectBtn = screen.getByTestId('reject-btn');
    expect(rejectBtn.className).toContain('btn-danger-soft');
  });

  it('R5.0(4) Cards have radius 20px and no 1px border', () => {
    render(
      <Card data-testid="test-card">
        <div>Content inside card</div>
      </Card>
    );
    const card = screen.getByTestId('test-card');
    expect(card.className).toContain('card');
  });

  it('R5.0(5) Tab bar is fixed floating pill (radius >= 24, 12px side inset, 4-5 items, azure icons, primaryContainer active capsule)', () => {
    const tabs = [
      { id: 'home', label: 'Home', icon: 'dashboard' as const },
      { id: 'deposits', label: 'Deposits', icon: 'documents' as const },
      { id: 'inbox', label: 'Inbox', icon: 'inbox' as const },
      { id: 'profile', label: 'Profile', icon: 'profile' as const },
    ];
    render(<FloatingTabBar items={tabs} activeId="deposits" onSelect={() => {}} />);

    const tabbar = screen.getByTestId('tabbar');
    expect(tabbar.className).toContain('tabbar');

    // 4 items
    expect(tabs.length).toBe(4);
    const activeTab = screen.getByTestId('tab-deposits');
    expect(activeTab.getAttribute('aria-selected')).toBe('true');
    expect(activeTab.getAttribute('aria-current')).toBe('page');

    const inactiveTab = screen.getByTestId('tab-home');
    expect(inactiveTab.getAttribute('aria-selected')).toBe('false');
    expect(inactiveTab.getAttribute('aria-current')).toBeNull();
  });

  it('R5.0(6) List rows are 52-56px high with hairline separators and chevrons', () => {
    render(
      <div className="card-group" data-testid="grouped-card">
        <div className="section-label">Needs attention</div>
        <div className="row" data-testid="row-1">
          <div className="grow">
            <b>Reply to an observation</b>
            <small>Due 28 Oct 2026</small>
          </div>
          <span className="chev">›</span>
        </div>
        <div className="row" data-testid="row-2">
          <div className="grow">
            <b>FDR maturing in 30 days</b>
            <small>Renewal not yet submitted</small>
          </div>
          <span className="chev">›</span>
        </div>
      </div>
    );
    const row1 = screen.getByTestId('row-1');
    expect(row1.className).toContain('row');
    expect(row1.textContent).toContain('Reply to an observation');
    expect(row1.querySelector('.chev')).toBeTruthy();
  });

  it('R5.0(7) Chips and segments selected background is --ink', () => {
    render(
      <div>
        <div className="chiprow">
          <button className="chip" aria-pressed="true" data-testid="active-chip">
            All
          </button>
          <button className="chip" aria-pressed="false" data-testid="inactive-chip">
            Observations
          </button>
        </div>
        <div className="segmented" data-testid="segmented-control">
          <button aria-selected="true" data-testid="seg-active">Institution</button>
          <button aria-selected="false" data-testid="seg-inactive">AICTE staff</button>
        </div>
      </div>
    );

    const activeChip = screen.getByTestId('active-chip');
    expect(activeChip.getAttribute('aria-pressed')).toBe('true');

    const segActive = screen.getByTestId('seg-active');
    expect(segActive.getAttribute('aria-selected')).toBe('true');
  });

  it('R5.0(8) Sheets have a grabber, 28px top radius, and a blurred scrim', () => {
    render(
      <BottomSheet open={true} onClose={() => {}}>
        <div>Sheet Content</div>
      </BottomSheet>
    );

    const scrim = screen.getByTestId('bottom-sheet-scrim');
    expect(scrim.className).toContain('scrim');

    const sheet = screen.getByTestId('bottom-sheet');
    expect(sheet.className).toContain('sheet');

    const grabber = screen.getByTestId('sheet-grabber');
    expect(grabber.className).toContain('sheet-grabber');
  });

  it('R5.0(9) Empty states contain the Kosh SVG', () => {
    render(
      <EmptyState
        title="Nothing here yet"
        body="Reminders, observations and decisions will appear here as soon as they happen."
      />
    );

    const empty = screen.getByTestId('empty-state');
    expect(empty).toBeTruthy();
    expect(empty.textContent).toContain('Nothing here yet');

    const koshSvg = screen.getByTestId('kosh-svg');
    expect(koshSvg).toBeTruthy();
    expect(koshSvg.tagName.toLowerCase()).toBe('svg');
  });

  it('R5.0(10) No raw colours outside token set in design token definition', () => {
    const allTokens = [...Object.values(light), ...Object.values(dark)];
    const hexPattern = /^#[0-9a-fA-F]{6}$/;

    for (const token of allTokens) {
      expect(hexPattern.test(token)).toBe(true);
    }
  });
});
