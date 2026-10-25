import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../lib/apiFetch';

export interface ReleaseRequestSummary {
  id: string;
  institution_id: string;
  institution_name: string;
  instrument_id: string;
  instrument_number: string;
  amount: number | string;
  status: string;
  recommendation: string | null;
  recommendation_reason: string | null;
  recommended_at: string | null;
  decision: string | null;
  decision_reason: string | null;
  created_at: string;
}

export interface ReleaseChecklistItemOut {
  rule_id: string;
  label: string;
  status: string;
  reason: string | null;
}

export interface ClearanceOut {
  id: string;
  cell: string;
  source: string;
  status: string;
  outcome: string | null;
}

export interface ReleaseRequestDetail extends ReleaseRequestSummary {
  checklist: ReleaseChecklistItemOut[];
  clearances: ClearanceOut[];
}

export function useReleaseRequests(status?: string) {
  const query = status ? `?status=${encodeURIComponent(status)}` : '';
  return useQuery({
    queryKey: ['release-requests', status ?? null],
    queryFn: () => apiFetch<ReleaseRequestSummary[]>(`/v1/release-requests${query}`),
  });
}

export function useReleaseRequestDetail(id: string | null) {
  return useQuery({
    queryKey: ['release-request', id],
    queryFn: () => apiFetch<ReleaseRequestDetail>(`/v1/release-requests/${id}`),
    enabled: !!id,
  });
}
