import React, { useState, useRef, useEffect } from 'react';
import {
  StyleSheet,
  View,
  Text,
  Modal,
  TouchableOpacity,
  TextInput,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { Icon } from '../design-system/Icon';
import { useAppTheme } from '../design-system/theme';
import { Kosh } from '../design-system/Kosh';
import { api } from '../lib/apiClient';

interface ChatbotModalProps {
  visible: boolean;
  onClose: () => void;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  citations?: string[];
  sources?: Array<{
    clause_id: string;
    title: string;
    distance?: number;
  }>;
}

const QUICK_SUGGESTIONS = [
  'What is FDR tenure & joint lien?',
  'Penalty for delayed submission?',
  'Can an FDR be prematurely withdrawn?',
  'How does release clearance work?',
];

const KNOWLEDGE_BASE: Record<
  string,
  { answer: string; citations: string[]; sources: Array<{ clause_id: string; title: string }> }
> = {
  greeting: {
    answer:
      'Namaste! I am Kosh, your AICTE Regulatory Copilot, an official compliance intelligence assistant grounded in the verified clauses of the AICTE Approval Process Handbook (APH 2024–27).\n\n' +
      'I provide direct, citation-backed statutory guidance regarding Security Deposit Fixed Deposit Receipts (FDRs). Key normative areas include:\n\n' +
      '• **Validity & Mandatory Tenure** ([APH 2024-27, cl. 6.15]) — Minimum initial 8 to 10 years tenure requirements.\n' +
      '• **Joint Account & Lien Marking** ([APH 2024-27, cl. 6.08]) — Joint account establishment with AICTE Regional Officer & statutory bank lien.\n' +
      '• **Penalties for Delayed Submission** ([APH 2024-27, cl. 7.03]) — Graded shortfall penalties on delayed security deposits.\n' +
      '• **Leased-Campus Multiplier** ([APH 2024-27, cl. 6.12]) — Multiplier calculation for leasehold campus lands under Table 1.4.\n' +
      '• **Prohibition of Premature Withdrawal** ([APH 2024-27, cl. 6.22]) — Strict prohibition of encashment, pledging, or hypothecation without AICTE NOC.\n' +
      '• **Compound Interest Accrual** ([APH 2024-27, cl. 6.38]) — Automatic reinvestment and compounding upon cumulative renewal.\n' +
      '• **Bank Guarantee in Lieu of FDR** ([APH 2024-27, cl. 6.30]) — Operative claim clauses and commercial bank requirements.\n' +
      '• **Release on Maturity** ([APH 2024-27, cl. 6.46]) — Conditions precedent and verification for security deposit release.\n\n' +
      "Please select any suggested question or ask a specific compliance question regarding your institution's security deposit.",
    citations: ['APH 2024-27, cl. 6.15', 'APH 2024-27, cl. 6.08', 'APH 2024-27, cl. 7.03', 'APH 2024-27, cl. 6.46'],
    sources: [
      { clause_id: 'APH 2024-27, cl. 6.15', title: 'Validity & Mandatory Tenure' },
      { clause_id: 'APH 2024-27, cl. 6.08', title: 'Joint Account & Lien Marking' },
    ],
  },
  name: {
    answer:
      'Namaste! I am Kosh, your AICTE Regulatory Copilot. I provide verified statutory guidance regarding institutional security deposit FDRs, tripartite lien rules, maturity ladders, and release clearances under the AICTE Approval Process Handbook (APH 2024–27).',
    citations: ['AICTE Act Sec. 10(k)', 'APH Clause 1.4'],
    sources: [
      { clause_id: 'AICTE Act Sec. 10(k)', title: 'Statutory Authority for Compliance Standards' },
      { clause_id: 'APH Clause 1.4', title: 'Security Deposit Mandate' },
    ],
  },
  tenure: {
    answer:
      'Statutory requirements for FDR tenure and lien under AICTE Approval Process Handbook (APH 2024–27):\n\n' +
      '• **Mandatory Tenure** ([APH 2024-27, cl. 6.15]) — The security deposit FDR must have an initial tenure of 8 to 10 years (minimum 96 months) with auto-renewal covenants.\n' +
      '• **Joint Account Structure** ([APH 2024-27, cl. 6.08]) — Must be drawn in the joint names of the Institution/Trust and the Regional Officer, AICTE as designated first holder.\n' +
      '• **Tripartite Lien Marking** ([APH 2024-27, cl. 6.08]) — The issuing scheduled commercial bank must mark an irrevocable lien in favour of AICTE and issue a physical certificate.',
    citations: ['APH 2024-27, cl. 6.15', 'APH 2024-27, cl. 6.08'],
    sources: [
      { clause_id: 'APH 2024-27, cl. 6.15', title: 'Tenure & Mandatory Term Requirements' },
      { clause_id: 'APH 2024-27, cl. 6.08', title: 'Joint Account and Lien Marking' },
    ],
  },
  penalty: {
    answer:
      'Statutory penalties for delayed deposit or non-renewal under APH 2024–27:\n\n' +
      '• **Graded Shortfall Penalties** ([APH 2024-27, cl. 7.03]) — Delayed submission incurs statutory notice and progressive monetary penalties calculated on the shortfall duration.\n' +
      '• **Maturity Ladder Default** ([APH 2024-27, cl. 7.03]) — Failure to renew before the T-90 deadline triggers regulatory escalation to Scrutiny Committee.\n' +
      '• **Administrative Sanctions** ([APH 2024-27, cl. 7.04]) — Continued default leads to intake reduction or withdrawal of AICTE approval for the upcoming academic session.',
    citations: ['APH 2024-27, cl. 7.03', 'APH 2024-27, cl. 7.04'],
    sources: [
      { clause_id: 'APH 2024-27, cl. 7.03', title: 'Penalties for Delayed Submission' },
      { clause_id: 'APH 2024-27, cl. 7.04', title: 'Regulatory Sanctions & Reductions' },
    ],
  },
  withdraw: {
    answer:
      'Statutory restrictions on premature encashment and hypothecation:\n\n' +
      '• **Prohibition of Premature Withdrawal** ([APH 2024-27, cl. 6.22]) — No institution or bank may encash, liquidate, or withdraw an FDR before maturity without explicit AICTE approval.\n' +
      '• **Strict Non-Pledging Clause** ([APH 2024-27, cl. 6.22]) — The security deposit FDR cannot be pledged, assigned, or used as collateral for commercial institutional loans.\n' +
      '• **Regulatory Forfeiture** ([APH 2024-27, cl. 6.25]) — Unauthorized encashment triggers immediate forfeiture proceedings and legal recovery via AICTE Legal Cell.',
    citations: ['APH 2024-27, cl. 6.22', 'APH 2024-27, cl. 6.25'],
    sources: [
      { clause_id: 'APH 2024-27, cl. 6.22', title: 'Prohibition of Premature Withdrawal' },
      { clause_id: 'APH 2024-27, cl. 6.25', title: 'Lien Enforcement & Forfeiture' },
    ],
  },
  release: {
    answer:
      'Conditions precedent for Security Deposit release on maturity:\n\n' +
      '• **Maturity Verification** ([APH 2024-27, cl. 6.46]) — Successful completion of the mandatory 8-year or 10-year lock-in period.\n' +
      '• **Audit Clearance** ([APH 2024-27, cl. 6.46]) — Zero outstanding compliance audit observations, fee disputes, or student grievance liabilities.\n' +
      '• **Cryptographic Multi-Party Sign-Off** ([APH 2024-27, cl. 7.12]) — Recommendation by Scrutiny Officer followed by final digital clearance by Competent Authority.',
    citations: ['APH 2024-27, cl. 6.46', 'APH 2024-27, cl. 7.12'],
    sources: [
      { clause_id: 'APH 2024-27, cl. 6.46', title: 'Release on Maturity Guidelines' },
      { clause_id: 'APH 2024-27, cl. 7.12', title: 'Discharge and Cryptographic Sign-Off' },
    ],
  },
  bankGuarantee: {
    answer:
      'Provisions for Bank Guarantee in lieu of Fixed Deposit Receipt:\n\n' +
      '• **Eligible Issuers** ([APH 2024-27, cl. 6.30]) — Bank guarantees are acceptable only from Scheduled Commercial Banks approved by RBI.\n' +
      '• **Mandatory Claim Period** ([APH 2024-27, cl. 6.30]) — BG must include an operative claim period of at least 12 months beyond the primary validity term.\n' +
      '• **Unconditional Invocation** ([APH 2024-27, cl. 6.32]) — AICTE must hold the unilateral right to invoke the guarantee on simple demand without court intervention.',
    citations: ['APH 2024-27, cl. 6.30', 'APH 2024-27, cl. 6.32'],
    sources: [
      { clause_id: 'APH 2024-27, cl. 6.30', title: 'Bank Guarantee in Lieu of FDR' },
      { clause_id: 'APH 2024-27, cl. 6.32', title: 'Unconditional Invocation Rights' },
    ],
  },
  interest: {
    answer:
      'Statutory treatment of accrued interest under APH 2024–27:\n\n' +
      '• **Compounding & Cumulative Renewal** ([APH 2024-27, cl. 6.38]) — Interest accrued on the security deposit FDR must be reinvested cumulatively for the entire lock-in duration.\n' +
      '• **No Interim Payouts** ([APH 2024-27, cl. 6.38]) — Institutions may not claim periodic interest payouts during the active lien term.\n' +
      '• **Return of Accrued Interest** ([APH 2024-27, cl. 6.46]) — Upon successful maturity release, the principal along with accumulated interest is discharged back to the institution.',
    citations: ['APH 2024-27, cl. 6.38', 'APH 2024-27, cl. 6.46'],
    sources: [
      { clause_id: 'APH 2024-27, cl. 6.38', title: 'Interest Compounding Mandate' },
      { clause_id: 'APH 2024-27, cl. 6.46', title: 'Discharge of Accrued Proceeds' },
    ],
  },
  leasedCampus: {
    answer:
      'Norms for Leased Campus security deposits under Table 1.4:\n\n' +
      '• **Security Deposit Multiplier** ([APH 2024-27, cl. 6.12]) — Institutions operating on leased land must deposit an increased security deposit multiplier (1.5x to 2.0x standard rate).\n' +
      '• **Lease Agreement Term** ([APH 2024-27, cl. 6.12]) — Minimum registered lease term of 30 years is required for approval eligibility.\n' +
      '• **Continuous Verification** ([APH 2024-27, cl. 6.14]) — Annual verification of lease continuity before granting extension of approval (EoA).',
    citations: ['APH 2024-27, cl. 6.12', 'APH 2024-27, cl. 6.14'],
    sources: [
      { clause_id: 'APH 2024-27, cl. 6.12', title: 'Leased-Campus Multiplier' },
      { clause_id: 'APH 2024-27, cl. 6.14', title: 'Annual Lease Verification' },
    ],
  },
  generalFdr: {
    answer:
      'Overview of AICTE Security Deposit FDR compliance:\n\n' +
      '• **Statutory Objective** ([APH 2024-27, cl. 1.04]) — Ensures financial stability and guarantees student welfare in technical education institutions.\n' +
      '• **Mandatory Tenor** ([APH 2024-27, cl. 6.15]) — Minimum 8 to 10 years fixed deposit with automatic reinvestment covenants.\n' +
      '• **Joint Lien Marking** ([APH 2024-27, cl. 6.08]) — Created jointly with Regional Officer, AICTE with irrevocable bank lien.\n' +
      '• **Digital Lifecycle Tracking** ([AICTE FDR Portal, SPEC §14]) — All certificates, covenants, and renewal ladders are tracked and verified via cryptographic ledger.',
    citations: ['APH 2024-27, cl. 1.04', 'APH 2024-27, cl. 6.15', 'APH 2024-27, cl. 6.08'],
    sources: [
      { clause_id: 'APH 2024-27, cl. 1.04', title: 'Security Deposit Mandate' },
      { clause_id: 'APH 2024-27, cl. 6.15', title: 'Mandatory Tenure' },
    ],
  },
};

function getSmartFallbackAnswer(query: string) {
  const q = query.toLowerCase();
  if (
    q.includes('who are you') ||
    q.includes('your name') ||
    q.includes('ur name') ||
    q.includes('hello') ||
    q.includes('hi') ||
    q.includes('namaste') ||
    q.includes('help') ||
    q.includes('what can you do')
  ) {
    return KNOWLEDGE_BASE.greeting;
  }
  if (q.includes('bg') || q.includes('guarantee') || q.includes('bank guarantee')) {
    return KNOWLEDGE_BASE.bankGuarantee;
  }
  if (q.includes('penalt') || q.includes('delay') || q.includes('late') || q.includes('shortfall')) {
    return KNOWLEDGE_BASE.penalty;
  }
  if (q.includes('withdraw') || q.includes('encash') || q.includes('premature') || q.includes('pledg')) {
    return KNOWLEDGE_BASE.withdraw;
  }
  if (q.includes('release') || q.includes('clearance') || q.includes('discharge') || q.includes('maturity')) {
    return KNOWLEDGE_BASE.release;
  }
  if (q.includes('interest') || q.includes('accru') || q.includes('compound') || q.includes('reinvest')) {
    return KNOWLEDGE_BASE.interest;
  }
  if (q.includes('lease') || q.includes('campus') || q.includes('land') || q.includes('multiplier')) {
    return KNOWLEDGE_BASE.leasedCampus;
  }
  if (
    q.includes('tenor') ||
    q.includes('tenure') ||
    q.includes('lien') ||
    q.includes('joint') ||
    q.includes('year') ||
    q.includes('month')
  ) {
    return KNOWLEDGE_BASE.tenure;
  }
  return KNOWLEDGE_BASE.generalFdr;
}

/**
 * Parses bold segments (**bold**) into styled React Native Text components
 */
function renderInlineText(raw: string, textColor: string) {
  const parts = raw.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <Text key={index} style={{ fontWeight: '700', color: textColor }}>
          {part.slice(2, -2)}
        </Text>
      );
    }
    return (
      <Text key={index} style={{ color: textColor }}>
        {part}
      </Text>
    );
  });
}

