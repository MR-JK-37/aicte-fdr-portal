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
  general?: boolean;
}

const QUICK_SUGGESTIONS = [
  'What is FDR tenure & joint lien?',
  'Penalty for delayed submission?',
  'Can an FDR be prematurely withdrawn?',
  'How does release clearance work?',
];

function extractErrorMessage(error: unknown, fallback: string): string {
  if (error && typeof error === 'object') {
    const e = error as Record<string, unknown>;
    if (typeof e.detail === 'string') return e.detail;
    if (typeof e.title === 'string') return e.title;
  }
  return fallback;
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
  const scrollViewRef = useRef<React.ElementRef<typeof ScrollView>>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const watchdogTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
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

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    if (watchdogTimerRef.current) {
      clearTimeout(watchdogTimerRef.current);
      watchdogTimerRef.current = null;
    }
    setIsLoading(false);
  };

  /**
   * Sends the question to the real AICTE AI gateway (POST /v1/ai/policy-qa —
   * the same Groq/OpenRouter-backed, APH-corpus-grounded endpoint the web
   * AskHandbookModal uses). This never substitutes a locally-invented answer
   * or citation when the real call is slow, fails, or honestly reports no
   * match — CLAUDE.md non-negotiables #1/#2: nothing simulated in production,
   * facts never come from anywhere but the authorised backend.
   */
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

    // 30s watchdog so isLoading never stays stuck true if the call hangs.
    watchdogTimerRef.current = setTimeout(() => {
      setIsLoading(false);
    }, 30000);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const { data, error } = await api.POST('/v1/ai/policy-qa', {
        body: { question: textToSend },
        signal: controller.signal,
      });

      // If the user fired another message or cancelled in the meantime,
      // ignore this superseded response.
      if (abortControllerRef.current !== controller) return;

      if (data && data.answer) {
        const assistantMsg: ChatMessage = {
          id: `bot-${Date.now()}`,
          sender: 'assistant',
          text: data.answer,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          citations: data.verified_citations || [],
          sources: (data.sources || []).map((s: any) => ({
            clause_id: s.clause_id,
            title: s.title,
            distance: s.distance,
          })),
          general: data.general ?? false,
        };
        setMessages((prev) => [...prev, assistantMsg]);
        return;
      }

      const unavailableMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        sender: 'assistant',
        text: extractErrorMessage(
          error,
          'AI gateway is temporarily unavailable. Try again shortly.'
        ),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, unavailableMsg]);
    } catch (err) {
      if (abortControllerRef.current !== controller) return;
      const cancelledMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        sender: 'assistant',
        text:
          err instanceof Error && err.name === 'AbortError'
            ? 'Cancelled.'
            : 'Network error while reaching the AI gateway. Check your connection and try again.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, cancelledMsg]);
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

                      {/* Distinct from a clause-grounded answer — never let a
                          general-conversation reply look like a verified
                          statutory citation (CLAUDE.md non-negotiable #3). */}
                      {!isUser && m.general && (
                        <View style={styles.generalBadgeWrap}>
                          <Icon name="chat" size={12} color={tone.text3} />
                          <Text style={[styles.generalBadgeText, { color: tone.text3 }]}>
                            General conversation, not a regulatory citation
                          </Text>
                        </View>
                      )}

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
                      onPress={handleCancel}
                      activeOpacity={0.7}
                      style={[
                        styles.cancelBtn,
                        {
                          backgroundColor: isDark ? tone.surface : '#eff3ff',
                          borderColor: isDark ? tone.surfaceMuted : '#e1e6f8',
                        },
                      ]}
                      accessibilityLabel="Cancel the pending request"
                    >
                      <Icon name="error" size={12} color={tone.text3} />
                      <Text style={[styles.cancelBtnText, { color: tone.accent }]}>Cancel</Text>
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
  generalBadgeWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    marginTop: 8,
  },
  generalBadgeText: {
    fontSize: 10,
    fontWeight: '700',
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
