---
name: ui-screenshot-qa
description: Capture and check the UI screenshot matrix (web viewports × themes × locales; mobile devices) for the FDR portal against the design spec.
---
1. Web: run the Playwright visual suite (`pnpm --filter web e2e:visual`) producing `artifacts/screenshots/web/<route>__<w>x<h>__<theme>__<locale>.png` for widths 390, 768, 1280, 1920; themes light, dark, dark+reduced-transparency; locales en, hi, ta.
2. Mobile: capture from iOS simulator (iPhone + iPad) and Android emulator (phone + tablet/foldable) in light/dark and font scale 100%/200%.
3. Check for: glass only on nav/controls, contrast, clipped Hindi/Tamil, touch targets, icon source rules (Android Material Symbols only), empty/error/forbidden states.
4. Hand the folder to the `design-reviewer` subagent and fix every FAIL.