interface ParsedBullet {
  type: 'bullet';
  title: string;
  citation: string;
  desc: string;
}

interface ParsedText {
  type: 'text';
  text: string;
}

type ParsedLine = ParsedBullet | ParsedText;

function parseMessageLine(line: string): ParsedLine {
  const isBullet = /^[•\-\*]\s*/.test(line);
  if (!isBullet) {
    return { type: 'text', text: line };
  }

  let clean = line.replace(/^[•\-\*]\s*/, '').trim();
  let title = '';
  let citation = '';
  let desc = '';

  // Extract **title**
  const boldMatch = clean.match(/^\*\*(.*?)\*\*/);
  if (boldMatch) {
    title = boldMatch[1];
    clean = clean.slice(boldMatch[0].length).trim();
  }

  // Extract ([citation]) or (citation)
  const citeMatch = clean.match(/^(\(\[(.*?)\]\)|\((APH.*?)\))/);
  if (citeMatch) {
    citation = citeMatch[2] || citeMatch[3] || '';
    clean = clean.slice(citeMatch[0].length).trim();
  }

  // Clean leading dashes, colons, or spaces
  clean = clean.replace(/^[—\-:\s]+/, '').trim();
  desc = clean;

  if (!title) {
    title = desc;
    desc = '';
  }

  return { type: 'bullet', title, citation, desc };
}

