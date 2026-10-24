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
    { id: 'submit', label: 'Submit New FDR Intake & OCR (L1)', category: 'Navigation', icon: <FileText size={14} />, shortcut: 'G N' },
    { id: 'verify', label: 'Bank Branch & Statement Verification (L2/L3)', category: 'Navigation', icon: <CheckCircle2 size={14} />, shortcut: 'G V' },
    { id: 'reminders', label: 'Maturity Calendar & Escalation Ladder', category: 'Navigation', icon: <Clock size={14} />, shortcut: 'G M' },
    { id: 'release', label: 'Release Authorization & Maker-Checker', category: 'Navigation', icon: <Shield size={14} />, shortcut: 'G R' },
    { id: 'reports', label: 'Regulatory Reports Catalogue & Exports (F-16)', category: 'Navigation', icon: <BarChart3 size={14} />, shortcut: 'G E' },
    { id: 'copilot', label: 'AI Copilot & Text-to-SQL Analytics', category: 'Regulatory', icon: <Sparkles size={14} />, shortcut: 'G C' },
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
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div className="w-full max-w-xl rounded-2xl bg-slate-900 border border-cyan-500/30 shadow-2xl overflow-hidden flex flex-col">
        {/* Search Input Bar */}
        <div className="p-4 border-b border-slate-800 flex items-center gap-3 bg-slate-950/60">
          <Search size={18} className="text-cyan-400" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            placeholder="Type a command or screen name (e.g., reports, search, release)..."
            className="w-full bg-transparent text-sm text-white placeholder-slate-500 focus:outline-none font-medium"
          />
          <kbd className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-slate-800 text-slate-400 border border-slate-700">
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div className="max-h-80 overflow-y-auto p-2 space-y-1 text-xs">
          {filtered.length === 0 ? (
            <div className="p-6 text-center text-slate-500">No matching commands found.</div>
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
                  className={`p-3 rounded-xl flex items-center justify-between cursor-pointer transition-colors ${
                    isSelected
                      ? 'bg-purple-950/60 text-white border border-cyan-500/40 shadow-sm shadow-cyan-950/20'
                      : 'text-slate-300 hover:bg-slate-800/60'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className={`p-1.5 rounded-lg ${isSelected ? 'bg-cyan-500/20 text-cyan-300' : 'bg-slate-800 text-slate-400'}`}>
                      {item.icon}
                    </span>
                    <div>
                      <div className="font-semibold">{item.label}</div>
                      <div className="text-[10px] text-slate-500">{item.category}</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {item.shortcut && (
                      <kbd className="px-1.5 py-0.5 rounded text-[10px] font-mono text-slate-400 bg-slate-950 border border-slate-800">
                        {item.shortcut}
                      </kbd>
                    )}
                    <ArrowRight size={14} className={isSelected ? 'text-cyan-400' : 'text-slate-600'} />
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer shortcuts helper */}
        <div className="p-3 border-t border-slate-800 bg-slate-950 text-[11px] text-slate-500 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span>↑↓ Navigate</span>
            <span>↵ Select</span>
            <span>ESC Close</span>
          </div>
          <span className="font-mono text-cyan-400">⌘K Command Palette</span>
        </div>
      </div>
    </div>
  );
};
