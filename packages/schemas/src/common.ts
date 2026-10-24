import { z } from 'zod';

/**
 * Hand-written placeholder schemas only — these exist to prove the zod
 * toolchain is wired up correctly for apps/web and apps/mobile, and to give
 * the design-system showcase something real to validate against. They are
 * NOT the domain schemas (Instrument, Institution, ReleaseRequest, …) —
 * those get generated from the backend's real OpenAPI spec once it exists
 * (see README.md). Do not hand-extend this file with domain types; wait
 * for generation so client and server never drift.
 */

export const correlationIdSchema = z.string().min(1);

export const errorEnvelopeSchema = z.object({
  correlationId: correlationIdSchema,
  code: z.string(),
  message: z.string(),
});
export type ErrorEnvelope = z.infer<typeof errorEnvelopeSchema>;

export const moneyPaiseSchema = z.number().int().nonnegative();

export const evidenceAttributeSchema = z.enum([
  'declared',
  'extracted',
  'bankConfirmed',
  'ledgerReconciled',
  'inconclusive',
  'rejected',
]);
export type EvidenceAttribute = z.infer<typeof evidenceAttributeSchema>;

export const statusToneSchema = z.enum(['ok', 'warn', 'info', 'error', 'pending', 'neutral']);
export type StatusTone = z.infer<typeof statusToneSchema>;