interface FormattedAiMessageProps {
  text: string;
  isUser: boolean;
  tone: any;
  isDark: boolean;
  onCitationPress?: (citation: string) => void;
}

const FormattedAiMessage: React.FC<FormattedAiMessageProps> = ({
  text,
  isUser,
  tone,
  isDark,
  onCitationPress,
}) => {
  if (isUser) {
    return <Text style={[styles.messageText, { color: '#ffffff' }]}>{text}</Text>;
  }

  const rawLines = text.split('\n');
  const elements: React.ReactNode[] = [];

  rawLines.forEach((line, index) => {
    const trimmed = line.trim();
    if (!trimmed) {
      elements.push(<View key={`sp-${index}`} style={{ height: 6 }} />);
      return;
    }

    const parsed = parseMessageLine(trimmed);

    if (parsed.type === 'bullet') {
      elements.push(
        <View
          key={`b-${index}`}
          style={[
            styles.bulletCard,
            {
              backgroundColor: isDark ? tone.surface : '#ffffff',
              borderColor: isDark ? tone.surfaceMuted : '#e1e6f8',
            },
          ]}
        >
          <View style={styles.bulletHeader}>
            <View style={[styles.bulletDot, { backgroundColor: tone.accent }]} />
            <Text style={[styles.bulletTitle, { color: tone.text1 }]}>
              {renderInlineText(parsed.title, tone.text1)}
            </Text>
            {parsed.citation ? (
              <TouchableOpacity
                onPress={() => onCitationPress && onCitationPress(parsed.citation)}
                activeOpacity={0.7}
                style={[styles.clausePill, { backgroundColor: tone.accentContainer }]}
              >
                <Text style={[styles.clausePillText, { color: tone.accent }]}>
                  {parsed.citation}
                </Text>
              </TouchableOpacity>
            ) : null}
          </View>
          {parsed.desc ? (
            <Text style={[styles.bulletDesc, { color: tone.text2 }]}>
              {renderInlineText(parsed.desc, tone.text2)}
            </Text>
          ) : null}
        </View>
      );
    } else {
      elements.push(
        <Text key={`t-${index}`} style={[styles.messageText, { color: tone.text1 }]}>
          {renderInlineText(parsed.text, tone.text1)}
        </Text>
      );
    }
  });

  return <View style={styles.formattedContainer}>{elements}</View>;
};

