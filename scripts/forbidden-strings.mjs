#!/usr/bin/env node
// forbidden-strings.mjs — fails (exit 1) if removed/simulated features or fake-data markers appear in source or BUILT bundles.
// Usage: node scripts/forbidden-strings.mjs <dir> [<dir> ...]     e.g. apps/web/src apps/mobile/app apps/web/dist apps/mobile/dist backend/app
// Tests, fixtures, docs and this script are skipped. Add a path to ALLOW only with a written reason in docs/DECISIONS.md.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, extname, sep } from 'node:path';

const PATTERNS = [
  [/AI\s*Voice/i, 'AI voice feature'], [/Voice\s*Call/i, 'voice call'], [/Clock\s*Live/i, 'simulated clock control'],
  [/\bSIMULATION\b/, 'simulation badge'], [/Simulat(e|ed|ion)\b/, 'simulate action'], [/Demo\s*FDR/i, 'demo FDR'],
  [/Text[-\s]?to[-\s]?SQL/i, 'text-to-SQL'], [/\bL1 Only\b|\bGold Standard\b|\bL[0-3]\s*(Branch|Only|Verified)\b/, 'L0-L3 evidence ladder'],
  [/AXIS-FDR-\d+|SBI-\d{5,}|HDFC-\d{5,}|PNB-\d{5,}/, 'sample FDR numbers'],
  [/DEMO_MODE|MOCK_BANK_PROVIDER|SIMULATED_CLOCK|FAKE_PUSH_SUCCESS/, 'simulation flag'],
  [/Eligible for Release/, 'hard-coded release eligibility'], [/Sign\s*&\s*Issue\s*QR\s*Certificate/i, 'substitute certificate issuance'],
  [/<option[^>]*>\s*(Bureau Admin|Scrutiny Officer|Competent Authority)\s*<\/option>/, 'client-side role switcher'],
];
const SKIP_DIR = new Set(['node_modules', '.git', '__tests__', 'tests', 'fixtures', 'docs', '.expo', '.next', 'coverage', 'artifacts']);
const EXT = new Set(['.ts', '.tsx', '.js', '.jsx', '.mjs', '.css', '.html', '.json', '.py', '.kt', '.swift', '.md', '.yaml', '.yml', '.txt', '']);
let bad = 0;
function walk(p) {
  const st = statSync(p, { throwIfNoEntry: false }); if (!st) return;
  if (st.isDirectory()) { for (const n of readdirSync(p)) { if (!SKIP_DIR.has(n)) walk(join(p, n)); } return; }
  if (!EXT.has(extname(p)) || st.size > 8e6) return;
  if (/\.(test|spec)\.|forbidden-strings\.mjs$|prod_guard\.py$/.test(p)) return;
  const text = readFileSync(p, 'utf8');
  for (const [re, why] of PATTERNS) { const m = re.exec(text); if (m) { bad++; console.error(`FORBIDDEN (${why}): ${p.split(sep).join('/')} -> "${m[0].slice(0, 60)}"`); } }
}
const dirs = process.argv.slice(2); if (!dirs.length) { console.error('usage: forbidden-strings.mjs <dir>...'); process.exit(2); }
dirs.forEach(walk);
console.log(bad ? `${bad} forbidden marker(s)` : 'forbidden-strings OK');
process.exit(bad ? 1 : 0);
