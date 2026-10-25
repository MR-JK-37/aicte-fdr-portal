import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../lib/apiFetch';
import { Instrument, InstrumentStatus } from '../types';

export interface InstrumentApiItem {
  id: string;
  institution_id: string;
  institution_name?: string | null;
  bank_name?: string | null;
  type: string;
  status: string;
  evidence_level: string;
  instrument_number: string;
  amount: number | string;
  issue_date: string | null;
  maturity_date: string | null;
  tenor_months: number | null;
  utr: string | null;
  created_at: string;
  updated_at: string;
}

function mapApiToInstrument(item: InstrumentApiItem): Instrument {
  // Convert Decimal amount (rupees) to paise (or standard number)
  const numAmount = typeof item.amount === 'string' ? parseFloat(item.amount) : item.amount;
  const bankName = item.bank_name || 'State Bank of India';
  const ifscMap: Record<string, string> = {
    'State Bank of India': 'SBIN0000691',
    'Punjab National Bank': 'PUNB0112000',
    'Bank of Baroda': 'BARB0INSTIT',
    'Canara Bank': 'CNRB0001920',
  };

  return {
    id: item.id,
    institution_id: item.institution_id,
    institution_name: item.institution_name || 'Apex Institute of Technology, Bengaluru',
    instrument_number: item.instrument_number,
    type: item.type,
    amount: Math.round(numAmount * 100), // in paise
    bank_name: bankName,
    branch_ifsc: ifscMap[bankName] || 'SBIN0000691',
    issue_date: item.issue_date || '',
    maturity_date: item.maturity_date || '',
    status: item.status as InstrumentStatus,
    evidence_level: item.evidence_level?.startsWith('L2') ? 'L2' : 'L0',
    utr_number: item.utr || undefined,
  };
}

export function useInstruments(filters?: { status?: string; institutionId?: string }) {
  const queryParams = new URLSearchParams();
  if (filters?.status) queryParams.set('status', filters.status);
  if (filters?.institutionId) queryParams.set('institution_id', filters.institutionId);

  const url = `/v1/instruments${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;

  return useQuery({
    queryKey: ['instruments', filters],
    queryFn: async () => {
      const data = await apiFetch<InstrumentApiItem[]>(url);
      return (data || []).map(mapApiToInstrument);
    },
  });
}
