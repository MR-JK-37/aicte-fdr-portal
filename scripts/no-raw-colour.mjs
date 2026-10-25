#!/usr/bin/env node
/**
 * no-raw-colour.mjs (Stream R5 / R5.1 / G-23)
 *
 * Verifies that source files (CSS/TS/TSX/Kotlin/Swift) do not contain raw hex colours
 * outside the designated token set and illustration palettes.
 *
 * Usage: node scripts/no-raw-colour.mjs <dir> [<dir> ...]
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
  'archive-v1-dark',
]);

const SKIP_FILES = new Set([
  'tokens.ts',
  'tokens.css',
  'tokens-entry.css',
  'check_tokens.py',
  'build_preview.py',
  'Kosh.tsx', // Mascot illustrations use specific SVG gradient/shading colors
]);

// Valid token palette hex colors (lowercase)
const ALLOWED_HEX = new Set([
  // Light tokens
  '#dde5fb', '#f4f5fd', '#ffffff', '#fff', '#f8f9fe', '#eceff8', '#e1e6f8', '#e6e9f6', '#80859f',
  '#14141a', '#474b62', '#656981', '#a5a9bf', '#2d63cf', '#e6edff', '#163a8f', '#eff3ff',
  '#1a1a1e', '#c0183f', '#fde4e6', '#b0303f', '#0b7a4b', '#d5f5e5', '#064a2d', '#8f5a00',
  '#ffebc2', '#5c3a00', '#ffdce2', '#8a0f2d', '#5b3fb0', '#e7e0ff', '#33207a', '#555b70',
  '#e8eaf3', '#333749', '#0f1230', '#3b78d8', '#4570da', '#c9d7f7',
  // Dark tokens
  '#080a14', '#0c0e1b', '#151833', '#1b1f3d', '#212649', '#2a305a', '#2b3058', '#7f85a8',
  '#f3f4fb', '#bdc1d8', '#9a9fba', '#5d6283', '#8fb0ff', '#0a1a5e', '#1e2d75', '#dce4ff',
  '#1a2352', '#ff7a93', '#4a0617', '#5a1428', '#ffd9e0', '#47d69a', '#0f3b2a', '#bff3db',
  '#ffb938', '#4a3305', '#ffe2a8', '#33257a', '#a4a9c2', '#2a2f4d', '#dde0ef', '#000000', '#000',
  '#7aa5ff', '#1f2a5e',
  // Brand
  '#050505', '#3b0a6b', '#00eeff',
  // Mascot / preview illustration accents
  '#8fb4ff', '#2556b8', '#1d47a0', '#16213f', '#ffb7c2', '#dbe6ff', '#c4d5fa', '#b4c9f4',
]);

const EXT = new Set(['.ts', '.tsx', '.css', '.kt', '.swift']);
let bad = 0;

function walk(p) {
  const st = statSync(p, { throwIfNoEntry: false });
  if (!st) return;

  if (st.isDirectory()) {
    const dirName = basename(p);
    if (SKIP_DIR.has(dirName)) return;
    for (const n of readdirSync(p)) {
      walk(join(p, n));
    }
    return;
  }

  const fileName = basename(p);
  if (SKIP_FILES.has(fileName)) return;
  if (!EXT.has(extname(p))) return;
  if (/\.(test|spec)\./.test(fileName)) return;

  const text = readFileSync(p, 'utf8');
  const lines = text.split('\n');

  for (let lineNum = 1; lineNum <= lines.length; lineNum++) {
    const line = lines[lineNum - 1];
    // Skip full comment lines
    if (line.trim().startsWith('//') || line.trim().startsWith('*') || line.trim().startsWith('/*')) continue;

    // Search for hex patterns #xxx, #xxxxxx, #xxxxxxxx
    const matches = line.matchAll(/#([0-9a-fA-F]{3,8})\b/g);
    for (const match of matches) {
      const hex = match[0].toLowerCase();
      // If 6 or 8 chars, check standard hex
      const baseHex = hex.length === 9 ? hex.slice(0, 7) : hex;
      if (!ALLOWED_HEX.has(baseHex) && !ALLOWED_HEX.has(hex)) {
        bad++;
        console.error(`RAW COLOUR in ${p.split(sep).join('/')}:${lineNum}: "${match[0]}" is outside token palette`);
      }
    }
  }
}

const dirs = process.argv.slice(2);
if (!dirs.length) {
  console.error('usage: node no-raw-colour.mjs <dir>...');
  process.exit(2);
}

dirs.forEach(walk);
console.log(bad ? `FAILED: ${bad} raw colour violation(s) found` : 'no-raw-colour: OK');
process.exit(bad ? 1 : 0);
