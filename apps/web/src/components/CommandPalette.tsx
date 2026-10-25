import React, { useState, useEffect, useRef } from 'react';
import { Search, ArrowRight, LayoutDashboard, FileText, CheckCircle2, Clock, Shield, Sparkles, Database, HelpCircle, BarChart3, Settings, QrCode } from 'lucide-react';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectAction: (tabId: string) => void;
}

interface CommandItem {
  id: string;
  label: string;
  category: 'Navigation' | 'Actions' | 'Regulatory';
  shortcut?: string;
  icon: React.ReactNode;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose, onSelectAction }) => {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const commands: CommandItem[] = [
    { id: 'dashboard', label: 'Go to KPI Dashboard & Register', category: 'Navigation', icon: <LayoutDashboard size={14} />, shortcut: 'G D' },
    { id: 'search', label: 'Universal Search & Saved Views (F-17)', category: 'Navigation', icon: <Search size={14} />, shortcut: 'G S' },
    { id: 'submit', label: 'Submit New FDR Intake', category: 'Navigation', icon: <FileText size={14} />, shortcut: 'G N' },
    { id: 'verify', label: 'Bank Branch & Statement Verification', category: 'Navigation', icon: <CheckCircle2 size={14} />, shortcut: 'G V' },
    { id: 'reminders', label: 'Maturity Calendar & Escalation Ladder', category: 'Navigation', icon: <Clock size={14} />, shortcut: 'G M' },
    { id: 'release', label: 'Release Authorization & Maker-Checker', category: 'Navigation', icon: <Shield size={14} />, shortcut: 'G R' },
    { id: 'reports', label: 'Regulatory Reports Catalogue & Exports (F-16)', category: 'Navigation', icon: <BarChart3 size={14} />, shortcut: 'G E' },
    { id: 'copilot', label: 'AI Copilot (bounded policy Q&A)', category: 'Regulatory', icon: <Sparkles size={14} />, shortcut: 'G C' },
    { id: 'audit', label: 'Cryptographic Audit Trail & WORM Ledger (F-18)', category: 'Regulatory', icon: <Database size={14} />, shortcut: 'G A' },
    { id: 'admin', label: 'System Admin & Connector Health (F-19)', category: 'Actions', icon: <Settings size={14} />, shortcut: 'G X' },
    { id: 'help', label: 'Help, Support & DPDP Data Rights (F-21, F-22)', category: 'Regulatory', icon: <HelpCircle size={14} />, shortcut: 'G H' },
    { id: 'public_receipt', label: 'Public Receipt Verification Portal (F-20)', category: 'Actions', icon: <QrCode size={14} />, shortcut: 'G P' },
  ];

  const filtered = commands.filter((c) =>
    c.label.toLowerCase().includes(query.toLowerCase()) ||
    c.category.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % Math.max(1, filtered.length));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + filtered.length) % Math.max(1, filtered.length));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filtered[selectedIndex]) {
          onSelectAction(filtered[selectedIndex].id);
          onClose();
        }
      } else if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filtered, selectedIndex, onSelectAction, onClose]);

  if (!isOpen) return null;

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 100, display: 'flex', alignItems: 'flex-start', justifyContent: 'center', paddingTop: '80px', padding: '16px', background: 'rgba(15, 23, 42, 0.45)', backdropFilter: 'blur(8px)' }}>
      <div style={{ width: '100%', maxWidth: '580px', borderRadius: '24px', background: 'var(--surface)', border: '1px solid var(--border)', boxShadow: '0 24px 48px rgba(0, 0, 0, 0.16)', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {/* Search Input Bar */}
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '12px', background: 'var(--field)' }}>
          <Search size={18} color="var(--azure)" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            placeholder="Type a command or screen name (e.g., reports, search, release)..."
            style={{ width: '100%', background: 'transparent', border: 'none', fontSize: '13px', color: 'var(--text1)', fontWeight: 600, outline: 'none' }}
          />
          <kbd style={{ padding: '2px 8px', borderRadius: '6px', fontSize: '10px', fontFamily: 'var(--font-mono)', fontWeight: 700, background: 'var(--surface)', color: 'var(--text3)', border: '1px solid var(--border)' }}>
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div style={{ maxHeight: '340px', overflowY: 'auto', padding: '10px', display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '12px' }}>
          {filtered.length === 0 ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text3)' }}>No matching commands found.</div>
          ) : (
            filtered.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={item.id}
                  onClick={() => {
                    onSelectAction(item.id);
                    onClose();
                  }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  style={{
                    padding: '12px 14px',
                    borderRadius: '14px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    background: isSelected ? 'var(--primary-container)' : 'transparent',
                    color: isSelected ? 'var(--azure)' : 'var(--text1)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ padding: '6px', borderRadius: '8px', background: isSelected ? '#FFFFFF' : 'var(--field)', color: isSelected ? 'var(--azure)' : 'var(--text3)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      {item.icon}
                    </span>
                    <div>
                      <div style={{ fontWeight: 700, color: isSelected ? 'var(--azure)' : 'var(--text1)' }}>{item.label}</div>
                      <div style={{ fontSize: '10px', color: 'var(--text3)' }}>{item.category}</div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {item.shortcut && (
                      <kbd style={{ padding: '2px 6px', borderRadius: '4px', fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text3)', background: 'var(--field)', border: '1px solid var(--border)' }}>
                        {item.shortcut}
                      </kbd>
                    )}
                    <ArrowRight size={14} color={isSelected ? 'var(--azure)' : 'var(--text3)'} />
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer shortcuts helper */}
        <div style={{ padding: '12px 20px', borderTop: '1px solid var(--border)', background: 'var(--field)', fontSize: '11px', color: 'var(--text3)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span>↑↓ Navigate</span>
            <span>↵ Select</span>
            <span>ESC Close</span>
          </div>
          <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--azure)', fontWeight: 600 }}>⌘K Command Palette</span>
        </div>
      </div>
    </div>
  );
};