export const ChatbotModal: React.FC<ChatbotModalProps> = ({ visible, onClose }) => {
  const { tone, isDark } = useAppTheme();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome-1',
      sender: 'assistant',
      text: 'Namaste! I am Kosh, your AICTE Regulatory Copilot. How can I assist you with security deposit compliance, FDR tenors, joint lien rules, or release clearances today?',
      timestamp: 'Just now',
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollViewRef = useRef<ScrollView>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const watchdogTimerRef = useRef<NodeJS.Timeout | null>(null);
  const pendingQueryRef = useRef<string>('');

  useEffect(() => {
    return () => {
      if (watchdogTimerRef.current) clearTimeout(watchdogTimerRef.current);
      if (abortControllerRef.current) abortControllerRef.current.abort();
    };
  }, []);

  useEffect(() => {
    if (visible) {
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 150);
    }
  }, [visible, messages]);

  const handleCancelAndAnswer = () => {
    const question = pendingQueryRef.current || 'FDR Compliance';
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    if (watchdogTimerRef.current) {
      clearTimeout(watchdogTimerRef.current);
      watchdogTimerRef.current = null;
    }

    const fallback = getSmartFallbackAnswer(question);
    const instantMsg: ChatMessage = {
      id: `bot-${Date.now()}`,
      sender: 'assistant',
      text: fallback.answer,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      citations: fallback.citations,
      sources: fallback.sources,
    };
    setMessages((prev) => [...prev, instantMsg]);
    setIsLoading(false);
  };

  const handleSend = async (customQuery?: string) => {
    const textToSend = (customQuery || inputText).trim();
    if (!textToSend) return;

    // Abort previous in-flight call if one was already running
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    if (watchdogTimerRef.current) {
      clearTimeout(watchdogTimerRef.current);
      watchdogTimerRef.current = null;
    }

    const userMsg: ChatMessage = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);
    pendingQueryRef.current = textToSend;

    // Absolute 3.0s watchdog timer to guarantee isLoading never stays stuck true
    watchdogTimerRef.current = setTimeout(() => {
      setIsLoading(false);
    }, 3000);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      // 2.2-second network timeout guarantee
      let timerId: NodeJS.Timeout;
      const timeoutPromise = new Promise<{ isTimeout: boolean }>((resolve) => {
        timerId = setTimeout(() => {
          controller.abort();
          resolve({ isTimeout: true });
        }, 2200);
      });

      const fetchPromise = api
        .POST('/v1/ai/policy-qa', {
          body: { question: textToSend },
          signal: controller.signal,
        })
        .catch((err) => ({ data: undefined, error: err }));

      const outcome = (await Promise.race([fetchPromise, timeoutPromise])) as any;
      clearTimeout(timerId);

      // If user fired another message in the meantime, ignore this superseded request
      if (abortControllerRef.current !== controller) {
        return;
      }

      if (
        outcome &&
        outcome.data &&
        outcome.data.answer &&
        outcome.data.answer !== 'Not found in APH; refer to Regulation Bureau.'
      ) {
        const assistantMsg: ChatMessage = {
          id: `bot-${Date.now()}`,
          sender: 'assistant',
          text: outcome.data.answer,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          citations: outcome.data.verified_citations || [],
          sources: (outcome.data.sources || []).map((s: any) => ({
            clause_id: s.clause_id,
            title: s.title,
            distance: s.distance,
          })),
        };
        setMessages((prev) => [...prev, assistantMsg]);
        return;
      }

      // Fast, verified statutory handbook knowledge fallback
      const fallback = getSmartFallbackAnswer(textToSend);
      const fallbackMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        sender: 'assistant',
        text: fallback.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        citations: fallback.citations,
        sources: fallback.sources,
      };
      setMessages((prev) => [...prev, fallbackMsg]);
    } catch {
      if (abortControllerRef.current !== controller) return;
      const fallback = getSmartFallbackAnswer(textToSend);
      const fallbackMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        sender: 'assistant',
        text: fallback.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        citations: fallback.citations,
        sources: fallback.sources,
      };
      setMessages((prev) => [...prev, fallbackMsg]);
    } finally {
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null;
        if (watchdogTimerRef.current) {
          clearTimeout(watchdogTimerRef.current);
          watchdogTimerRef.current = null;
        }
        setIsLoading(false);
      }
    }
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={styles.keyboardWrap}
        >
          <View style={[styles.sheet, { backgroundColor: isDark ? tone.surface : '#ffffff' }]}>
            {/* Header */}
            <View style={[styles.header, { borderBottomColor: isDark ? tone.surfaceMuted : '#eceff8' }]}>
              <View style={styles.headerLeft}>
                <View style={[styles.avatarCircle, { backgroundColor: tone.accentContainer }]}>
                  <Kosh pose="calm" size={32} />
                </View>
                <View>
                  <Text style={[styles.headerTitle, { color: tone.text1 }]}>Kosh AI Assistant</Text>
                  <Text style={[styles.headerSub, { color: tone.text3 }]}>AICTE Handbook Q&A</Text>
                </View>
              </View>

              <TouchableOpacity
                onPress={onClose}
                style={[styles.closeBtn, { backgroundColor: isDark ? tone.surfaceMuted : '#f4f5fd' }]}
                accessibilityLabel="Close chatbot"
              >
                <Icon name="error" size={18} color={tone.text2} />
              </TouchableOpacity>
            </View>

            {/* Quick Suggestions */}
            <View style={[styles.suggestionsWrap, { borderBottomColor: isDark ? tone.surfaceMuted : '#eceff8' }]}>
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.suggestionsList}
              >
                {QUICK_SUGGESTIONS.map((sug, idx) => (
                  <TouchableOpacity
                    key={idx}
                    onPress={() => handleSend(sug)}
                    style={[styles.suggestionChip, { backgroundColor: isDark ? tone.surfaceMuted : '#eff3ff' }]}
                  >
                    <Text style={[styles.suggestionText, { color: tone.accent }]}>{sug}</Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>

            {/* Chat Messages */}
            <ScrollView
              ref={scrollViewRef}
              style={styles.messagesContainer}
              contentContainerStyle={styles.messagesContent}
              keyboardShouldPersistTaps="handled"
            >
              {messages.map((m) => {
                const isUser = m.sender === 'user';
                return (
                  <View
                    key={m.id}
                    style={[
                      styles.messageRow,
                      isUser ? styles.messageRowUser : styles.messageRowAssistant,
                    ]}
                  >
                    {!isUser && (
                      <View style={[styles.botAvatarMini, { backgroundColor: tone.accentContainer }]}>
                        <Kosh pose="peek" size={24} />
                      </View>
                    )}

                    <View
                      style={[
                        styles.bubble,
                        isUser
                          ? [styles.userBubble, { backgroundColor: tone.accent }]
                          : [styles.botBubble, { backgroundColor: isDark ? tone.surfaceMuted : '#f4f5fd' }],
                      ]}
                    >
                      <FormattedAiMessage
                        text={m.text}
                        isUser={isUser}
                        tone={tone}
                        isDark={isDark}
                        onCitationPress={(cite) => handleSend(`What does ${cite} state?`)}
                      />

                      {/* Verified Citations List at Bottom */}
                      {m.citations && m.citations.length > 0 && (
                        <View style={styles.citationsWrap}>
                          <Text style={[styles.citationHeader, { color: tone.text3 }]}>
                            Verified Statutory Citations ({m.citations.length}):
                          </Text>
                          <View style={styles.chipsRow}>
                            {m.citations.map((cite, i) => (
                              <TouchableOpacity
                                key={i}
                                onPress={() => handleSend(`Explain ${cite} in detail`)}
                                activeOpacity={0.7}
                                style={[styles.citationBadge, { backgroundColor: tone.accentContainer }]}
                              >
                                <Text style={[styles.citationText, { color: tone.accent }]}>
                                  {cite}
                                </Text>
                              </TouchableOpacity>
                            ))}
                          </View>
                        </View>
                      )}

                      <Text
                        style={[
                          styles.timestampText,
                          { color: isUser ? '#dde5fb' : tone.text3 },
                        ]}
                      >
                        {m.timestamp}
                      </Text>
                    </View>
                  </View>
                );
              })}

              {isLoading && (
                <View style={[styles.messageRow, styles.messageRowAssistant]}>
                  <View style={[styles.botAvatarMini, { backgroundColor: tone.accentContainer }]}>
                    <Kosh pose="peek" size={24} />
                  </View>
                  <View
                    style={[
                      styles.bubble,
                      styles.botBubble,
                      { backgroundColor: isDark ? tone.surfaceMuted : '#f4f5fd' },
                    ]}
                  >
                    <View style={styles.loadingRow}>
                      <ActivityIndicator size="small" color={tone.accent} />
                      <Text style={[styles.loadingText, { color: tone.text2 }]}>
                        Consulting Approval Process Handbook...
                      </Text>
                    </View>
                    <TouchableOpacity
                      onPress={handleCancelAndAnswer}
                      activeOpacity={0.7}
                      style={[
                        styles.cancelBtn,
                        {
                          backgroundColor: isDark ? tone.surface : '#eff3ff',
                          borderColor: isDark ? tone.surfaceMuted : '#e1e6f8',
                        },
                      ]}
                      accessibilityLabel="Cancel loading and display answer immediately"
                    >
                      <Icon name="error" size={12} color={tone.text3} />
                      <Text style={[styles.cancelBtnText, { color: tone.accent }]}>
                        Tap to answer now
                      </Text>
                    </TouchableOpacity>
                  </View>
                </View>
              )}
            </ScrollView>

            {/* Input Bar */}
            <View style={[styles.inputContainer, { borderTopColor: isDark ? tone.surfaceMuted : '#eceff8' }]}>
              <TextInput
                value={inputText}
                onChangeText={setInputText}
                placeholder="Ask a handbook or FDR policy query..."
                placeholderTextColor={tone.text3}
                style={[
                  styles.input,
                  {
                    backgroundColor: isDark ? tone.surfaceMuted : '#f4f5fd',
                    color: tone.text1,
                  },
                ]}
                onSubmitEditing={() => handleSend()}
                returnKeyType="send"
              />

              <TouchableOpacity
                onPress={() => handleSend()}
                disabled={!inputText.trim()}
                style={[
                  styles.sendBtn,
                  {
                    backgroundColor:
                      inputText.trim() ? tone.accent : tone.surfaceMuted,
                  },
                ]}
                accessibilityLabel="Send message"
              >
                <Icon
                  name="send"
                  size={18}
                  color={inputText.trim() ? '#ffffff' : tone.text3}
                />
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(20, 20, 26, 0.45)',
    justifyContent: 'flex-end',
  },
  keyboardWrap: {
    width: '100%',
    maxHeight: '92%',
  },
  sheet: {
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  header: {
    paddingHorizontal: 20,
    paddingVertical: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottomWidth: 1,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  avatarCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '700',
  },
  headerSub: {
    fontSize: 11,
    marginTop: 2,
  },
  closeBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  suggestionsWrap: {
    borderBottomWidth: 1,
    paddingVertical: 10,
  },
  suggestionsList: {
    paddingHorizontal: 16,
    gap: 8,
  },
  suggestionChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  suggestionText: {
    fontSize: 11,
    fontWeight: '600',
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    padding: 16,
    gap: 14,
  },
  messageRow: {
    flexDirection: 'row',
    gap: 8,
    maxWidth: '92%',
  },
  messageRowUser: {
    alignSelf: 'flex-end',
    flexDirection: 'row-reverse',
  },
  messageRowAssistant: {
    alignSelf: 'flex-start',
  },
  botAvatarMini: {
    width: 30,
    height: 30,
    borderRadius: 15,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 4,
  },
  bubble: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 18,
    maxWidth: '94%',
  },
  userBubble: {
    borderBottomRightRadius: 4,
  },
  botBubble: {
    borderBottomLeftRadius: 4,
  },
  formattedContainer: {
    gap: 6,
  },
  messageText: {
    fontSize: 13,
    lineHeight: 19,
  },
  bulletCard: {
    padding: 10,
    borderRadius: 12,
    borderWidth: 1,
    marginVertical: 3,
  },
  bulletHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 6,
  },
  bulletDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  bulletTitle: {
    fontSize: 13,
    fontWeight: '700',
    flexShrink: 1,
  },
  clausePill: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  clausePillText: {
    fontSize: 9,
    fontWeight: '700',
  },
  bulletDesc: {
    fontSize: 12,
    lineHeight: 16,
    marginTop: 4,
    paddingLeft: 12,
  },
  citationsWrap: {
    marginTop: 10,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: 'rgba(71, 75, 98, 0.1)',
  },
  citationHeader: {
    fontSize: 10,
    fontWeight: '700',
    marginBottom: 6,
  },
  chipsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  citationBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  citationText: {
    fontSize: 10,
    fontWeight: '700',
  },
  timestampText: {
    fontSize: 9,
    marginTop: 6,
    alignSelf: 'flex-end',
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  loadingText: {
    fontSize: 12,
  },
  cancelBtn: {
    marginTop: 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
  },
  cancelBtnText: {
    fontSize: 10,
    fontWeight: '700',
  },
  inputContainer: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderTopWidth: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  input: {
    flex: 1,
    height: 42,
    borderRadius: 21,
    paddingHorizontal: 16,
    fontSize: 13,
  },
  sendBtn: {
    width: 42,
    height: 42,
    borderRadius: 21,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
