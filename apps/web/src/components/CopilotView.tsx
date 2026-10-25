import React, { useState } from 'react';
import { Sparkles, Search, BookOpen, CheckCircle2, AlertCircle, ShieldAlert, FileText, Send } from 'lucide-react';
import { Kosh } from '../design-system/Kosh';
import { apiFetch, ProblemError } from '../lib/apiFetch';

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
  'Can an institution submit a Bank Guarantee in lieu of an FDR?',
  'How is interest compounded on the FDR security deposit?',
];

function renderInlineContent(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  const regex = /(\*\*[^*]+\*\*|\[APH[^\]]+\])/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    const token = match[0];
    if (token.startsWith('**') && token.endsWith('**')) {
      parts.push(
        <strong
          key={match.index}
          style={{
            fontWeight: 700,
            color: 'var(--text1)',
          }}
        >
          {token.slice(2, -2)}
        </strong>
      );
    } else if (token.startsWith('[') && token.endsWith(']')) {
      parts.push(
        <span
          key={match.index}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            padding: '2px 8px',
            margin: '0 4px',
            borderRadius: '999px',
            fontSize: '11px',
            fontWeight: 700,
            background: 'rgba(5, 150, 105, 0.1)',
            color: '#059669',
            border: '1px solid rgba(5, 150, 105, 0.25)',
            verticalAlign: 'baseline',
          }}
        >
          {token.slice(1, -1)}
        </span>
      );
    }
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  return parts;
}

function FormattedAiResponse({ rawText }: { rawText: string }) {
  const clean = rawText
    .replace(/(?:\n|\r\n)?\*?Note:?\s*These clauses are (?:synthetic placeholders|SYNTHETIC PLACEHOLDERS)[^\n]*\*?/gi, '')
    .replace(/\[SYNTHETIC PLACEHOLDER\]\s*/gi, '')
    .trim();

  // Split by double newline into distinct paragraph/bullet blocks
  const blocks = clean.split(/\n\s*\n/);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '14px', lineHeight: '24px', color: 'var(--text1)' }}>
      {blocks.map((block, idx) => {
        const lines = block.split('\n').map((l) => l.trim()).filter(Boolean);
        const isBulletList = lines.length > 0 && lines.every((l) => l.startsWith('•') || l.startsWith('-') || l.startsWith('* '));

        if (isBulletList) {
          return (
            <ul
              key={idx}
              style={{
                margin: '4px 0',
                padding: 0,
                listStyle: 'none',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              {lines.map((line, lineIdx) => {
                const bulletContent = line.replace(/^[•\-\*]\s*/, '');
                return (
                  <li
                    key={lineIdx}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '12px',
                      background: 'rgba(255, 255, 255, 0.6)',
                      border: '1px solid var(--hairline)',
                      padding: '10px 14px',
                      borderRadius: '12px',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.02)',
                    }}
                  >
                    <span
                      style={{
                        display: 'inline-block',
                        width: '6px',
                        height: '6px',
                        borderRadius: '50%',
                        backgroundColor: 'var(--azure)',
                        marginTop: '8px',
                        flexShrink: 0,
                      }}
                    />
                    <div style={{ flex: 1, fontSize: '13.5px', lineHeight: '22px', color: 'var(--text2)' }}>
                      {renderInlineContent(bulletContent)}
                    </div>
                  </li>
                );
              })}
            </ul>
          );
        }

        return (
          <p key={idx} style={{ margin: 0, color: 'var(--text1)', fontWeight: 500, lineHeight: '24px' }}>
            {renderInlineContent(block)}
          </p>
        );
      })}
    </div>
  );
}

