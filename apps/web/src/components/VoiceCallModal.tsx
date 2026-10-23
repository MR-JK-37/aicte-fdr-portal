import React, { useState, useEffect } from 'react';
import {
  PhoneCall,
  PhoneOff,
  Mic,
  MicOff,
  ShieldAlert,
  ShieldCheck,
  Lock,
  Volume2,
  CheckCircle2,
  RefreshCw,
  Globe,
  MessageSquare,
  Hash,
  AlertOctagon,
  X
} from 'lucide-react';
import { Instrument } from '../types';

interface VoiceCallModalProps {
  instrument: Instrument | null;
  onClose: () => void;
  onAddAuditEntry: (action: string, entityId: string, details: any) => void;
}

type CallState =
  | 'RINGING'
  | 'GREET_DISCLOSE'
  | 'VERIFY_PIN'
  | 'BRIEF'
  | 'MENU_QA'
  | 'CONFIRM_ACK'
  | 'CLOSE'
  | 'LOCKED';

interface TranscriptLine {
  sender: 'bot' | 'user';
  text: string;
  time: string;
}

export const VoiceCallModal: React.FC<VoiceCallModalProps> = ({
  instrument,
  onClose,
  onAddAuditEntry,
}) => {
  if (!instrument) return null;

  const [callState, setCallState] = useState<CallState>('RINGING');
  const [language, setLanguage] = useState<'en' | 'hi' | 'ta'>('en');
  const [pinInput, setPinInput] = useState('');
  const [attemptsLeft, setAttemptsLeft] = useState(3);
  const [transcripts, setTranscripts] = useState<TranscriptLine[]>([]);
  const [isMuted, setIsMuted] = useState(false);
  const [auditHash, setAuditHash] = useState<string | null>(null);

  // Add transcript helper
  const addTranscript = (sender: 'bot' | 'user', text: string) => {
    const time = new Date().toLocaleTimeString('en-IN', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setTranscripts((prev) => [...prev, { sender, text, time }]);
  };

  // Auto-answer after short delay
  useEffect(() => {
    if (callState === 'RINGING') {
      const timer = setTimeout(() => {
        setCallState('GREET_DISCLOSE');
        addTranscript(
          'bot',
          'Namaskar. This is AICTE Automated Security Deposit Notification Service calling regarding ' +
            instrument.institution_name +
            '. This call is recorded for statutory compliance under AICTE Act Sec 10(k). To access financial details, please enter your 4-digit voice security PIN.'
        );
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [callState, instrument]);

  // Handle PIN submission
  const handleKeypadPress = (digit: string) => {
    if (pinInput.length < 4) {
      const nextPin = pinInput + digit;
      setPinInput(nextPin);
      if (nextPin.length === 4) {
        verifyPin(nextPin);
      }
    }
  };

  const handleBackspace = () => {
    setPinInput((prev) => prev.slice(0, -1));
  };

  const verifyPin = (enteredPin: string) => {
    addTranscript('user', `[Entered PIN: ••••]`);
    // Valid test PIN is 1234 or 9999
    if (enteredPin === '1234' || enteredPin === '9999') {
      setCallState('BRIEF');
      const spokenAmount =
        language === 'hi'
          ? 'पैंतीस लाख रुपये'
          : language === 'ta'
          ? 'முப்பத்தைந்து லட்சம் ரூபாய்'
          : 'Thirty-Five Lakh Rupees';

      const last4 = instrument.instrument_number.slice(-4);

      setTimeout(() => {
        addTranscript(
          'bot',
          `PIN verified successfully. Your Fixed Deposit Receipt ending in digits ${last4} issued by ${instrument.bank_name} for an amount of ${spokenAmount} matures on ${instrument.maturity_date}. Press 1 to acknowledge, Press 2 to request 7-day snooze, or Press 3 for Officer callback.`
        );
        setCallState('MENU_QA');
      }, 800);
    } else {
      const remaining = attemptsLeft - 1;
      setAttemptsLeft(remaining);
      setPinInput('');

      if (remaining <= 0) {
        setCallState('LOCKED');
        addTranscript(
          'bot',
          'Security Alert: Maximum PIN verification attempts exceeded. Your voice channel has been locked for 24 hours. This incident has been logged in the AICTE immutable audit registry.'
        );
        onAddAuditEntry('VOICE_CHANNEL_LOCKED', instrument.id, {
          reason: '3 consecutive incorrect PIN attempts',
          locked_hours: 24,
          channel: 'voice_webrtc',
        });
      } else {
        addTranscript('bot', `Incorrect PIN. You have ${remaining} attempt(s) remaining. Please try again.`);
      }
    }
  };

  const handleAction = (option: number) => {
    if (option === 1) {
      addTranscript('user', '1 - Acknowledge Maturity Reminder');
      setCallState('CONFIRM_ACK');
      const mockHash = 'sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069';
      setAuditHash(mockHash);

      setTimeout(() => {
        addTranscript(
          'bot',
          `Thank you. Your acknowledgement for FDR ending in ${instrument.instrument_number.slice(-4)} has been recorded in the AICTE cryptographic audit ledger. Transaction Reference: ${mockHash.slice(0, 18)}... Good day.`
        );
        onAddAuditEntry('VOICE_REMINDER_ACKNOWLEDGED', instrument.id, {
          instrument_number: instrument.instrument_number,
          channel: 'voice_ai_agent',
          language,
          hash: mockHash,
        });
        setTimeout(() => setCallState('CLOSE'), 2500);
      }, 700);
    } else if (option === 2) {
      addTranscript('user', '2 - Request 7-day Snooze');
      setTimeout(() => {
        addTranscript('bot', 'A 7-day snooze grace period has been registered. You will receive an advisory 7 days prior to expiry.');
        onAddAuditEntry('VOICE_REMINDER_SNOOZED', instrument.id, { days: 7, channel: 'voice' });
        setTimeout(() => setCallState('CLOSE'), 1500);
      }, 600);
    } else if (option === 3) {
      addTranscript('user', '3 - Request Callback');
      setTimeout(() => {
        addTranscript('bot', 'Your callback request has been logged. An AICTE Regional Scrutiny Officer will reach out during office hours.');
        onAddAuditEntry('OFFICER_CALLBACK_REQUESTED', instrument.id, { channel: 'voice' });
        setTimeout(() => setCallState('CLOSE'), 1500);
      }, 600);
    }
  };

  const switchLanguage = (lang: 'en' | 'hi' | 'ta') => {
    setLanguage(lang);
    const msg =
      lang === 'hi'
        ? 'भाषा हिंदी में बदल दी गई है।'
        : lang === 'ta'
        ? 'மொழி தமிழில் மாற்றப்பட்டது.'
        : 'Language switched to English.';
    addTranscript('bot', msg);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-xl glass-card border border-indigo-500/30 overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        {/* Top bar */}
        <div className="p-4 bg-slate-900/90 border-b border-slate-700/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-lg shadow-indigo-500/30 animate-pulse">
              <PhoneCall className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-100 text-sm">AICTE Autonomous Voice Bot</span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                  Sarvam AI (WebRTC)
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Connected • FDR #{instrument.instrument_number} ({instrument.institution_name})
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Language dropdown */}
            <div className="flex items-center bg-slate-800 rounded-lg p-0.5 border border-slate-700 text-[11px]">
              <button
                onClick={() => switchLanguage('en')}
                className={`px-2 py-0.5 rounded font-medium ${language === 'en' ? 'bg-indigo-600 text-white' : 'text-slate-400'}`}
              >
                EN
              </button>
              <button
                onClick={() => switchLanguage('hi')}
                className={`px-2 py-0.5 rounded font-medium ${language === 'hi' ? 'bg-indigo-600 text-white' : 'text-slate-400'}`}
              >
                HI
              </button>
              <button
                onClick={() => switchLanguage('ta')}
                className={`px-2 py-0.5 rounded font-medium ${language === 'ta' ? 'bg-indigo-600 text-white' : 'text-slate-400'}`}
              >
                TA
              </button>
            </div>

            <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Audio Waveform Banner */}
        <div className="px-6 py-3 bg-gradient-to-r from-slate-950 via-indigo-950/40 to-slate-950 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Volume2 className="w-4 h-4 text-indigo-400 animate-pulse" />
            <span className="text-xs text-indigo-300 font-medium">
              {callState === 'RINGING'
                ? 'Establishing WebRTC Audio Link...'
                : callState === 'LOCKED'
                ? 'Channel Locked'
                : 'Live Audio Stream (8000 Hz / G.711 / WebRTC)'}
            </span>
          </div>

          {/* Animated waveform bars */}
          <div className="flex items-end gap-1 h-5">
            {[4, 12, 18, 8, 20, 14, 10, 16, 6, 12].map((h, i) => (
              <span
                key={i}
                className="w-1 bg-indigo-500 rounded-full transition-all duration-300 animate-pulse"
                style={{ height: `${callState === 'CLOSE' || callState === 'LOCKED' ? 2 : h}px` }}
              />
            ))}
          </div>
        </div>

        {/* Conversation Transcript Stream */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-950/60 min-h-[180px] max-h-[220px]">
          {transcripts.map((t, idx) => (
            <div
              key={idx}
              className={`flex flex-col ${t.sender === 'user' ? 'items-end' : 'items-start'} text-xs space-y-1`}
            >
              <div className="flex items-center gap-1.5 text-[10px] text-slate-500 px-1">
                <span>{t.sender === 'bot' ? 'AICTE Bot' : 'Authorized Signatory'}</span>
                <span>•</span>
                <span>{t.time}</span>
              </div>
              <div
                className={`p-3 rounded-2xl max-w-[85%] leading-relaxed ${
                  t.sender === 'user'
                    ? 'bg-indigo-600 text-white rounded-br-none shadow-md'
                    : 'bg-slate-900 border border-slate-700/70 text-slate-200 rounded-bl-none'
                }`}
              >
                {t.text}
              </div>
            </div>
          ))}
        </div>

        {/* Interactive Interaction Area */}
        <div className="p-4 bg-slate-900/90 border-t border-slate-700/60">
          {callState === 'VERIFY_PIN' || callState === 'GREET_DISCLOSE' ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-300 font-medium flex items-center gap-1.5">
                  <Lock className="w-4 h-4 text-amber-400" />
                  Enter 4-Digit Voice PIN (Demo: 1234)
                </span>
                <span className="text-amber-400 text-[11px] font-semibold">
                  {attemptsLeft} attempt(s) remaining
                </span>
              </div>

              {/* PIN circles */}
              <div className="flex justify-center gap-3 py-2">
                {[0, 1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-base transition-all ${
                      pinInput.length > i
                        ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/40 border-indigo-400'
                        : 'bg-slate-800 border border-slate-700 text-slate-500'
                    }`}
                  >
                    {pinInput.length > i ? '•' : ''}
                  </div>
                ))}
              </div>

              {/* Numeric Keypad */}
              <div className="grid grid-cols-3 gap-2 max-w-[240px] mx-auto pt-1">
                {['1', '2', '3', '4', '5', '6', '7', '8', '9', '', '0', 'del'].map((val, idx) => {
                  if (val === '') return <div key={idx} />;
                  if (val === 'del') {
                    return (
                      <button
                        key={idx}
                        onClick={handleBackspace}
                        className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                      >
                        DEL
                      </button>
                    );
                  }
                  return (
                    <button
                      key={idx}
                      onClick={() => handleKeypadPress(val)}
                      className="p-2.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-100 text-sm font-bold border border-slate-700/70 hover:border-indigo-500 transition shadow-sm active:scale-95"
                    >
                      {val}
                    </button>
                  );
                })}
              </div>
            </div>
          ) : callState === 'MENU_QA' ? (
            <div className="space-y-3">
              <span className="text-xs font-medium text-slate-300 block">
                Select Voice Response Action:
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <button
                  onClick={() => handleAction(1)}
                  className="btn-primary py-2 px-3 text-xs flex items-center justify-center gap-1.5 bg-emerald-600 hover:bg-emerald-500"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  [1] Acknowledge
                </button>
                <button
                  onClick={() => handleAction(2)}
                  className="btn-secondary py-2 px-3 text-xs flex items-center justify-center gap-1.5"
                >
                  [2] Snooze 7d
                </button>
                <button
                  onClick={() => handleAction(3)}
                  className="btn-secondary py-2 px-3 text-xs flex items-center justify-center gap-1.5"
                >
                  [3] Officer Callback
                </button>
              </div>
            </div>
          ) : callState === 'LOCKED' ? (
            <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/40 flex items-center gap-3 text-xs text-rose-300">
              <AlertOctagon className="w-6 h-6 text-rose-400 shrink-0" />
              <div>
                <strong>Voice Channel Locked (24 Hours)</strong>
                <p className="text-[11px] text-rose-400/80 mt-0.5">
                  Three consecutive failed PIN attempts detected. An officer review ticket has been automatically dispatched.
                </p>
              </div>
            </div>
          ) : callState === 'CONFIRM_ACK' ? (
            <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/40 flex items-center gap-3 text-xs text-emerald-300">
              <ShieldCheck className="w-6 h-6 text-emerald-400 shrink-0" />
              <div>
                <strong>Cryptographic Voice Acknowledgement Recorded</strong>
                <p className="font-mono text-[10px] text-emerald-400/80 truncate max-w-sm mt-0.5">
                  Hash: {auditHash}
                </p>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center py-2 text-xs text-slate-400">
              <RefreshCw className="w-4 h-4 animate-spin mr-2" /> Call in progress...
            </div>
          )}

          {/* Bottom Call Controls */}
          <div className="flex items-center justify-between pt-4 mt-3 border-t border-slate-800">
            <button
              onClick={() => setIsMuted(!isMuted)}
              className={`p-2 rounded-full border text-xs flex items-center gap-1.5 ${
                isMuted ? 'bg-rose-950 text-rose-300 border-rose-800' : 'bg-slate-800 text-slate-300 border-slate-700'
              }`}
            >
              {isMuted ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              <span>{isMuted ? 'Unmute' : 'Mute'}</span>
            </button>

            <button
              onClick={onClose}
              className="px-5 py-2 rounded-full bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-rose-600/30 transition active:scale-95"
            >
              <PhoneOff className="w-4 h-4" />
              <span>End Call</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
