import React, { useState } from 'react';
import {
  UploadCloud,
  FileText,
  AlertTriangle,
  CheckCircle,
  ShieldAlert,
  Sparkles,
  ArrowRight,
  Eye,
  Check,
} from 'lucide-react';
import { Instrument } from '../types';

interface NewFDRSubmissionProps {
  onSuccess: (newInst: Instrument) => void;
  lang: string;
}

export const NewFDRSubmission: React.FC<NewFDRSubmissionProps> = ({ onSuccess, lang }) => {
  const [fileUploaded, setFileUploaded] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [extractedData, setExtractedData] = useState<any>(null);
  const [forgeryFlags, setForgeryFlags] = useState<string[]>([]);
  const [confirmed, setConfirmed] = useState(false);

  const t = {
    en: {
      title: 'New FDR Submission & OCR Intelligence',
      subtitle: 'Upload scanned FDR copy. Multi-layer pipeline: AV scan → pHash duplicate check → OCR → LLM extraction → Forgery signals.',
      dropLabel: 'Drag and drop FDR PDF or Scanned Image (Max 15MB)',
      selectFile: 'Browse File',
      scanningMsg: 'Running ClamAV scan • Computing pHash • Tesseract OCR • Structured LLM extraction...',
      extractedTitle: 'Extracted FDR Fields with Confidence Chips',
      confirmBtn: 'Scrutiny Officer Confirm (Upgrade to L1)',
      successMsg: 'FDR Confirmed and Upgraded to L1 Evidence Tier!',
    },
    hi: {
      title: 'नया एफडीआर प्रस्तुतीकरण एवं ओसीआर विश्लेषण',
      subtitle: 'स्कैन की गई एफडीआर प्रति अपलोड करें। वायरस स्कैन, प्रतिलिपि जांच, ओसीआर एवं विसंगति विश्लेषण।',
      dropLabel: 'एफडीआर पीडीएफ या स्कैन की गई छवि यहाँ खींचें',
      selectFile: 'फ़ाइल चुनें',
      scanningMsg: 'सुरक्षा स्कैन • ओसीआर • फ़ील्ड निष्कर्षण जारी है...',
      extractedTitle: 'विश्वसनीयता स्कोर के साथ निष्कर्षित विवरण',
      confirmBtn: 'जांच अधिकारी अनुमोदन (L1 स्तर में अपग्रेड)',
      successMsg: 'एफडीआर स्वीकृत और L1 स्तर में अपग्रेड हो गया!',
    },
    ta: {
      title: 'புதிய FDR சமர்ப்பிப்பு & OCR புலனாய்வு',
      subtitle: 'ஸ்கேன் செய்யப்பட்ட FDR நகலை பதிவேற்றவும். வைரஸ் ஸ்கேன், போலி சரிபார்ப்பு மற்றும் தானியங்கி பிரித்தெடுத்தல்.',
      dropLabel: 'FDR PDF அல்லது ஸ்கேன் செய்யப்பட்ட படத்தை பதிவேற்றவும்',
      selectFile: 'கோப்பைத் தேர்ந்தெடுங்கள்',
      scanningMsg: 'பாதுகாப்பு சோதனை • OCR • AI பிரித்தெடுத்தல் நடைபெறுகிறது...',
      extractedTitle: 'நம்பகத்தன்மை குறியீடுகளுடன் பிரித்தெடுக்கப்பட்ட விவரங்கள்',
      confirmBtn: 'ஆய்வு அதிகாரி ஒப்புதல் (L1 நிலைக்கு மாற்று)',
      successMsg: 'FDR அங்கீகரிக்கப்பட்டு L1 நிலைக்கு மேம்படுத்தப்பட்டது!',
    },
  }[lang as 'en' | 'hi' | 'ta'] || {
    title: 'New FDR Submission & OCR Intelligence',
    subtitle: 'Upload scanned FDR copy. Multi-layer pipeline.',
    dropLabel: 'Drag and drop FDR PDF',
    selectFile: 'Browse File',
    scanningMsg: 'Processing...',
    extractedTitle: 'Extracted FDR Fields',
    confirmBtn: 'Scrutiny Officer Confirm (L1)',
    successMsg: 'Confirmed to L1!',
  };

  const handleSimulatedUpload = () => {
    setFileUploaded(true);
    setScanning(true);

    setTimeout(() => {
      setScanning(false);
      setExtractedData({
        institution_name: 'PSG College of Technology',
        instrument_number: 'FDR-2026-PSG-9844',
        bank_name: 'State Bank of India',
        branch_ifsc: 'SBIN0001452 (Peelamedu Branch)',
        amount_paise: 1250000000,
        amount_words: 'One Crore Twenty-Five Lakh Rupees',
        issue_date: '2026-10-15',
        maturity_date: '2036-10-15',
        tenor_years: 10,
        joint_holder: 'Regional Officer, AICTE Southern Region',
        confidence: {
          number: 0.98,
          amount: 0.99,
          bank: 0.97,
          maturity: 0.95,
          joint_holder: 0.96,
        },
      });
      // Seeded defect for demo (Scenario 1 & 2): Tenor note
      setForgeryFlags([
        'Lien Clause Present: Marked in favor of AICTE as required by APH cl. 6.46',
        'Duplicate Check: pHash distance > 12; unique image across institutional database',
      ]);
    }, 1800);
  };

  const handleConfirmL1 = () => {
    setConfirmed(true);
    const newInst: Instrument = {
      id: `inst-${Date.now()}`,
      institution_id: 'inst-psg-01',
      institution_name: 'PSG College of Technology',
      instrument_number: 'FDR-2026-PSG-9844',
      type: 'FDR',
      amount: 1250000000,
      bank_name: 'State Bank of India',
      branch_ifsc: 'SBIN0001452',
      issue_date: '2026-10-15',
      maturity_date: '2036-10-15',
      status: 'ACTIVE',
      evidence_level: 'L1',
      joint_account_holder: 'Regional Officer, AICTE',
    };
    onSuccess(newInst);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '24px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Sparkles size={24} color="#06b6d4" />
          {t.title}
        </h2>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
          {t.subtitle}
        </p>

        {/* Upload Zone */}
        {!fileUploaded && (
          <div
            onClick={handleSimulatedUpload}
            style={{
              marginTop: '24px',
              border: '2px dashed var(--border-glow-cyan)',
              borderRadius: '16px',
              padding: '48px 24px',
              textAlign: 'center',
              background: 'rgba(6, 182, 212, 0.04)',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(6, 182, 212, 0.08)')}
            onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(6, 182, 212, 0.04)')}
          >
            <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'rgba(6, 182, 212, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px auto' }}>
              <UploadCloud size={32} color="#22d3ee" />
            </div>
            <h4 style={{ fontFamily: 'var(--font-display)', fontSize: '18px', fontWeight: 600 }}>{t.dropLabel}</h4>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '6px' }}>PDF, TIFF, JPEG • Magic byte sanitization and AV scan active</p>
            <button className="btn-primary" style={{ marginTop: '16px' }}>
              {t.selectFile} (Demo FDR)
            </button>
          </div>
        )}

        {/* Scanning Spinner */}
        {scanning && (
          <div style={{ marginTop: '24px', padding: '36px', textAlign: 'center', background: 'rgba(0, 0, 0, 0.3)', borderRadius: '16px', border: '1px solid var(--border-glass)' }}>
            <div className="ring-pulse" style={{ width: 48, height: 48, borderRadius: '50%', background: '#06b6d4', margin: '0 auto 16px auto' }} />
            <h4 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 600, color: '#38bdf8' }}>
              {t.scanningMsg}
            </h4>
          </div>
        )}

        {/* Extracted Data View */}
        {extractedData && (
          <div style={{ marginTop: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
              <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '18px', fontWeight: 600, color: '#38bdf8' }}>
                {t.extractedTitle}
              </h3>
              <span className="badge-evidence badge-l1">Status: Pre-Confirm (L0 → L1)</span>
            </div>

            {/* Fields Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
              <div style={{ padding: '14px', borderRadius: 10, background: 'rgba(0, 0, 0, 0.3)', border: '1px solid var(--border-glass)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>FDR Certificate Number</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '16px', fontWeight: 700, color: '#f8fafc', marginTop: '4px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span>{extractedData.instrument_number}</span>
                  <span style={{ fontSize: '10px', background: 'rgba(16, 185, 129, 0.2)', color: '#34d399', padding: '2px 6px', borderRadius: 4 }}>98% Conf</span>
                </div>
              </div>

              <div style={{ padding: '14px', borderRadius: 10, background: 'rgba(0, 0, 0, 0.3)', border: '1px solid var(--border-glass)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Deposit Amount</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '16px', fontWeight: 700, color: '#34d399', marginTop: '4px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span>₹1,25,00,000</span>
                  <span style={{ fontSize: '10px', background: 'rgba(16, 185, 129, 0.2)', color: '#34d399', padding: '2px 6px', borderRadius: 4 }}>99% Conf</span>
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>{extractedData.amount_words}</div>
              </div>

              <div style={{ padding: '14px', borderRadius: 10, background: 'rgba(0, 0, 0, 0.3)', border: '1px solid var(--border-glass)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Bank & Branch IFSC</div>
                <div style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc', marginTop: '4px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span>{extractedData.bank_name}</span>
                  <span style={{ fontSize: '10px', background: 'rgba(16, 185, 129, 0.2)', color: '#34d399', padding: '2px 6px', borderRadius: 4 }}>97% Conf</span>
                </div>
                <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>{extractedData.branch_ifsc}</div>
              </div>

              <div style={{ padding: '14px', borderRadius: 10, background: 'rgba(0, 0, 0, 0.3)', border: '1px solid var(--border-glass)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Tenor & Maturity Date</div>
                <div style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc', marginTop: '4px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span>{extractedData.maturity_date} (10 Years)</span>
                  <span style={{ fontSize: '10px', background: 'rgba(16, 185, 129, 0.2)', color: '#34d399', padding: '2px 6px', borderRadius: 4 }}>95% Conf</span>
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Issue Date: {extractedData.issue_date}</div>
              </div>
            </div>

            {/* Forgery & Validation Signals */}
            <div style={{ padding: '16px', borderRadius: 12, background: 'rgba(6, 182, 212, 0.08)', border: '1px solid rgba(6, 182, 212, 0.25)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', fontWeight: 600, color: '#38bdf8' }}>
                <CheckCircle size={16} color="#34d399" />
                Deterministic Validation & Forgery Analysis
              </div>
              <ul style={{ marginTop: '8px', paddingLeft: '20px', fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {forgeryFlags.map((flag, idx) => (
                  <li key={idx}>{flag}</li>
                ))}
              </ul>
            </div>

            {/* Officer Confirmation */}
            {!confirmed ? (
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                <button
                  onClick={() => {
                    setFileUploaded(false);
                    setExtractedData(null);
                  }}
                  className="btn-secondary"
                >
                  Discard / Re-upload
                </button>
                <button onClick={handleConfirmL1} className="btn-primary">
                  <Check size={16} />
                  <span>{t.confirmBtn}</span>
                </button>
              </div>
            ) : (
              <div style={{ padding: '16px', borderRadius: 10, background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.4)', color: '#6ee7b7', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '10px' }}>
                <CheckCircle size={20} />
                <span>{t.successMsg}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
