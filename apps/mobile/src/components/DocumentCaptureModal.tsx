import React, { useState } from 'react';
import { StyleSheet, View, Text, TouchableOpacity, Modal, Platform } from 'react-native';
import { Icon } from '../design-system/Icon';

interface DocumentCaptureModalProps {
  visible: boolean;
  onClose: () => void;
  onUploadSuccess?: (docName: string) => void;
}

export const DocumentCaptureModal: React.FC<DocumentCaptureModalProps> = ({ visible, onClose, onUploadSuccess }) => {
  const [stage, setStage] = useState<'viewfinder' | 'preview' | 'uploading' | 'completed'>('viewfinder');
  const [progress, setProgress] = useState(0);

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
          if (onUploadSuccess) onUploadSuccess('FDR_Scan_AXIS_2026.pdf');
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
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            onPress={() => {
              handleReset();
              onClose();
            }}
            style={styles.closeBtn}
          >
            <Text style={styles.closeBtnText}>Cancel</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Document Capture (M-05)</Text>
          <View style={{ width: 40 }} />
        </View>

        {/* Viewfinder Stage */}
        {stage === 'viewfinder' && (
          <View style={styles.body}>
            <View style={styles.cameraBox}>
              <View style={styles.guideLines}>
                <Text style={styles.guideText}>Position Fixed Deposit Receipt inside frame</Text>
                <View style={styles.autoCropBadge}>
                  <Icon name="verified" size={14} color="#00eeff" />
                  <Text style={styles.autoCropText}>Edge-Detection & Perspective Active</Text>
                </View>
              </View>
            </View>

            <View style={styles.captureControls}>
              <TouchableOpacity style={styles.shutterButton} onPress={handleCapture}>
                <View style={styles.shutterInner} />
              </TouchableOpacity>
              <Text style={styles.shutterLabel}>Tap to Capture Document</Text>
            </View>
          </View>
        )}

        {/* Preview & Pre-check Stage */}
        {stage === 'preview' && (
          <View style={styles.body}>
            <View style={styles.previewBox}>
              <Icon name="documents" size={64} color="#00eeff" />
              <Text style={styles.previewTitle}>FDR_Captured_Page_1.pdf</Text>
              <Text style={styles.previewMeta}>2480 × 3508 • 300 DPI • 1.8 MB</Text>

              {/* Local Pre-check Results */}
              <View style={styles.precheckList}>
                <View style={styles.precheckItem}>
                  <Icon name="success" size={14} color="#3ddc97" />
                  <Text style={styles.precheckText}>Perspective & Skew Corrected (0.2°)</Text>
                </View>
                <View style={styles.precheckItem}>
                  <Icon name="success" size={14} color="#3ddc97" />
                  <Text style={styles.precheckText}>Blur & Legibility Score: 98% (Pass)</Text>
                </View>
                <View style={styles.precheckItem}>
                  <Icon name="success" size={14} color="#3ddc97" />
                  <Text style={styles.precheckText}>Size within statutory 10 MB limit</Text>
                </View>
              </View>
            </View>

            <View style={styles.previewActions}>
              <TouchableOpacity style={styles.retakeButton} onPress={handleReset}>
                <Text style={styles.retakeText}>Retake</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.uploadButton} onPress={handleStartUpload}>
                <Icon name="upload" size={16} color="#050505" />
                <Text style={styles.uploadText}>Upload to Vault</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Uploading Stage */}
        {stage === 'uploading' && (
          <View style={styles.body}>
            <View style={styles.uploadBox}>
              <Icon name="sync" size={48} color="#00eeff" />
              <Text style={styles.uploadTitle}>Uploading Chunked Payload</Text>
              <Text style={styles.uploadProgress}>{progress}% completed</Text>

              {/* Progress Bar */}
              <View style={styles.progressBarBg}>
                <View style={[styles.progressBarFill, { width: `${progress}%` }]} />
              </View>

              <Text style={styles.uploadNote}>
                Resumable chunked upload with background continuation (M-05)
              </Text>
            </View>
          </View>
        )}

        {/* Completed Stage */}
        {stage === 'completed' && (
          <View style={styles.body}>
            <View style={styles.completeBox}>
              <Icon name="success" size={56} color="#3ddc97" />
              <Text style={styles.completeTitle}>Document Uploaded & Quarantined</Text>
              <Text style={styles.completeText}>
                File safely staged in S3 storage. ClamAV antivirus scanning and local OCR extraction initiated.
              </Text>
            </View>

            <TouchableOpacity
              style={styles.doneButton}
              onPress={() => {
                handleReset();
                onClose();
              }}
            >
              <Text style={styles.doneText}>Return to App</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Local pre-checks do not replace ClamAV virus scanning and server-side quarantine isolation.
          </Text>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#050505',
    paddingHorizontal: 20,
    paddingTop: 48,
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
    color: '#00eeff',
    fontWeight: '600',
    fontSize: 14,
  },
  headerTitle: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
  },
  body: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 24,
  },
  cameraBox: {
    width: '100%',
    height: 380,
    backgroundColor: '#0c0716',
    borderRadius: 20,
    borderWidth: 1.5,
    borderColor: 'rgba(0, 238, 255, 0.4)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  guideLines: {
    alignItems: 'center',
    gap: 12,
  },
  guideText: {
    color: '#94a3b8',
    fontSize: 12,
    textAlign: 'center',
  },
  autoCropBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(0, 238, 255, 0.1)',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(0, 238, 255, 0.3)',
  },
  autoCropText: {
    color: '#00eeff',
    fontSize: 11,
    fontWeight: '600',
  },
  captureControls: {
    alignItems: 'center',
    gap: 8,
  },
  shutterButton: {
    width: 68,
    height: 68,
    borderRadius: 34,
    borderWidth: 4,
    borderColor: '#00eeff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  shutterInner: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: '#ffffff',
  },
  shutterLabel: {
    color: '#94a3b8',
    fontSize: 12,
  },
  previewBox: {
    width: '100%',
    backgroundColor: '#151316',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(0, 238, 255, 0.25)',
    padding: 20,
    alignItems: 'center',
    gap: 8,
  },
  previewTitle: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '700',
    marginTop: 8,
  },
  previewMeta: {
    color: '#94a3b8',
    fontSize: 11,
  },
  precheckList: {
    width: '100%',
    marginTop: 14,
    gap: 8,
    backgroundColor: '#0c0716',
    padding: 12,
    borderRadius: 12,
  },
  precheckItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  precheckText: {
    color: '#e2e8f0',
    fontSize: 11,
  },
  previewActions: {
    flexDirection: 'row',
    gap: 12,
    width: '100%',
  },
  retakeButton: {
    flex: 1,
    backgroundColor: '#1e293b',
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#475569',
  },
  retakeText: {
    color: '#f8fafc',
    fontSize: 13,
    fontWeight: '600',
  },
  uploadButton: {
    flex: 2,
    backgroundColor: '#00eeff',
    borderRadius: 12,
    paddingVertical: 12,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  uploadText: {
    color: '#050505',
    fontSize: 13,
    fontWeight: '700',
  },
  uploadBox: {
    alignItems: 'center',
    gap: 12,
    width: '100%',
    paddingHorizontal: 20,
  },
  uploadTitle: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
  },
  uploadProgress: {
    color: '#00eeff',
    fontSize: 13,
    fontWeight: '600',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  progressBarBg: {
    width: '100%',
    height: 8,
    backgroundColor: '#1e293b',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#00eeff',
  },
  uploadNote: {
    color: '#64748b',
    fontSize: 11,
    textAlign: 'center',
    marginTop: 8,
  },
  completeBox: {
    alignItems: 'center',
    gap: 12,
    paddingHorizontal: 24,
  },
  completeTitle: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
    textAlign: 'center',
  },
  completeText: {
    color: '#94a3b8',
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 18,
  },
  doneButton: {
    width: '100%',
    backgroundColor: '#00eeff',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
  },
  doneText: {
    color: '#050505',
    fontWeight: '700',
    fontSize: 14,
  },
  footer: {
    alignItems: 'center',
  },
  footerText: {
    color: '#475569',
    fontSize: 10,
    textAlign: 'center',
  },
});
