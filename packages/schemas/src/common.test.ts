import { test } from 'node:test';
import assert from 'node:assert/strict';
import { errorEnvelopeSchema, evidenceAttributeSchema } from './common';

test('zod toolchain parses a valid error envelope', () => {
  const parsed = errorEnvelopeSchema.parse({ correlationId: 'abc-123', code: 'NOT_FOUND', message: 'nope' });
  assert.equal(parsed.code, 'NOT_FOUND');
});

test('zod rejects an unknown evidence attribute', () => {
  assert.throws(() => evidenceAttributeSchema.parse('verified'));
});
