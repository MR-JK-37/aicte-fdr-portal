import React from 'react';
import { Clock, Play, RotateCcw, Calendar, ArrowRight, Zap } from 'lucide-react';

interface SimClockControlProps {
  isOpen: boolean;
  onClose: () => void;
  offsetDays: number;
  onSetOffset: (days: number) => void;
  simDate: string;
}

export const SimClockControl: React.FC<SimClockControlProps> = ({
  isOpen,
  onClose,
  offsetDays,
  onSetOffset,
  simDate,
}) => {
  if (!isOpen) return null;

  const jumps = [
    { label: 'Real Time (0d)', days: 0, desc: 'Live wall-clock' },
    { label: '+30 Days (T-60)', days: 30, desc: 'Fires T-60 Reminder Window' },
    { label: '+60 Days (T-30)', days: 60, desc: 'Critical T-30 Window + In-App AI Call' },
    { label: '+83 Days (T-7)', days: 83, desc: 'Final Urgent T-7 Window' },
    { label: '+300 Days (Matured)', days: 300, desc: 'Full ladder fires; ACTIVE → MATURED' },
  ];

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0, 0, 0, 0.7)', backdropFilter: 'blur(8px)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px' }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '520px', padding: '24px', border: '1px solid var(--border-glow-cyan)', boxShadow: 'var(--shadow-cyan-glow)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: 36, height: 36, borderRadius: 8, background: 'rgba(245, 158, 11, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Clock size={20} color="#fbbf24" />
            </div>
            <div>
              <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '18px', fontWeight: 600 }}>Simulation Clock (Time Travel)</h3>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Per brief acceptance test: jump forward without waiting real months</p>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: '18px', cursor: 'pointer' }}>✕</button>
        </div>

        {/* Current Time Display */}
        <div style={{ background: 'rgba(0, 0, 0, 0.4)', borderRadius: 12, padding: '16px', marginBottom: '20px', border: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', fontWeight: 600 }}>
              Simulated System Date
            </div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: '20px', fontWeight: 700, color: '#38bdf8', marginTop: '4px' }}>
              {simDate}
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
              Stored Offset
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '16px', fontWeight: 700, color: offsetDays > 0 ? '#fbbf24' : '#10b981', marginTop: '4px' }}>
              +{offsetDays} Days
            </div>
          </div>
        </div>

        {/* Preset Jumps */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
          {jumps.map((jump) => (
            <button
              key={jump.days}
              onClick={() => {
                onSetOffset(jump.days);
                onClose();
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 16px',
                borderRadius: 10,
                background: offsetDays === jump.days ? 'rgba(6, 182, 212, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                border: offsetDays === jump.days ? '1px solid rgba(6, 182, 212, 0.5)' : '1px solid var(--border-glass)',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.15s ease',
              }}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: '14px', color: offsetDays === jump.days ? '#22d3ee' : 'var(--text-primary)' }}>
                  {jump.label}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  {jump.desc}
                </div>
              </div>
              <ArrowRight size={16} color={offsetDays === jump.days ? '#22d3ee' : 'var(--text-muted)'} />
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <button
            onClick={() => {
              onSetOffset(0);
              onClose();
            }}
            className="btn-secondary"
          >
            <RotateCcw size={14} />
            <span>Reset to Live Clock</span>
          </button>
          <button onClick={onClose} className="btn-primary">
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
