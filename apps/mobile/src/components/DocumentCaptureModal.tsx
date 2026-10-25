import React, { useState } from 'react';
import { StyleSheet, View, Text, TouchableOpacity, Modal, Platform } from 'react-native';
import { Icon } from '../design-system/Icon';
import { useAppTheme } from '../design-system/theme';

interface DocumentCaptureModalProps {
  visible: boolean;
  onClose: () => void;
  onUploadSuccess?: (docName: string) => void;
}

export const DocumentCaptureModal: React.FC<DocumentCaptureModalProps> = ({
  visible,
  onClose,
  onUploadSuccess,
}) => {
  const { tone, isDark } = useAppTheme();
  const [stage, setStage] = useState<'viewfinder' | 'preview' | 'uploading' | 'completed'>('viewfinder');
  const [progress, setProgress] = useState(0);

  const cardBg = isDark ? tone.surface : '#ffffff';

  const handleCapture = () => {
    setStage('preview');
  };

  const handleStartUpload = () => {
    setStage('uploading');
    setProgress(15);
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setStage('completed');
          if (onUploadSuccess) onUploadSuccess('fdr_document_scan.pdf');
          return 100;
        }
        return prev + 25;
      });
    }, 250);
  };

  const handleReset = () => {
    setStage('viewfinder');
    setProgress(0);
  };

  return (
    <Modal visible={visible} animationType="slide" transparent={false}>
      <View style={[styles.container, { backgroundColor: tone.bg }]}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            onPress={() => {
              handleReset();
              onClose();
            }}
            style={styles.closeBtn}
          >
            <Text style={[styles.closeBtnText, { color: tone.accent }]}>Cancel</Text>
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: tone.text1 }]}>Document Capture (M-05)</Text>
          <View style={{ width: 40 }} />
        </View>

        {/* Viewfinder Stage */}
        {stage === 'viewfinder' && (
          <View style={styles.body}>
            <View
              style={[
                styles.viewfinder,
                {
                  backgroundColor: isDark ? 'rgba(0,0,0,0.5)' : '#f8fafc',
                  borderColor: isDark ? tone.outline : '#e2e8f0',
                },
              ]}
            >
              <View style={[styles.corner, styles.cornerTL, { borderColor: tone.accent }]} />
              <View style={[styles.corner, styles.cornerTR, { borderColor: tone.accent }]} />
              <View style={[styles.corner, styles.cornerBL, { borderColor: tone.accent }]} />
              <View style={[styles.corner, styles.cornerBR, { borderColor: tone.accent }]} />

              <View style={styles.guideFrame}>
                <Icon name="documents" size={44} color={tone.accent} />
                <Text style={[styles.reticleText, { color: tone.text3 }]}>
                  Align physical deposit receipt inside boundary lines
                </Text>
              </View>
            </View>

            {/* Shutter Button */}
            <View style={styles.shutterContainer}>
              <TouchableOpacity
                style={[styles.shutterOuter, { borderColor: tone.accent }]}
                onPress={handleCapture}
              >
                <View style={[styles.shutterInner, { backgroundColor: tone.accent }]} />
              </TouchableOpacity>
              <Text style={[styles.shutterLabel, { color: tone.text3 }]}>Tap to capture</Text>
            </View>
          </View>
        )}

        {/* Review Preview Stage */}
        {stage === 'preview' && (
          <View style={styles.body}>
            <View style={[styles.previewBox, { backgroundColor: cardBg }]}>
              <Icon name="verified" size={40} color="#059669" />
              <Text style={[styles.previewTitle, { color: tone.text1 }]}>Document Captured</Text>
              <Text style={[styles.previewMeta, { color: tone.text3 }]}>
                Resolution: 300 DPI • Perspective corrected • Size: 1.2 MB
              </Text>

              <View style={[styles.precheckList, { backgroundColor: isDark ? tone.surfaceMuted : '#f8fafc' }]}>
                <View style={styles.precheckItem}>
                  <Icon name="success" size={14} color="#059669" />
                  <Text style={[styles.precheckText, { color: tone.text2 }]}>
                    Four corners detected and flattened
                  </Text>
                </View>
                <View style={styles.precheckItem}>
                  <Icon name="success" size={14} color="#059669" />
                  <Text style={[styles.precheckText, { color: tone.text2 }]}>
                    Contrast threshold passed for OCR (M-05)
                  </Text>
                </View>
              </View>
            </View>

            <View style={styles.previewActions}>
              <TouchableOpacity
                style={[styles.retakeButton, { backgroundColor: isDark ? tone.surfaceMuted : '#f1f5f9' }]}
                onPress={handleReset}
              >
                <Text style={[styles.retakeText, { color: tone.text2 }]}>Retake</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.uploadButton, { backgroundColor: isDark ? '#ffffff' : tone.ink }]}
                onPress={handleStartUpload}
              >
                <Icon name="upload" size={16} color={isDark ? '#0f172a' : '#ffffff'} />
                <Text style={[styles.uploadText, { color: isDark ? '#0f172a' : '#ffffff' }]}>
                  Upload & Queue
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Uploading Stage */}
        {stage === 'uploading' && (
          <View style={styles.uploadBox}>
            <Icon name="upload" size={48} color={tone.accent} />
            <Text style={[styles.uploadTitle, { color: tone.text1 }]}>Uploading Scanned Dossier</Text>
            <Text style={[styles.uploadProgress, { color: tone.accent }]}>{progress}%</Text>
            <View style={[styles.progressBarBg, { backgroundColor: tone.accentContainer }]}>
              <View style={[styles.progressBarFill, { width: `${progress}%`, backgroundColor: tone.accent }]} />
            </View>
            <Text style={[styles.uploadNote, { color: tone.text3 }]}>
              Encrypting AES-GCM-256 before transmission to object store.
            </Text>
          </View>
        )}

        {/* Completed Stage */}
        {stage === 'completed' && (
          <View style={styles.completeBox}>
            <Icon name="success" size={56} color="#059669" />
            <Text style={[styles.completeTitle, { color: tone.text1 }]}>Upload Completed</Text>
            <Text style={[styles.completeText, { color: tone.text3 }]}>
              Scanned receipt has been attached to the case queue with verification hash.
            </Text>
            <TouchableOpacity
              style={[styles.doneButton, { backgroundColor: isDark ? '#ffffff' : tone.ink }]}
              onPress={() => {
                handleReset();
                onClose();
              }}
            >
              <Text style={[styles.doneText, { color: isDark ? '#0f172a' : '#ffffff' }]}>Done</Text>
            </TouchableOpacity>
          </View>
        )}

        <View style={styles.footer}>
          <Text style={[styles.footerText, { color: tone.text3 }]}>
            Parity with F-06 / F-12 Document Vault • Secure Upload Pipeline
          </Text>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'ios' ? 48 : 24,
    paddingBottom: 24,
    justifyContent: 'space-between',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  closeBtn: {
    padding: 8,
  },
  closeBtnText: {
    fontSize: 15,
    fontWeight: '700',
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '700',
  },
  body: {
    alignItems: 'center',
    gap: 24,
  },
  viewfinder: {
    width: 260,
    height: 360,
    borderWidth: 1,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  corner: {
    position: 'absolute',
    width: 24,
    height: 24,
  },
  cornerTL: {
    top: -2,
    left: -2,
    borderTopWidth: 3,
    borderLeftWidth: 3,
    borderTopLeftRadius: 8,
  },
  cornerTR: {
    top: -2,
    right: -2,
    borderTopWidth: 3,
    borderRightWidth: 3,
    borderTopRightRadius: 8,
  },
  cornerBL: {
    bottom: -2,
    left: -2,
    borderBottomWidth: 3,
    borderLeftWidth: 3,
    borderBottomLeftRadius: 8,
  },
  cornerBR: {
    bottom: -2,
    right: -2,
    borderBottomWidth: 3,
    borderRightWidth: 3,
    borderBottomRightRadius: 8,
  },
  guideFrame: {
    alignItems: 'center',
    gap: 12,
    paddingHorizontal: 20,
  },
  reticleText: {
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 18,
  },
  shutterContainer: {
    alignItems: 'center',
    gap: 8,
  },
  shutterOuter: {
    width: 68,
    height: 68,
    borderRadius: 34,
    borderWidth: 3,
    justifyContent: 'center',
    alignItems: 'center',
  },
  shutterInner: {
    width: 52,
    height: 52,
    borderRadius: 26,
  },
  shutterLabel: {
    fontSize: 12,
    fontWeight: '600',
  },
  previewBox: {
    width: '100%',
    borderRadius: 20,
    padding: 20,
    alignItems: 'center',
    gap: 8,
    shadowColor: '#1e1b4b',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 3,
  },
  previewTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginTop: 8,
  },
  previewMeta: {
    fontSize: 11,
  },
  precheckList: {
    width: '100%',
    marginTop: 14,
    gap: 8,
    padding: 12,
    borderRadius: 12,
  },
  precheckItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  precheckText: {
    fontSize: 11,
  },
  previewActions: {
    flexDirection: 'row',
    gap: 12,
    width: '100%',
  },
  retakeButton: {
    flex: 1,
    borderRadius: 999,
    paddingVertical: 14,
    alignItems: 'center',
  },
  retakeText: {
    fontSize: 13,
    fontWeight: '600',
  },
  uploadButton: {
    flex: 2,
    borderRadius: 999,
    paddingVertical: 14,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  uploadText: {
    fontSize: 13,
    fontWeight: '700',
  },
  uploadBox: {
    alignItems: 'center',
    gap: 14,
    width: '100%',
    paddingHorizontal: 20,
  },
  uploadTitle: {
    fontSize: 16,
    fontWeight: '700',
  },
  uploadProgress: {
    fontSize: 14,
    fontWeight: '700',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  progressBarBg: {
    width: '100%',
    height: 8,
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
  },
  uploadNote: {
    fontSize: 11,
    textAlign: 'center',
    marginTop: 8,
  },
  completeBox: {
    alignItems: 'center',
    gap: 14,
    paddingHorizontal: 24,
  },
  completeTitle: {
    fontSize: 18,
    fontWeight: '800',
    textAlign: 'center',
  },
  completeText: {
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 18,
  },
  doneButton: {
    width: '100%',
    borderRadius: 999,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 10,
  },
  doneText: {
    fontWeight: '700',
    fontSize: 14,
  },
  footer: {
    alignItems: 'center',
  },
  footerText: {
    fontSize: 11,
    textAlign: 'center',
  },
});