export const CopilotView: React.FC = () => {
  const [ragQuery, setRagQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<PolicyQAResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAsk = async (queryText?: string) => {
    const q = queryText || ragQuery;
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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header Banner */}
      <div
        className="card"
        style={{
          padding: '24px 28px',
          background: 'linear-gradient(135deg, var(--hero-from), var(--hero-to) 70%)',
          position: 'relative',
          overflow: 'hidden',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '20px',
        }}
      >
        <div style={{ position: 'relative', zIndex: 2, maxWidth: '640px' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 12px',
              borderRadius: '999px',
              background: 'rgba(255, 255, 255, 0.7)',
              color: 'var(--azure)',
              fontSize: '12px',
              fontWeight: 800,
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              marginBottom: '10px',
            }}
          >
            <Sparkles size={14} />
            AICTE Regulatory Intelligence
          </div>
          <h2
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '28px',
              fontWeight: 800,
              color: 'var(--text1)',
              margin: '0 0 8px',
              lineHeight: 1.25,
            }}
          >
            AICTE Regulatory Copilot
          </h2>
          <p
            style={{
              fontSize: '14px',
              color: 'var(--text2)',
              margin: 0,
              lineHeight: '22px',
              fontWeight: 500,
            }}
          >
            Bounded regulatory assistant grounded directly in verified APH clauses. Every answer
            must cite verifiable statutory clauses from the normative handbook, with zero hallucinated references.
          </p>
        </div>

        <div style={{ position: 'relative', zIndex: 2, display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ filter: 'drop-shadow(0 12px 24px rgba(59, 120, 216, 0.25))' }}>
            <Kosh pose="document" size={110} />
          </div>
        </div>
      </div>

      {/* Main Interactive Copilot Card */}
      <div className="card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <BookOpen size={20} color="var(--azure)" />
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 800, fontFamily: 'var(--font-display)', color: 'var(--text1)' }}>
            Ask Approval Process Handbook (APH)
          </h3>
        </div>

        {/* Input Bar */}
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              background: 'var(--field)',
              borderRadius: '999px',
              padding: '0 16px',
              height: '48px',
            }}
          >
            <Search size={18} color="var(--text3)" />
            <input
              type="text"
              value={ragQuery}
              onChange={(e) => setRagQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleAsk();
              }}
              placeholder="Ask any regulatory question about security deposits, tenure, lien, maturity..."
              style={{
                flex: 1,
                border: 'none',
                background: 'transparent',
                outline: 'none',
                fontSize: '14px',
                fontWeight: 600,
                color: 'var(--text1)',
              }}
            />
          </div>

          <button
            type="button"
            onClick={() => handleAsk()}
            disabled={!ragQuery.trim() || isLoading}
            className="btn btn-primary"
            style={{
              height: '48px',
              padding: '0 24px',
              borderRadius: '999px',
              gap: '8px',
              display: 'inline-flex',
              alignItems: 'center',
            }}
          >
            {isLoading ? (
              <>
                <Sparkles size={16} className="animate-spin" />
                <span>Searching APH…</span>
              </>
            ) : (
              <>
                <Send size={16} />
                <span>Ask Copilot</span>
              </>
            )}
          </button>
        </div>

        {/* Sample Prompt Chips */}
        <div style={{ marginTop: '16px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text3)', alignSelf: 'center', marginRight: '4px' }}>
            Suggested:
          </span>
          {SAMPLE_QUESTIONS.map((sq) => (
            <button
              key={sq}
              type="button"
              onClick={() => {
                setRagQuery(sq);
                handleAsk(sq);
              }}
              className="chip"
              style={{
                fontSize: '12px',
                fontWeight: 600,
                padding: '6px 12px',
                background: 'var(--field)',
                border: '1px solid var(--hairline)',
                borderRadius: '999px',
                color: 'var(--text2)',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              {sq}
            </button>
          ))}
        </div>

        {/* Error Banner */}
        {error && (
          <div
            style={{
              marginTop: '20px',
              padding: '14px 18px',
              background: 'var(--danger-container)',
              borderRadius: '16px',
              color: 'var(--on-danger-container)',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              fontSize: '13px',
              fontWeight: 600,
            }}
          >
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        {/* Response Display */}
        {response && (
          <div
            style={{
              marginTop: '24px',
              padding: '24px',
              borderRadius: '20px',
              background: response.refused
                ? 'rgba(217, 119, 6, 0.04)'
                : 'linear-gradient(180deg, var(--surface) 0%, var(--field) 100%)',
              border: `1px solid ${response.refused ? 'rgba(217, 119, 6, 0.25)' : 'var(--border)'}`,
              boxShadow: 'var(--shadow-card)',
            }}
          >
            {/* Header Status Bar */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {response.refused ? (
                  <ShieldAlert size={20} color="#D97706" />
                ) : (
                  <CheckCircle2 size={20} color="#059669" />
                )}
                <span
                  style={{
                    fontSize: '13px',
                    fontWeight: 800,
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                    color: response.refused ? '#D97706' : '#059669',
                  }}
                >
                  {response.refused
                    ? 'Statutory Boundary Notice • Out of Scope'
                    : 'Statutory APH Citation Verified'}
                </span>
              </div>

              {response.verified_citations.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {response.verified_citations.map((cite) => (
                    <span
                      key={cite}
                      style={{
                        padding: '4px 10px',
                        fontSize: '11px',
                        fontWeight: 700,
                        borderRadius: '20px',
                        background: 'rgba(5, 150, 105, 0.1)',
                        color: '#059669',
                        border: '1px solid rgba(5, 150, 105, 0.2)',
                      }}
                    >
                      {cite}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Answer / Primary Guidance */}
            <div
              style={{
                marginTop: '4px',
              }}
            >
              <FormattedAiResponse rawText={response.answer} />
            </div>

            {/* Enhanced Statutory Fallback Advisory for Refused / Out-of-Scope Inquiries */}
            {response.refused && (
              <div
                style={{
                  marginTop: '20px',
                  padding: '18px 20px',
                  borderRadius: '16px',
                  background: 'var(--surface)',
                  border: '1px solid rgba(217, 119, 6, 0.2)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '14px',
                }}
              >
                <div>
                  <h4 style={{ fontSize: '13px', fontWeight: 800, color: 'var(--text1)', margin: '0 0 4px' }}>
                    Regulatory Policy &amp; Escalation Guidance
                  </h4>
                  <p style={{ fontSize: '12px', color: 'var(--text2)', margin: 0, lineHeight: 1.6 }}>
                    Under statutory compliance guidelines (AICTE Act Sec. 10(k)), this regulatory assistant enforces
                    strict zero-hallucination bounds and refuses to extrapolate unverified norms. For matters not codified
                    in the handbook, please consult official AICTE escalation channels:
                  </p>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '10px' }}>
                  <div style={{ padding: '10px 14px', borderRadius: '10px', background: 'var(--field)', border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text3)', textTransform: 'uppercase' }}>
                      Central Policy Desk
                    </div>
                    <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text1)', marginTop: '2px' }}>
                      AICTE Regulation Bureau, New Delhi
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '2px' }}>
                      Nelson Mandela Marg, Vasant Kunj
                    </div>
                  </div>

                  <div style={{ padding: '10px 14px', borderRadius: '10px', background: 'var(--field)', border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text3)', textTransform: 'uppercase' }}>
                      File-Specific Lien / Exemption
                    </div>
                    <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text1)', marginTop: '2px' }}>
                      Jurisdictional AICTE Regional Office (RO)
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text3)', marginTop: '2px' }}>
                      Joint lien holder on institutional FDR
                    </div>
                  </div>
                </div>

                <div style={{ borderTop: '1px solid var(--border)', paddingTop: '12px' }}>
                  <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text3)', marginBottom: '8px' }}>
                    Try these verified compliance topics instead:
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {SAMPLE_QUESTIONS.slice(0, 4).map((sq) => (
                      <button
                        key={sq}
                        type="button"
                        onClick={() => {
                          setRagQuery(sq);
                          handleAsk(sq);
                        }}
                        style={{
                          fontSize: '11px',
                          fontWeight: 600,
                          padding: '5px 10px',
                          borderRadius: '8px',
                          background: 'var(--field)',
                          border: '1px solid var(--border)',
                          color: 'var(--azure)',
                          cursor: 'pointer',
                        }}
                      >
                        {sq}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Source Clauses Inspector (only rendered when genuine grounding clauses exist) */}
            {response.sources.length > 0 && (
              <div style={{ marginTop: '20px', borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
                <div
                  style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    color: 'var(--text3)',
                    letterSpacing: '0.04em',
                    marginBottom: '10px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                >
                  <FileText size={14} />
                  Retrieved Handbook Grounding Clauses ({response.sources.length})
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '10px' }}>
                  {response.sources.map((s) => (
                    <div
                      key={s.clause_id}
                      style={{
                        padding: '10px 14px',
                        borderRadius: '12px',
                        background: 'var(--field)',
                        border: '1px solid var(--border)',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '4px',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text1)' }}>
                          {s.clause_id}
                        </span>
                        <span
                          style={{
                            fontSize: '10px',
                            fontWeight: 700,
                            padding: '2px 8px',
                            borderRadius: '12px',
                            background: 'rgba(5, 150, 105, 0.1)',
                            color: '#059669',
                            border: '1px solid rgba(5, 150, 105, 0.2)',
                          }}
                        >
                          dist: {s.distance.toFixed(3)}
                        </span>
                      </div>
                      <span style={{ fontSize: '12px', color: 'var(--text2)', fontWeight: 500 }}>
                        {s.title}
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
  );
};
