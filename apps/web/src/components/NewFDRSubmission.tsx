import React, { useState } from 'react';
import { UploadCloud, Sparkles, CheckCircle2, AlertTriangle, Loader2 } from 'lucide-react';
import { api } from '../lib/apiClient';
import { useAuth } from '../auth/AuthContext';

interface NewFDRSubmissionProps {
  lang: string;
}

type StepStatus = 'idle' | 'running' | 'done' | 'error';

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '10px 12px',
  borderRadius: '10px',
  border: '1px solid var(--border)',
  background: 'var(--surface)',
  color: 'var(--text1)',
  fontSize: '13px',
  boxSizing: 'border-box',
};

const labelStyle: React.CSSProperties = {
  fontSize: '12px',
  fontWeight: 700,
  color: 'var(--text2)',
  marginBottom: '4px',
  display: 'block',
};

export const NewFDRSubmission: React.FC<NewFDRSubmissionProps> = ({ lang }) => {
  const { user } = useAuth();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const [instrumentNumber, setInstrumentNumber] = useState('');
  const [amount, setAmount] = useState('');
  const [issueDate, setIssueDate] = useState('');
  const [maturityDate, setMaturityDate] = useState('');

  const [draftStatus, setDraftStatus] = useState<StepStatus>('idle');
  const [uploadStatus, setUploadStatus] = useState<StepStatus>('idle');
  const [extractStatus, setExtractStatus] = useState<StepStatus>('idle');
  const [submitStatus, setSubmitStatus] = useState<StepStatus>('idle');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [instrumentId, setInstrumentId] = useState<string | null>(null);
  const [candidateFields, setCandidateFields] = useState<Record<string, unknown> | null>(null);
  const [extractionEngine, setExtractionEngine] = useState<string | null>(null);

  const t = {
    en: {
      title: 'New FDR Submission',
      subtitle:
        'Create the instrument record, upload the scanned FDR copy, and let the document pipeline (virus scan, duplicate check, OCR) run before submitting for scrutiny.',
      dropLabel: 'Drag and drop FDR PDF or scanned image (max 15MB)',
      selectFile: 'Choose file',
      instrumentNumber: 'FDR / Instrument number',
      amount: 'Amount (INR)',
      issueDate: 'Issue date',
      maturityDate: 'Maturity date',
      createAndUpload: 'Create instrument & upload document',
      submitForScrutiny: 'Submit for scrutiny',
      noInstitution: 'Your account has no institution assigned. An institution-scoped role is required to submit an FDR.',
      stepDraft: 'Creating instrument record',
      stepUpload: 'Uploading & scanning document',
      stepExtract: 'Running OCR / AI field extraction',
      extractedFieldsTitle: 'AI-extracted candidate fields: verify against the record',
      extractedNone: 'No candidate fields were extracted from this document (OCR may be unavailable, or the scan is unreadable). This never blocks manual entry.',
      submitted: 'Submitted for scrutiny. Track status from the dashboard.',
    },
    hi: {
      title: 'नया एफडीआर प्रस्तुतीकरण',
      subtitle: 'इंस्ट्रूमेंट रिकॉर्ड बनाएं, स्कैन की गई एफडीआर प्रति अपलोड करें, और समीक्षा हेतु सबमिट करने से पहले दस्तावेज़ पाइपलाइन चलने दें।',
      dropLabel: 'एफडीआर पीडीएफ या स्कैन की गई छवि यहाँ खींचें',
      selectFile: 'फ़ाइल चुनें',
      instrumentNumber: 'एफडीआर / इंस्ट्रूमेंट संख्या',
      amount: 'राशि (INR)',
      issueDate: 'जारी करने की तिथि',
      maturityDate: 'परिपक्वता तिथि',
      createAndUpload: 'इंस्ट्रूमेंट बनाएं और दस्तावेज़ अपलोड करें',
      submitForScrutiny: 'जांच हेतु सबमिट करें',
      noInstitution: 'आपके खाते में कोई संस्थान निर्दिष्ट नहीं है।',
      stepDraft: 'इंस्ट्रूमेंट रिकॉर्ड बनाया जा रहा है',
      stepUpload: 'दस्तावेज़ अपलोड और स्कैन हो रहा है',
      stepExtract: 'OCR / AI फ़ील्ड निष्कर्षण चल रहा है',
      extractedFieldsTitle: 'AI द्वारा निकाले गए संभावित फ़ील्ड: रिकॉर्ड से सत्यापित करें',
      extractedNone: 'इस दस्तावेज़ से कोई फ़ील्ड नहीं निकाली जा सकी। मैन्युअल प्रविष्टि अभी भी उपलब्ध है।',
      submitted: 'जांच हेतु सबमिट किया गया।',
    },
    ta: {
      title: 'புதிய FDR சமர்ப்பிப்பு',
      subtitle: 'இன்ஸ்ட்ரூமென்ட் பதிவை உருவாக்கி, ஸ்கேன் செய்யப்பட்ட FDR நகலை பதிவேற்றி, ஆவண செயலாக்கம் முடிந்தபின் சமர்ப்பிக்கவும்.',
      dropLabel: 'FDR PDF அல்லது ஸ்கேன் செய்யப்பட்ட படத்தை பதிவேற்றவும்',
      selectFile: 'கோப்பைத் தேர்ந்தெடுங்கள்',
      instrumentNumber: 'FDR / இன்ஸ்ட்ரூமென்ட் எண்',
      amount: 'தொகை (INR)',
      issueDate: 'வழங்கிய தேதி',
      maturityDate: 'முதிர்வு தேதி',
      createAndUpload: 'இன்ஸ்ட்ரூமென்ட் உருவாக்கி பதிவேற்றவும்',
      submitForScrutiny: 'பரிசீலனைக்கு சமர்ப்பிக்கவும்',
      noInstitution: 'உங்கள் கணக்கில் நிறுவனம் ஒதுக்கப்படவில்லை.',
      stepDraft: 'இன்ஸ்ட்ரூமென்ட் பதிவு உருவாக்கப்படுகிறது',
      stepUpload: 'ஆவணம் பதிவேற்றப்பட்டு ஸ்கேன் செய்யப்படுகிறது',
      stepExtract: 'OCR / AI புல எக்ஸ்ட்ராக்ஷன் இயங்குகிறது',
      extractedFieldsTitle: 'AI-யால் பிரித்தெடுக்கப்பட்ட புலங்கள்: பதிவுடன் சரிபார்க்கவும்',
      extractedNone: 'இந்த ஆவணத்தில் இருந்து எந்த புலமும் பிரித்தெடுக்கப்படவில்லை.',
      submitted: 'பரிசீலனைக்கு சமர்ப்பிக்கப்பட்டது.',
    },
  }[lang as 'en' | 'hi' | 'ta'] || {
    title: 'New FDR Submission',
    subtitle: 'Upload a scanned FDR copy.',
    dropLabel: 'Drag and drop FDR PDF',
    selectFile: 'Choose file',
    instrumentNumber: 'FDR / Instrument number',
    amount: 'Amount (INR)',
    issueDate: 'Issue date',
    maturityDate: 'Maturity date',
    createAndUpload: 'Create instrument & upload document',
    submitForScrutiny: 'Submit for scrutiny',
    noInstitution: 'No institution assigned.',
    stepDraft: 'Creating instrument record',
    stepUpload: 'Uploading & scanning document',
    stepExtract: 'Running OCR / AI field extraction',
    extractedFieldsTitle: 'AI-extracted candidate fields',
    extractedNone: 'No candidate fields extracted.',
    submitted: 'Submitted for scrutiny.',
  };

  const canSubmit =
    !!user?.institution_id &&
    instrumentNumber.trim().length >= 3 &&
    !!amount &&
    Number(amount) > 0 &&
    draftStatus !== 'running' &&
    uploadStatus !== 'running';

  const handleCreateAndUpload = async () => {
    setErrorMessage(null);
    setCandidateFields(null);
    if (!user?.institution_id) {
      setErrorMessage(t.noInstitution);
      return;
    }

    setDraftStatus('running');
    const { data: instrument, error: draftError } = await api.POST('/v1/instruments/draft', {
      body: {
        institution_id: user.institution_id,
        type: 'FDR',
        instrument_number: instrumentNumber.trim(),
        amount: Number(amount),
        issue_date: issueDate ? new Date(issueDate).toISOString() : null,
        maturity_date: maturityDate ? new Date(maturityDate).toISOString() : null,
      },
    });
    if (draftError || !instrument) {
      setDraftStatus('error');
      setErrorMessage(extractErrorMessage(draftError, 'Could not create the instrument record.'));
      return;
    }
    setDraftStatus('done');
    setInstrumentId(instrument.id);

    if (!selectedFile) {
      return;
    }

    setUploadStatus('running');
    // openapi-fetch only switches to multipart/form-data encoding for a body
    // that is already a `FormData` instance — a plain `{ file: selectedFile }`
    // object gets JSON-serialised (losing the File entirely), which is why
    // the backend saw `file` as missing. Building the FormData ourselves
    // keeps this call fully typed for params/response while still getting
    // the right wire encoding for the body.
    const formData = new FormData();
    formData.append('file', selectedFile);
    const { data: document, error: uploadError } = await api.POST('/v1/documents/upload-direct', {
      params: {
        query: {
          instrument_id: instrument.id,
          declared_mime_type: selectedFile.type || 'application/pdf',
        },
      },
      body: formData as unknown as { file: string },
      bodySerializer: (body) => body as unknown as BodyInit,
    });
    if (uploadError || !document) {
      setUploadStatus('error');
      setErrorMessage(extractErrorMessage(uploadError, 'Upload was rejected (virus scan, magic-byte check, or size limit).'));
      return;
    }
    setUploadStatus('done');

    setExtractStatus('running');
    const { data: extraction, error: extractError } = await api.POST(
      '/v1/documents/{document_id}/extract',
      { params: { path: { document_id: document.id } } }
    );
    if (extractError || !extraction) {
      setExtractStatus('error');
      setErrorMessage(extractErrorMessage(extractError, 'OCR/AI extraction did not complete.'));
      return;
    }
    setExtractStatus('done');
    setExtractionEngine(extraction.engine);
    setCandidateFields(extraction.candidate_fields ?? {});
  };

  const handleSubmitForScrutiny = async () => {
    if (!instrumentId) return;
    setSubmitStatus('running');
    const { error } = await api.POST('/v1/instruments/{instrument_id}/submit', {
      params: { path: { instrument_id: instrumentId } },
      body: {
        reason: 'Institution submission via Submit FDR screen',
        policy_version: 'APH-2024-27-v1.0',
      },
    });
    if (error) {
      setSubmitStatus('error');
      setErrorMessage(extractErrorMessage(error, 'Could not submit for scrutiny.'));
      return;
    }
    setSubmitStatus('done');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '24px', padding: '32px', boxShadow: 'var(--shadow-card)' }}>
        <h2
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '22px',
            fontWeight: 800,
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            color: 'var(--text1)',
          }}
        >
          <Sparkles size={22} color="var(--azure)" />
          {t.title}
        </h2>
        <p style={{ fontSize: '13px', color: 'var(--text3)', marginTop: '4px' }}>{t.subtitle}</p>

        {!user?.institution_id && (
          <div style={{ marginTop: '16px', padding: '12px 16px', borderRadius: '12px', background: '#FEF2F2', color: '#991B1B', fontSize: '13px' }}>
            {t.noInstitution}
          </div>
        )}

        <div style={{ marginTop: '24px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <label style={labelStyle}>{t.instrumentNumber}</label>
            <input
              style={inputStyle}
              value={instrumentNumber}
              onChange={(e) => setInstrumentNumber(e.target.value)}
              placeholder="SBI/2026/00123"
              disabled={draftStatus === 'done'}
            />
          </div>
          <div>
            <label style={labelStyle}>{t.amount}</label>
            <input
              style={inputStyle}
              type="number"
              min="0"
              step="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="3500000"
              disabled={draftStatus === 'done'}
            />
          </div>
          <div>
            <label style={labelStyle}>{t.issueDate}</label>
            <input
              style={inputStyle}
              type="date"
              value={issueDate}
              onChange={(e) => setIssueDate(e.target.value)}
              disabled={draftStatus === 'done'}
            />
          </div>
          <div>
            <label style={labelStyle}>{t.maturityDate}</label>
            <input
              style={inputStyle}
              type="date"
              value={maturityDate}
              onChange={(e) => setMaturityDate(e.target.value)}
              disabled={draftStatus === 'done'}
            />
          </div>
        </div>

        <div
          style={{
            marginTop: '24px',
            border: '2px dashed #CBD5E1',
            borderRadius: '20px',
            padding: '40px 24px',
            textAlign: 'center',
            background: 'var(--field)',
          }}
        >
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: '50%',
              background: '#FFFFFF',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 14px auto',
              boxShadow: '0 4px 14px rgba(0,0,0,0.06)',
            }}
          >
            <UploadCloud size={26} color="var(--azure)" />
          </div>
          <h4 style={{ fontFamily: 'var(--font-display)', fontSize: '15px', fontWeight: 700, color: 'var(--text1)' }}>
            {t.dropLabel}
          </h4>
          <p style={{ fontSize: '12px', color: 'var(--text3)', marginTop: '4px' }}>PDF, TIFF, JPEG (Max 15MB)</p>
          <label
            style={{
              marginTop: '14px',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '10px 22px',
              borderRadius: '9999px',
              background: 'var(--ink)',
              color: '#FFFFFF',
              fontSize: '13px',
              fontWeight: 700,
              cursor: draftStatus === 'done' ? 'not-allowed' : 'pointer',
              opacity: draftStatus === 'done' ? 0.5 : 1,
              border: 'none',
            }}
          >
            {t.selectFile}
            <input
              type="file"
              accept="application/pdf,image/*"
              style={{ display: 'none' }}
              disabled={draftStatus === 'done'}
              onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
            />
          </label>
          {selectedFile && (
            <p style={{ marginTop: '10px', fontSize: '12px', color: 'var(--text2)', fontWeight: 600 }}>
              {selectedFile.name}
            </p>
          )}
        </div>

        {errorMessage && (
          <div style={{ marginTop: '16px', padding: '12px 16px', borderRadius: '12px', background: '#FEF2F2', color: '#991B1B', fontSize: '13px', display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
            <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
            <span>{errorMessage}</span>
          </div>
        )}

        {draftStatus !== 'idle' && (
          <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <StepRow label={t.stepDraft} status={draftStatus} />
            {selectedFile && <StepRow label={t.stepUpload} status={uploadStatus} />}
            {selectedFile && <StepRow label={t.stepExtract} status={extractStatus} />}
          </div>
        )}

        {candidateFields !== null && (
          <div style={{ marginTop: '16px', padding: '16px', borderRadius: '14px', background: '#F1F5F9', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text1)', marginBottom: '8px' }}>
              {t.extractedFieldsTitle}
              {extractionEngine && (
                <span style={{ fontWeight: 500, color: 'var(--text3)' }}> · engine: {extractionEngine}</span>
              )}
            </div>
            {Object.keys(candidateFields).length === 0 ? (
              <p style={{ fontSize: '12px', color: 'var(--text3)' }}>{t.extractedNone}</p>
            ) : (
              <dl style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 16px', margin: 0 }}>
                {Object.entries(candidateFields).map(([key, value]) => (
                  <React.Fragment key={key}>
                    <dt style={{ fontSize: '12px', color: 'var(--text3)' }}>{key}</dt>
                    <dd style={{ fontSize: '12px', color: 'var(--text1)', fontWeight: 600, margin: 0 }}>
                      {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                    </dd>
                  </React.Fragment>
                ))}
              </dl>
            )}
          </div>
        )}

        <div style={{ marginTop: '24px', display: 'flex', gap: '12px' }}>
          {draftStatus !== 'done' ? (
            <button
              type="button"
              onClick={handleCreateAndUpload}
              disabled={!canSubmit}
              style={{
                padding: '12px 24px',
                borderRadius: '9999px',
                background: canSubmit ? 'var(--ink)' : '#CBD5E1',
                color: '#FFFFFF',
                fontSize: '14px',
                fontWeight: 700,
                border: 'none',
                cursor: canSubmit ? 'pointer' : 'not-allowed',
              }}
            >
              {draftStatus === 'running' || uploadStatus === 'running' || extractStatus === 'running' ? (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                  <Loader2 size={14} className="spin" /> …
                </span>
              ) : (
                t.createAndUpload
              )}
            </button>
          ) : submitStatus === 'done' ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#15803D', fontSize: '13px', fontWeight: 700 }}>
              <CheckCircle2 size={18} /> {t.submitted}
            </div>
          ) : (
            <button
              type="button"
              onClick={handleSubmitForScrutiny}
              disabled={submitStatus === 'running'}
              style={{
                padding: '12px 24px',
                borderRadius: '9999px',
                background: 'var(--ink)',
                color: '#FFFFFF',
                fontSize: '14px',
                fontWeight: 700,
                border: 'none',
                cursor: submitStatus === 'running' ? 'wait' : 'pointer',
              }}
            >
              {t.submitForScrutiny}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

function StepRow({ label, status }: { label: string; status: StepStatus }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: 'var(--text2)' }}>
      {status === 'running' && <Loader2 size={14} className="spin" color="var(--azure)" />}
      {status === 'done' && <CheckCircle2 size={14} color="#15803D" />}
      {status === 'error' && <AlertTriangle size={14} color="#B91C1C" />}
      {status === 'idle' && <span style={{ width: 14, height: 14, borderRadius: '50%', border: '2px solid var(--border)', display: 'inline-block' }} />}
      <span>{label}</span>
    </div>
  );
}

function extractErrorMessage(error: unknown, fallback: string): string {
  if (error && typeof error === 'object') {
    const e = error as Record<string, unknown>;
    if (typeof e.detail === 'string') return e.detail;
    if (typeof e.title === 'string') return e.title;
  }
  return fallback;
}
