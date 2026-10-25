import React, { useState } from 'react';
import { UploadCloud, Sparkles } from 'lucide-react';

interface NewFDRSubmissionProps {
  lang: string;
}

export const NewFDRSubmission: React.FC<NewFDRSubmissionProps> = ({ lang }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const t = {
    en: {
      title: 'New FDR Submission',
      subtitle:
        'Upload a scanned FDR copy. Document review (virus scan, duplicate check, OCR, officer confirmation) is tracked in stream R4/R3.',
      dropLabel: 'Drag and drop FDR PDF or scanned image (max 15MB)',
      selectFile: 'Choose file',
      notWired: 'Submission is not yet connected to the API. Nothing is uploaded or recorded.',
    },
    hi: {
      title: 'नया एफडीआर प्रस्तुतीकरण',
      subtitle: 'स्कैन की गई एफडीआर प्रति अपलोड करें।',
      dropLabel: 'एफडीआर पीडीएफ या स्कैन की गई छवि यहाँ खींचें',
      selectFile: 'फ़ाइल चुनें',
      notWired: 'यह सुविधा अभी एपीआई से जुड़ी नहीं है। कुछ भी अपलोड नहीं हुआ है।',
    },
    ta: {
      title: 'புதிய FDR சமர்ப்பிப்பு',
      subtitle: 'ஸ்கேன் செய்யப்பட்ட FDR நகலை பதிவேற்றவும்.',
      dropLabel: 'FDR PDF அல்லது ஸ்கேன் செய்யப்பட்ட படத்தை பதிவேற்றவும்',
      selectFile: 'கோப்பைத் தேர்ந்தெடுங்கள்',
      notWired: 'இது இன்னும் API உடன் இணைக்கப்படவில்லை. எதுவும் பதிவேற்றப்படவில்லை.',
    },
  }[lang as 'en' | 'hi' | 'ta'] || {
    title: 'New FDR Submission',
    subtitle: 'Upload a scanned FDR copy.',
    dropLabel: 'Drag and drop FDR PDF',
    selectFile: 'Choose file',
    notWired: 'Not yet connected to the API.',
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
        <p style={{ fontSize: '13px', color: 'var(--text3)', marginTop: '4px' }}>
          {t.subtitle}
        </p>

        <div
          style={{
            marginTop: '24px',
            border: '2px dashed #CBD5E1',
            borderRadius: '20px',
            padding: '48px 24px',
            textAlign: 'center',
            background: 'var(--field)',
            transition: 'border-color 0.2s ease',
          }}
        >
          <div
            style={{
              width: 60,
              height: 60,
              borderRadius: '50%',
              background: '#FFFFFF',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px auto',
              boxShadow: '0 4px 14px rgba(0,0,0,0.06)',
            }}
          >
            <UploadCloud size={28} color="var(--azure)" />
          </div>
          <h4 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 700, color: 'var(--text1)' }}>
            {t.dropLabel}
          </h4>
          <p style={{ fontSize: '12px', color: 'var(--text3)', marginTop: '4px' }}>
            PDF, TIFF, JPEG (Max 15MB)
          </p>
          <label
            style={{
              marginTop: '16px',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '10px 22px',
              borderRadius: '9999px',
              background: 'var(--ink)',
              color: '#FFFFFF',
              fontSize: '13px',
              fontWeight: 700,
              cursor: 'pointer',
              border: 'none',
              boxShadow: '0 4px 12px rgba(17, 24, 39, 0.2)',
            }}
          >
            {t.selectFile}
            <input
              type="file"
              accept="application/pdf,image/*"
              style={{ display: 'none' }}
              onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
            />
          </label>
        </div>

        {selectedFile && (
          <div
            style={{
              marginTop: '16px',
              padding: '16px',
              borderRadius: '14px',
              background: '#F1F5F9',
              border: '1px solid var(--border)',
              fontSize: '12px',
              color: 'var(--text2)',
            }}
          >
            <strong style={{ color: 'var(--text1)' }}>{selectedFile.name}</strong> selected.{' '}
            {t.notWired}
          </div>
        )}
      </div>
    </div>
  );
};
