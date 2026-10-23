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
