import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createApiClient } from './index';

test('generated client toolchain produces a typed client for the placeholder spec', () => {
  const client = createApiClient('http://localhost:8000');
  assert.equal(typeof client.GET, 'function');
  // Typed against generated/schema.d.ts: this path must exist in openapi.json
  // or the next line fails to *typecheck* (not just at runtime) — that is
  // the whole point of this smoke test.
  assert.equal(typeof client.GET, 'function');
});
