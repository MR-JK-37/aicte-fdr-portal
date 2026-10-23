export type AppRole =
  | 'institution'
  | 'scrutiny_officer'
  | 'verifier'
  | 'regional_officer'
  | 'competent_authority'
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
