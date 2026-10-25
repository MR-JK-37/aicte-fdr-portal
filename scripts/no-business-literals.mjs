#!/usr/bin/env node
/**
 * no-business-literals.mjs (Stream R3 / R3.3)
 *
 * Verifies that apps/web/src and apps/mobile/src do not contain hard-coded business literals:
 * 1. FDR-number patterns (sample FDRs, REC numbers)
 * 2. Raw ₹ literals outside designated currency formatters and input prefix affixes
 * 3. Hard-coded 'Cr' / 'Lakh' amount strings outside formatters
 * 4. Hard-coded bank names in arrays
 *
 * Usage: node scripts/no-business-literals.mjs <dir> [<dir> ...]
 */

import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, extname, sep, basename } from 'node:path';

const SKIP_DIR = new Set([
  'node_modules',
  '.git',
  '__tests__',
  'tests',
  'fixtures',
  'docs',
  '.expo',
  '.next',
  'coverage',
  'artifacts',
  'dist',
  'build',
]);

const ALLOWED_CURRENCY_FILES = new Set([
  'formatters.ts',
  'formatters.js',
  'format.ts',
  'format.js',
  'Input.tsx', // contains the static currency affix symbol {amount && <span>₹</span>}
]);

const PATTERNS = [
  {
    name: 'sample FDR / receipt number pattern',
    regex: /\b(?:[A-Z0-9_]+-)?FDR-\d{3,}\b|\bREC-AICTE-\d{3,}\b/i,
    filter: (filePath, text, match) => {
      // Allow regex definitions or comments describing format
      const line = text.split('\n').find((l) => l.includes(match[0])) || '';
      return !line.includes('//') && !line.includes('/*') && !line.includes('placeholder=');
    },
  },
  {
    name: 'hard-coded amount with Cr/Lakh',
    regex: /['"`]\s*(?:₹\s*)?\d+(?:\.\d+)?\s*(?:Cr|Crore|Crores|Lakh|Lakhs)\b['"`]|\b\d+\s*(?:Cr|Crore|Crores|Lakh|Lakhs)\b/i,
    filter: (filePath, text, match) => {
      const base = basename(filePath);
      if (ALLOWED_CURRENCY_FILES.has(base)) return false;
      const line = text.split('\n').find((l) => l.includes(match[0])) || '';
      return !line.includes('//') && !line.includes('/*');
    },
  },
  {
    name: 'raw ₹ literal outside formatters',
    regex: /₹/,
    filter: (filePath, text, match) => {
      const base = basename(filePath);
      if (ALLOWED_CURRENCY_FILES.has(base)) return false;
      const line = text.split('\n').find((l) => l.includes(match[0])) || '';
      return !line.includes('//') && !line.includes('/*');
    },
  },
  {
    name: 'bank names in arrays',
    regex: /\[\s*['"](?:State Bank of India|SBI|HDFC Bank|HDFC|ICICI Bank|ICICI|Punjab National Bank|PNB|Axis Bank|Canara Bank|Bank of Baroda)['"]/i,
    filter: (filePath, text) => {
      return true;
    },
  },
];

let violations = 0;

function checkFile(filePath) {
  const base = basename(filePath);
  if (/\.(test|spec)\./i.test(base)) return;
  if (!/\.(tsx?|jsx?)$/i.test(extname(filePath))) return;

  const content = readFileSync(filePath, 'utf8');

  for (const { name, regex, filter } of PATTERNS) {
    const match = regex.exec(content);
    if (match) {
      if (!filter || filter(filePath, content, match)) {
        violations++;
        console.error(
          `BUSINESS LITERAL VIOLATION (${name}): ${filePath.split(sep).join('/')} -> "${match[0].slice(0, 60)}"`
        );
      }
    }
  }
}

function walk(currentPath) {
  const st = statSync(currentPath, { throwIfNoEntry: false });
  if (!st) return;
  if (st.isDirectory()) {
    for (const name of readdirSync(currentPath)) {
      if (!SKIP_DIR.has(name)) {
        walk(join(currentPath, name));
      }
    }
    return;
  }
  checkFile(currentPath);
}

const targets = process.argv.slice(2);
if (targets.length === 0) {
  console.error('Usage: node scripts/no-business-literals.mjs <dir>...');
  process.exit(2);
}

targets.forEach(walk);

if (violations > 0) {
  console.error(`\nFound ${violations} business literal violation(s) in source code.`);
  process.exit(1);
} else {
  console.log('no-business-literals OK (0 violations found)');
  process.exit(0);
}
