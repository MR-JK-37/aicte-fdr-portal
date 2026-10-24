export type MobileTab = 'home' | 'cases' | 'inbox' | 'tasks' | 'more';

export type AppRole =
  | 'institution'
  | 'scrutiny_officer'
  | 'verifier'
  | 'regional_officer'
  | 'competent_authority'
  | 'bureau_admin'
  | 'auditor';

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

export interface MobileInstrument {
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
  renewal_lineage?: {
    predecessor_id?: string;
    predecessor_number?: string;
    gap_days: number;
    overlap_days: number;
  };
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

export interface MobileNotification {
  id: string;
  title: string;
  body: string;
  category: 'critical_workflow' | 'deadline' | 'security_account' | 'informational';
  status: NotificationStage;
  created_at: string;
  read_at?: string;
  acknowledged_at?: string;
  action_target?: string;
  instrument_id?: string;
  local_remind_at?: string;
}

export interface MobileTask {
  id: string;
  title: string;
  type: 'intake_review' | 'bank_verify' | 'discrepancy_casework' | 'release_approval' | 'execution_proof';
  instrument_number: string;
  institution_name: string;
  assigned_role: AppRole;
  due_date: string;
  urgency: 'statutory_deadline' | 'high' | 'normal';
}

export interface MobileAppSettings {
  biometric_enabled: boolean;
  biometric_timeout_seconds: number;
  secure_screens_enabled: boolean;
  offline_read_cache_enabled: boolean;
  hide_amounts_on_lock_screen: boolean;
  haptics_enabled: boolean;
  dark_theme: boolean;
  active_language: 'en' | 'hi' | 'ta';
}
