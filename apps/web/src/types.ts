export type AppRole =
  // 13 canonical roles (MASTER_PROMPT §1.3 / AUTH_ROLES_MATRIX §1)
  | 'org_admin'
  | 'institution_submitter'
  | 'institution_viewer'
  | 'intake_officer'
  | 'scrutiny_officer'
  | 'finance_verifier'
  | 'regional_supervisor'
  | 'competent_authority'
  | 'audit_reviewer'
  | 'identity_admin'
  | 'platform_operator'
  | 'integration_service'
  | 'bank_verifier'
  // Phase 0 legacy aliases
  | 'institution'
  | 'verifier'
  | 'regional_officer'
  | 'bureau_admin'
  | 'auditor'
  | 'bank_user';

export type InstrumentStatus =
  | 'DRAFT'
  | 'PENDING_VERIFICATION'
  | 'ACTIVE'
  | 'EXPIRING'
  | 'MATURED'
  | 'RENEWED'
  | 'RELEASE_REQUESTED'
  | 'RELEASED'
  | 'FORFEITED';

export type EvidenceLevel = 'L0' | 'L1' | 'L2' | 'L3';

export interface Instrument {
  id: string;
  institution_id: string;
  institution_name: string;
  instrument_number: string;
  type: string;
  amount: number; // in paise
  bank_name: string;
  branch_ifsc: string;
  issue_date: string;
  maturity_date: string;
  status: InstrumentStatus;
  evidence_level: EvidenceLevel;
  joint_account_holder?: string;
  utr_number?: string;
}

export interface VerificationRecord {
  id: string;
  instrument_id: string;
  method: 'portal_ocr' | 'bank_confirmation' | 'statement_reconciliation' | 'sfms';
  evidence_level: EvidenceLevel;
  status: 'pending' | 'verified' | 'mismatch';
  verified_at: string;
  discrepancies?: string[];
}

export interface Discrepancy {
  id: string;
  instrument_id: string;
  institution_name: string;
  field_name: string;
  declared_value: string;
  confirmed_value: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'open' | 'resolved' | 'overridden';
}

export interface ReminderItem {
  id: string;
  instrument_number: string;
  institution_name: string;
  window: string;
  scheduled_for: string;
  ladder_step: number;
  current_channel: string;
  status: 'pending' | 'sent' | 'acknowledged';
  acknowledged_at?: string;
}

export interface AuditEntry {
  id: number;
  action: string;
  entity_type: string;
  entity_id: string;
  row_hash: string;
  prev_hash: string;
  created_at: string;
  actor_id?: string;
  actor_type?: string;
  details?: Record<string, any>;
}

export interface ReleaseChecklist {
  term_served: boolean;
  term_citation: string;
  no_open_discrepancies: boolean;
  discrepancy_citation: string;
  no_pending_scrutiny: boolean;
  scrutiny_citation: string;
  no_unpaid_penalties: boolean;
  penalty_citation: string;
  eligible: boolean;
}

export type NotificationStage =
  | 'CREATED'
  | 'QUEUED'
  | 'PROVIDER_ACCEPTED'
  | 'PROVIDER_FAILED'
  | 'DEVICE_RECEIVED'
  | 'OPENED'
  | 'ACKNOWLEDGED'
  | 'ACTIONED';

export interface InAppNotification {
  id: string;
  title: string;
  body: string;
  category: 'critical_workflow' | 'deadline' | 'security_account' | 'informational';
  status: NotificationStage;
  created_at: string;
  read_at?: string;
  acknowledged_at?: string;
  action_url?: string;
  instrument_id?: string;
}

export interface SearchFilterState {
  query: string;
  status: string[];
  bank: string[];
  minAmountPaise?: number;
  maxAmountPaise?: number;
  evidenceLevel: string[];
  sortBy: 'maturity_date' | 'amount' | 'created_at';
  sortOrder: 'asc' | 'desc';
}

export interface SavedViewPreset {
  id: string;
  name: string;
  description: string;
  filters: Partial<SearchFilterState>;
  badgeCount?: number;
}

export interface ReportDefinition {
  id: string;
  title: string;
  description: string;
  frequency: 'daily' | 'weekly' | 'monthly' | 'on_demand';
  category: 'compliance' | 'finance' | 'audit' | 'reconciliation';
  supportedFormats: ('csv' | 'json' | 'pdf')[];
}

export interface GeneratedReport {
  id: string;
  reportId: string;
  title: string;
  format: 'csv' | 'json' | 'pdf';
  generatedAt: string;
  fileSizeBytes: number;
  downloadUrl: string;
  status: 'ready' | 'generating' | 'failed';
}

export interface ConnectorHealth {
  id: string;
  name: string;
  type: 'core_banking' | 'pfms' | 'digilocker' | 'push_fcm' | 'push_apns' | 'email';
  status: 'healthy' | 'degraded' | 'unconfigured' | 'outage';
  latencyMs: number;
  lastChecked: string;
  details: string;
}

export interface SupportTicket {
  id: string;
  subject: string;
  category: 'handbook_query' | 'deposit_discrepancy' | 'release_escalation' | 'technical_issue';
  priority: 'low' | 'medium' | 'high' | 'statutory';
  status: 'open' | 'under_scrutiny' | 'resolved';
  createdAt: string;
  updatedAt: string;
}

export interface DPDPRightsRequest {
  id: string;
  requestType: 'access_data' | 'rectify_record' | 'retention_review' | 'nomination_update';
  subjectName: string;
  status: 'submitted' | 'under_review' | 'processed' | 'rejected';
  submittedAt: string;
  statutoryDaysRemaining: number;
}

export interface PublicReceiptPayload {
  receiptNumber: string;
  institutionAicteCode: string;
  institutionName: string;
  instrumentNumberMasked: string;
  amountPaise: number;
  bankName: string;
  timestampUtc: string;
  ed25519Signature: string;
  isSignatureValid: boolean;
  status: 'GENUINE_AICTE_SEALED' | 'INVALID_OR_TAMPERED';
}

