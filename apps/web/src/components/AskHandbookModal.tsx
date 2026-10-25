import React, { useState } from 'react';
import { Kosh } from '../design-system/Kosh';
import { apiFetch, ProblemError } from '../lib/apiFetch';
import { Sparkles, Send, X, BookOpen, CheckCircle2, AlertCircle } from 'lucide-react';

interface AskHandbookModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface SourceClause {
  clause_id: string;
  title: string;
  distance: number;
  synthetic_placeholder: boolean;
}

interface PolicyQAResponse {
  answer: string;
  refused: boolean;
  unavailable: boolean;
  verified_citations: string[];
  sources: SourceClause[];
}

const SAMPLE_QUESTIONS = [
  'What is the penalty for delayed submission of security deposit?',
  'What is the validity period or tenure required for an FDR?',
  'Can an institution prematurely withdraw or encash the FDR?',
  'Is a joint account required with AICTE Regional Officer?',
];

export const AskHandbookModal: React.FC<AskHandbookModalProps> = ({ isOpen, onClose }) => {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<PolicyQAResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleAsk = async (questionText?: string) => {
    const q = questionText || query;
    if (!q.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);
    setResponse(null);

    try {
      const data = await apiFetch<PolicyQAResponse>('/v1/ai/policy-qa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q.trim() }),
      });
      setResponse(data);
    } catch (err) {
      if (err instanceof ProblemError) {
        setError(err.problem?.detail || err.message || 'Service temporarily unavailable');
      } else {
        setError('Failed to query Approval Process Handbook. Check your connection.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
        background: 'rgba(15, 23, 42, 0.45)',
        backdropFilter: 'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)',
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="card"
        style={{
          width: '100%',
          maxWidth: '580px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          background: 'var(--surface)',
          borderRadius: '28px',
          boxShadow: '0 20px 48px rgba(35, 40, 110, 0.22)',
          padding: 0,
          overflow: 'hidden',
          border: 'none',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Grabber & Close */}
        <div style={{ padding: '16px 20px 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ width: 40, height: 4, borderRadius: 2, background: 'var(--field-strong)', margin: '0 auto' }} />
          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-3)',
              padding: 4,
            }}
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '16px 24px 28px', overflowY: 'auto' }}>
          {/* Header with Kosh Mascot (matching ui-refrence.png screen 6) */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: '12px' }}>
            <div style={{ filter: 'drop-shadow(0 10px 20px rgba(59, 120, 216, 0.22))' }}>
              <Kosh pose="wow" size={84} />
            </div>
            <h2
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: '20px',
                fontWeight: 800,
                color: 'var(--text1)',
                lineHeight: 1.3,
                maxWidth: '420px',
                margin: 0,
              }}
            >
              Ask me about the Approval Process Handbook. I always show the clause.
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text2)', margin: 0, fontWeight: 500 }}>
              AICTE Regulatory AI Copilot (Groq + OpenRouter Bounded Gateway)
            </p>
          </div>

          {/* Quick Prompts */}
          <div style={{ marginTop: '16px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {SAMPLE_QUESTIONS.map((sq) => (
              <button
                key={sq}
                type="button"
                onClick={() => {
                  setQuery(sq);
                  handleAsk(sq);
                }}
                className="chip"
                style={{
                  fontSize: '12px',
                  fontWeight: 600,
                  padding: '6px 12px',
                  borderRadius: '999px',
                  background: 'var(--field)',
                  color: 'var(--text2)',
                  border: 'none',
                  cursor: 'pointer',
                  textAlign: 'left',
                }}
              >
                {sq}
              </button>
            ))}
          </div>

          {/* Input Box */}
          <div style={{ marginTop: '16px', display: 'flex', gap: '10px', alignItems: 'center' }}>
            <div
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: 'var(--field)',
                borderRadius: '999px',
                padding: '0 16px',
                height: '48px',
              }}
            >
              <BookOpen size={18} color="var(--azure)" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleAsk();
                }}
                placeholder="Ask any APH compliance clause question..."
                style={{
                  flex: 1,
                  background: 'transparent',
                  border: 'none',
                  outline: 'none',
                  fontSize: '14px',
                  fontWeight: 600,
                  color: 'var(--text1)',
                  fontFamily: 'inherit',
                }}
              />
            </div>
            <button
              type="button"
              onClick={() => handleAsk()}
              disabled={isLoading || !query.trim()}
              className="btn btn-primary"
              style={{
                height: '48px',
                padding: '0 20px',
                borderRadius: '999px',
                background: 'var(--ink)',
                color: 'var(--on-ink)',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '14px',
                fontWeight: 700,
              }}
            >
              {isLoading ? (
                <div style={{ width: 16, height: 16, border: '2px solid #fff', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.6s linear infinite' }} />
              ) : (
                <>
                  <Send size={15} />
                  Ask
                </>
              )}
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div
              style={{
                marginTop: '16px',
                padding: '12px 16px',
                borderRadius: '16px',
                background: 'var(--danger-container)',
                color: 'var(--on-danger-container)',
                fontSize: '13px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          {/* AI Response Card */}
          {response && (
            <div
              style={{
                marginTop: '20px',
                padding: '18px',
                background: 'var(--canvas)',
                borderRadius: '20px',
                border: '1px solid var(--hairline)',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
              }}
            >
              {/* Citations Bar */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <CheckCircle2 size={16} color="var(--ok)" />
                  <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--ok)' }}>
                    Verified against Approval Process Handbook
                  </span>
                </div>
                {response.verified_citations.map((c) => (
                  <span
                    key={c}
                    className="pill pill-ok"
                    style={{
                      fontSize: '11px',
                      fontWeight: 800,
                      padding: '4px 10px',
                      borderRadius: '999px',
                      background: 'var(--ok-container)',
                      color: 'var(--on-ok-container)',
                    }}
                  >
                    {c}
                  </span>
                ))}
              </div>

              {/* Answer Content */}
              <div
                style={{
                  fontSize: '14px',
                  lineHeight: '1.6',
                  color: 'var(--text1)',
                  fontWeight: 500,
                }}
              >
                {response.answer}
              </div>

              {/* Retrieved Source Clauses Details */}
              {response.sources && response.sources.length > 0 && (
                <div style={{ borderTop: '1px solid var(--hairline)', paddingTop: '12px', marginTop: '4px' }}>
                  <div style={{ fontSize: '11px', fontWeight: 800, textTransform: 'uppercase', color: 'var(--text3)', letterSpacing: '0.04em' }}>
                    Matched Source Clauses
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '6px' }}>
                    {response.sources.map((s) => (
                      <div
                        key={s.clause_id}
                        style={{
                          padding: '8px 12px',
                          background: 'var(--surface)',
                          borderRadius: '12px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          fontSize: '12px',
                        }}
                      >
                        <span style={{ fontWeight: 700, color: 'var(--azure)' }}>
                          {s.clause_id}: {s.title}
                        </span>
                        <span style={{ fontSize: '11px', color: 'var(--text3)', fontWeight: 600 }}>
                          Distance: {s.distance.toFixed(4)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
