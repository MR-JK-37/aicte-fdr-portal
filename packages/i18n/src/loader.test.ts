import { test } from 'node:test';
import assert from 'node:assert/strict';
import { loadCatalog, getRawCatalog } from './loader';
import { createTranslator, formatIndianNumber, formatINR, formatCroresINR, formatLakhsINR } from './index';

test('english catalog is fully reviewed', () => {
  const raw = getRawCatalog('en');
  const unreviewed = Object.entries(raw).filter(([, v]) => v.status !== 'reviewed');
  assert.deepEqual(unreviewed, [], 'every English key must be status=reviewed (it is the authoritative locale)');
});

test('translation_catalog_status uses only machine-draft or reviewed', () => {
  for (const loc of ['en', 'hi', 'ta'] as const) {
    const raw = getRawCatalog(loc);
    for (const [key, item] of Object.entries(raw)) {
      assert.ok(
        item.status === 'reviewed' || item.status === 'machine-draft',
        `Key ${key} in ${loc} must have status 'reviewed' or 'machine-draft', got ${item.status}`
      );
    }
  }
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

test('Indian digit grouping formats numbers with thousands, lakhs, and crores (R3.5)', () => {
  // 123456789 -> 12,34,56,789
  assert.equal(formatIndianNumber(123456789), '12,34,56,789');
  assert.equal(formatIndianNumber(100000), '1,00,000');
  assert.equal(formatIndianNumber(10000000), '1,00,00,000');
  // Currency
  assert.equal(formatCroresINR(1500000000), '₹1.50 Cr');
  assert.equal(formatLakhsINR(350000000), '₹35.00 Lakh');
});

test('text-expansion test: Hindi and Tamil strings expand within acceptable bounds (< 3.0x of English)', () => {
  const en = loadCatalog('en');
  const hi = loadCatalog('hi', { reviewedOnly: false });
  const ta = loadCatalog('ta', { reviewedOnly: false });

  for (const [key, enMsg] of Object.entries(en)) {
    const hiMsg = hi[key];
    const taMsg = ta[key];

    if (hiMsg && enMsg.length > 5) {
      const hiRatio = hiMsg.length / enMsg.length;
      assert.ok(
        hiRatio < 3.0,
        `Hindi translation for "${key}" expanded ${hiRatio.toFixed(1)}x (> 3.0x limit): "${hiMsg}" vs "${enMsg}"`
      );
    }

    if (taMsg && enMsg.length > 5) {
      const taRatio = taMsg.length / enMsg.length;
      assert.ok(
        taRatio < 3.0,
        `Tamil translation for "${key}" expanded ${taRatio.toFixed(1)}x (> 3.0x limit): "${taMsg}" vs "${enMsg}"`
      );
    }
  }
});
