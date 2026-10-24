import { test } from 'node:test';
import assert from 'node:assert/strict';
import { loadCatalog, getRawCatalog } from './loader';
import { createTranslator } from './index';

test('english catalog is fully reviewed', () => {
  const raw = getRawCatalog('en');
  const unreviewed = Object.entries(raw).filter(([, v]) => v.status !== 'reviewed');
  assert.deepEqual(unreviewed, [], 'every English key must be status=reviewed (it is the authoritative locale)');
});

test('reviewed-only hindi catalog falls back to english for machine-draft keys', () => {
  const hi = loadCatalog('hi', { reviewedOnly: true });
  const en = loadCatalog('en');
  // At launch every hi key is machine-draft, so reviewed-only hi === en.
  assert.deepEqual(hi, en);
});

test('non-reviewed-only hindi catalog shows the draft text', () => {
  const hi = loadCatalog('hi', { reviewedOnly: false });
  assert.notEqual(hi['app.name'], loadCatalog('en')['app.name']);
});

test('createTranslator formats ICU plurals', () => {
  const t = createTranslator('en');
  assert.equal(t('count.items', { count: 1 }), '1 item');
  assert.equal(t('count.items', { count: 3 }), '3 items');
});

test('createTranslator surfaces missing keys loudly instead of silently', () => {
  const t = createTranslator('en');
  assert.equal(t('does.not.exist'), '⟦missing:does.not.exist⟧');
});
