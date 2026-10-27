import React, { useState } from 'react';
import { StyleSheet, View, Text, TouchableOpacity, Modal, Platform, TextInput, ScrollView, ActivityIndicator } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { Icon } from '../design-system/Icon';
import { useAppTheme } from '../design-system/theme';
import { api } from '../lib/apiClient';

interface DocumentCaptureModalProps {
  visible: boolean;
  onClose: () => void;
  institutionId: string | null;
  onSubmitted?: () => void;
}

type Stage = 'form' | 'viewfinder' | 'preview' | 'uploading' | 'completed' | 'error';

export const DocumentCaptureModal: React.FC<DocumentCaptureModalProps> = ({
  visible,
  onClose,
  institutionId,
  onSubmitted,
}) => {
  const { tone, isDark } = useAppTheme();
  const [stage, setStage] = useState<Stage>('form');
  const [instrumentNumber, setInstrumentNumber] = useState('');
  const [amount, setAmount] = useState('');
  const [issueDate, setIssueDate] = useState('');
  const [maturityDate, setMaturityDate] = useState('');
  const [asset, setAsset] = useState<ImagePicker.ImagePickerAsset | null>(null);
  const [stepLabel, setStepLabel] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [candidateFields, setCandidateFields] = useState<Record<string, unknown> | null>(null);

  const cardBg = isDark ? tone.surface : '#ffffff';

  const reset = () => {
    setStage('form');
    setInstrumentNumber('');
    setAmount('');
    setIssueDate('');
    setMaturityDate('');
    setAsset(null);
    setStepLabel('');
    setErrorMessage(null);
    setCandidateFields(null);
  };

  const canProceedFromForm =
    !!institutionId && instrumentNumber.trim().length >= 3 && !!amount && Number(amount) > 0;

  const handleCapture = async () => {
    // expo-image-picker's camera launcher asks for permission itself; on
    // web it falls back to the browser's native file/camera picker.
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    const result = permission.granted
      ? await ImagePicker.launchCameraAsync({ quality: 0.8, base64: false })
      : await ImagePicker.launchImageLibraryAsync({ quality: 0.8, base64: false });

    if (result.canceled || result.assets.length === 0) return;
    setAsset(result.assets[0]);
    setStage('preview');
  };

  const handlePickFromLibrary = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({ quality: 0.8, base64: false });
    if (result.canceled || result.assets.length === 0) return;
    setAsset(result.assets[0]);
    setStage('preview');
  };

  const handleStartUpload = async () => {
    if (!asset || !institutionId) return;
    setStage('uploading');
    setErrorMessage(null);

    try {
      setStepLabel('Creating instrument record…');
      const { data: instrument, error: draftError } = await api.POST('/v1/instruments/draft', {
        body: {
          institution_id: institutionId,
          type: 'FDR',
          instrument_number: instrumentNumber.trim(),
          amount: Number(amount),
          issue_date: issueDate ? new Date(issueDate).toISOString() : null,
          maturity_date: maturityDate ? new Date(maturityDate).toISOString() : null,
        },
      });
      if (draftError || !instrument) {
        throw new Error(extractErrorMessage(draftError, 'Could not create the instrument record.'));
      }

      setStepLabel('Uploading & scanning document…');
      const mimeType = asset.mimeType || 'image/jpeg';
      const fileForUpload: any =
        Platform.OS === 'web' && (asset as any).file
          ? (asset as any).file
          : {
              uri: asset.uri,
              name: asset.fileName || `capture.${mimeType.split('/')[1] || 'jpg'}`,
              type: mimeType,
            };

      const formData = new FormData();
      formData.append('file', fileForUpload);
      const { data: document, error: uploadError } = await api.POST('/v1/documents/upload-direct', {
        params: { query: { instrument_id: instrument.id, declared_mime_type: mimeType } },
        body: formData as unknown as { file: string },
        bodySerializer: (body) => body as unknown as BodyInit,
      });
      if (uploadError || !document) {
        throw new Error(
          extractErrorMessage(uploadError, 'Upload was rejected (virus scan, magic-byte check, or size limit).')
        );
      }

      setStepLabel('Running OCR / AI field extraction…');
      const { data: extraction } = await api.POST('/v1/documents/{document_id}/extract', {
        params: { path: { document_id: document.id } },
      });
      if (extraction) {
        setCandidateFields(extraction.candidate_fields ?? {});
      }

      setStepLabel('Submitting for scrutiny…');
      const { error: submitError } = await api.POST('/v1/instruments/{instrument_id}/submit', {
        params: { path: { instrument_id: instrument.id } },
        body: { reason: 'Institution submission via mobile document capture', policy_version: 'APH-2024-27-v1.0' },
      });
      if (submitError) {
        throw new Error(extractErrorMessage(submitError, 'Instrument was created but could not be submitted for scrutiny.'));
      }

      setStage('completed');
      onSubmitted?.();
    } catch (e: any) {
      setErrorMessage(e?.message || 'Submission failed.');
      setStage('error');
    }
  };

  return (
    <Modal visible={visible} animationType="slide" transparent={false}>
      <ScrollView
        contentContainerStyle={[styles.container, { backgroundColor: tone.bg }]}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.header}>
          <TouchableOpacity
            onPress={() => {
              reset();
              onClose();
            }}
            style={styles.closeBtn}
          >
            <Text style={[styles.closeBtnText, { color: tone.accent }]}>Cancel</Text>
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: tone.text1 }]}>New FDR Submission</Text>
          <View style={{ width: 40 }} />
        </View>

        {stage === 'form' && (
          <View style={styles.body}>
            {!institutionId && (
              <Text style={[styles.errorText, { color: '#B91C1C' }]}>
                Your account has no institution assigned. An institution-scoped role is required.
              </Text>
            )}
            <View style={styles.formField}>
              <Text style={[styles.label, { color: tone.text2 }]}>FDR / Instrument number</Text>
              <TextInput
                style={[styles.input, { borderColor: tone.outline, color: tone.text1, backgroundColor: cardBg }]}
                value={instrumentNumber}
                onChangeText={setInstrumentNumber}
                placeholder="SBI/2026/00123"
                placeholderTextColor={tone.text3}
              />
            </View>
            <View style={styles.formField}>
              <Text style={[styles.label, { color: tone.text2 }]}>Amount (INR)</Text>
              <TextInput
                style={[styles.input, { borderColor: tone.outline, color: tone.text1, backgroundColor: cardBg }]}
                value={amount}
                onChangeText={setAmount}
                placeholder="3500000"
                placeholderTextColor={tone.text3}
                keyboardType="numeric"
              />
            </View>
            <View style={styles.formField}>
              <Text style={[styles.label, { color: tone.text2 }]}>Issue date (YYYY-MM-DD)</Text>
              <TextInput
                style={[styles.input, { borderColor: tone.outline, color: tone.text1, backgroundColor: cardBg }]}
                value={issueDate}
                onChangeText={setIssueDate}
                placeholder="2026-01-10"
                placeholderTextColor={tone.text3}
              />
            </View>
            <View style={styles.formField}>
              <Text style={[styles.label, { color: tone.text2 }]}>Maturity date (YYYY-MM-DD)</Text>
              <TextInput
                style={[styles.input, { borderColor: tone.outline, color: tone.text1, backgroundColor: cardBg }]}
                value={maturityDate}
                onChangeText={setMaturityDate}
                placeholder="2029-01-10"
                placeholderTextColor={tone.text3}
              />
            </View>

            <TouchableOpacity
              style={[styles.primaryButton, { backgroundColor: canProceedFromForm ? tone.ink : tone.outline }]}
              disabled={!canProceedFromForm}
              onPress={() => setStage('viewfinder')}
            >
              <Text style={styles.primaryButtonText}>Continue to document capture</Text>
            </TouchableOpacity>
          </View>
        )}

        {stage === 'viewfinder' && (
          <View style={styles.body}>
            <View
              style={[
                styles.viewfinder,
                { backgroundColor: isDark ? 'rgba(0,0,0,0.5)' : '#f8fafc', borderColor: isDark ? tone.outline : '#e2e8f0' },
              ]}
            >
              <View style={styles.guideFrame}>
                <Icon name="documents" size={44} color={tone.accent} />
                <Text style={[styles.reticleText, { color: tone.text3 }]}>
                  Align the physical deposit receipt, then capture or pick from your library
                </Text>
              </View>
            </View>

            <View style={styles.shutterContainer}>
              <TouchableOpacity style={[styles.shutterOuter, { borderColor: tone.accent }]} onPress={handleCapture}>
                <View style={[styles.shutterInner, { backgroundColor: tone.accent }]} />
              </TouchableOpacity>
              <Text style={[styles.shutterLabel, { color: tone.text3 }]}>Tap to capture</Text>
              <TouchableOpacity onPress={handlePickFromLibrary}>
                <Text style={[styles.linkText, { color: tone.accent }]}>Choose from library instead</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {stage === 'preview' && asset && (
          <View style={styles.body}>
            <View style={[styles.previewBox, { backgroundColor: cardBg }]}>
              <Icon name="verified" size={40} color="#059669" />
              <Text style={[styles.previewTitle, { color: tone.text1 }]}>Document ready to upload</Text>
              <Text style={[styles.previewMeta, { color: tone.text3 }]}>
                {asset.fileName || 'capture'} {asset.fileSize ? `• ${(asset.fileSize / 1024).toFixed(0)} KB` : ''}
              </Text>
            </View>

            <View style={styles.previewActions}>
              <TouchableOpacity
                style={[styles.retakeButton, { backgroundColor: isDark ? tone.surfaceMuted : '#f1f5f9' }]}
                onPress={() => setStage('viewfinder')}
              >
                <Text style={[styles.retakeText, { color: tone.text2 }]}>Retake</Text>
              </TouchableOpacity>

              <TouchableOpacity style={[styles.uploadButton, { backgroundColor: isDark ? '#ffffff' : tone.ink }]} onPress={handleStartUpload}>
                <Icon name="upload" size={16} color={isDark ? '#0f172a' : '#ffffff'} />
                <Text style={[styles.uploadText, { color: isDark ? '#0f172a' : '#ffffff' }]}>Create, upload & submit</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {stage === 'uploading' && (
          <View style={styles.uploadBox}>
            <ActivityIndicator color={tone.accent} size="large" />
            <Text style={[styles.uploadTitle, { color: tone.text1 }]}>{stepLabel}</Text>
          </View>
        )}

        {stage === 'error' && (
          <View style={styles.uploadBox}>
            <Icon name="error" size={48} color="#B91C1C" />
            <Text style={[styles.uploadTitle, { color: tone.text1 }]}>Submission failed</Text>
            <Text style={[styles.errorText, { color: '#B91C1C' }]}>{errorMessage}</Text>
            <TouchableOpacity style={[styles.doneButton, { backgroundColor: isDark ? '#ffffff' : tone.ink }]} onPress={reset}>
              <Text style={[styles.doneText, { color: isDark ? '#0f172a' : '#ffffff' }]}>Start over</Text>
            </TouchableOpacity>
          </View>
        )}

        {stage === 'completed' && (
          <View style={styles.completeBox}>
            <Icon name="success" size={56} color="#059669" />
            <Text style={[styles.completeTitle, { color: tone.text1 }]}>Submitted for scrutiny</Text>
            <Text style={[styles.completeText, { color: tone.text3 }]}>
              The instrument record, document scan, and OCR extraction are now on the server. Track it from the
              dashboard.
            </Text>
            {candidateFields && Object.keys(candidateFields).length > 0 && (
              <View style={[styles.precheckList, { backgroundColor: isDark ? tone.surfaceMuted : '#f8fafc' }]}>
                <Text style={[styles.previewMeta, { color: tone.text3, marginBottom: 6 }]}>
                  AI-extracted candidate fields: verify against the record:
                </Text>
                {Object.entries(candidateFields).map(([k, v]) => (
                  <Text key={k} style={[styles.precheckText, { color: tone.text2 }]}>
                    {k}: {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                  </Text>
                ))}
              </View>
            )}
            <TouchableOpacity
              style={[styles.doneButton, { backgroundColor: isDark ? '#ffffff' : tone.ink }]}
              onPress={() => {
                reset();
                onClose();
              }}
            >
              <Text style={[styles.doneText, { color: isDark ? '#0f172a' : '#ffffff' }]}>Done</Text>
            </TouchableOpacity>
          </View>
        )}

        <View style={styles.footer}>
          <Text style={[styles.footerText, { color: tone.text3 }]}>Parity with F-06 / F-12 Document Vault • Secure Upload Pipeline</Text>
        </View>
      </ScrollView>
    </Modal>
  );
};

function extractErrorMessage(error: unknown, fallback: string): string {
  if (error && typeof error === 'object') {
    const e = error as Record<string, unknown>;
    if (typeof e.detail === 'string') return e.detail;
    if (typeof e.title === 'string') return e.title;
  }
  return fallback;
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'ios' ? 48 : 24,
    paddingBottom: 24,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  closeBtn: { padding: 8 },
  closeBtnText: { fontSize: 15, fontWeight: '700' },
  headerTitle: { fontSize: 16, fontWeight: '700' },
  body: { alignItems: 'center', gap: 16, marginTop: 16 },
  formField: { width: '100%', gap: 6 },
  label: { fontSize: 12, fontWeight: '700' },
  input: { width: '100%', borderWidth: 1, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 12, fontSize: 14 },
  primaryButton: { width: '100%', borderRadius: 999, paddingVertical: 14, alignItems: 'center', marginTop: 8 },
  primaryButtonText: { color: '#ffffff', fontWeight: '700', fontSize: 14 },
  errorText: { fontSize: 12, textAlign: 'center' },
  viewfinder: {
    width: 260,
    height: 300,
    borderWidth: 1,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  guideFrame: { alignItems: 'center', gap: 12, paddingHorizontal: 20 },
  reticleText: { fontSize: 12, textAlign: 'center', lineHeight: 18 },
  shutterContainer: { alignItems: 'center', gap: 8 },
  shutterOuter: { width: 68, height: 68, borderRadius: 34, borderWidth: 3, justifyContent: 'center', alignItems: 'center' },
  shutterInner: { width: 52, height: 52, borderRadius: 26 },
  shutterLabel: { fontSize: 12, fontWeight: '600' },
  linkText: { fontSize: 12, fontWeight: '700', marginTop: 6 },
  previewBox: { width: '100%', borderRadius: 20, padding: 20, alignItems: 'center', gap: 8 },
  previewTitle: { fontSize: 16, fontWeight: '700', marginTop: 8 },
  previewMeta: { fontSize: 11 },
  precheckList: { width: '100%', marginTop: 14, gap: 6, padding: 12, borderRadius: 12 },
  precheckText: { fontSize: 11 },
  previewActions: { flexDirection: 'row', gap: 12, width: '100%' },
  retakeButton: { flex: 1, borderRadius: 999, paddingVertical: 14, alignItems: 'center' },
  retakeText: { fontSize: 13, fontWeight: '600' },
  uploadButton: { flex: 2, borderRadius: 999, paddingVertical: 14, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 8 },
  uploadText: { fontSize: 13, fontWeight: '700' },
  uploadBox: { alignItems: 'center', gap: 14, width: '100%', paddingHorizontal: 20, marginTop: 40 },
  uploadTitle: { fontSize: 16, fontWeight: '700', textAlign: 'center' },
  completeBox: { alignItems: 'center', gap: 14, paddingHorizontal: 24, marginTop: 24 },
  completeTitle: { fontSize: 18, fontWeight: '800', textAlign: 'center' },
  completeText: { fontSize: 13, textAlign: 'center', lineHeight: 18 },
  doneButton: { width: '100%', borderRadius: 999, paddingVertical: 14, alignItems: 'center', marginTop: 10 },
  doneText: { fontWeight: '700', fontSize: 14 },
  footer: { alignItems: 'center', marginTop: 24 },
  footerText: { fontSize: 11, textAlign: 'center' },
});
