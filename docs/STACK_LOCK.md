# STACK_LOCK.md

Pinned versions + official doc URLs, per MASTER_PROMPT §0.3 ("Write the pinned version and doc URL in docs/STACK_LOCK.md") and the Phase 0 spike gate (§4.2, S-01…S-07). Every row below was checked against current official documentation on 2026-10-24 (WebSearch/WebFetch), not recalled from training data, per CLAUDE.md's "verify, don't recall" rule. Full detail and open gaps are in `docs/spikes/S-01.md` … `S-07.md`; this file is the flat summary.

| Spike | Item | Pinned value | Status | Official doc URL |
|---|---|---|---|---|
| S-01 | Expo SDK | **58** (stable, released 2026-10-15) | PASS | https://expo.dev/changelog/sdk-58 |
| S-01 | React Native | **0.88** (pinned by Expo SDK 58) | PASS | https://expo.dev/changelog/sdk-58 |
| S-01 | Node.js (Expo tooling) | **≥22.13 (22.x) / ≥24.3 (24.x) / 26.x** | PASS | https://expo.dev/changelog/sdk-58 |
| S-01 | iOS platform target | iOS 27 (SDK 58's newest target; confirm minimum-supported floor at build time) | PASS (re-check floor at build) | https://docs.expo.dev/versions/v58.0.0/ |
| S-01 | Android compile/target SDK | not confirmed from fetched excerpt — re-check before pinning `build.gradle` | **open item** | https://docs.expo.dev/versions/v58.0.0/ |
| S-02 | `@expo/ui` | **58.0.22** (tracks SDK 58 line); stable since SDK 56 | PASS for package existence/stability; **PARTIAL** for exact component list | https://docs.expo.dev/versions/latest/sdk/ui/ ; https://expo.dev/blog/expo-ui-stable-sdk-56 |
| S-02 | `@expo/ui` component coverage | Lists, Forms/Section, BottomSheet, DateTimePicker confirmed; **segmented control, search bar, tabs, large-title, dialogs not confirmed present or absent** | **open item — Phase 1 must inspect installed package directly** | https://github.com/expo/expo/tree/main/packages/expo-ui |
| S-02 | Fallback for unconfirmed components | Hand-built RN components matching Material 3 (Android) / HIG (iOS), per MASTER_PROMPT §13.3 | standing fallback | n/a |
| S-03 | `expo-glass-effect` | requires **iOS 26+**; auto-falls back to plain `View` below that or when API unavailable; use `isGlassEffectAPIAvailable()` (runtime) and `isLiquidGlassAvailable()` (compile-time) guards | PASS | https://github.com/expo/expo/blob/main/packages/expo-glass-effect/README.md |
| S-03 | `expo-symbols` | renders SF Symbols (iOS) / substitutes Material Symbols (Android/web); always pass an explicit `fallback` prop or platform-keyed name object; **minimum iOS version not confirmed from fetched docs — re-check** | PASS with one open item | https://docs.expo.dev/versions/latest/sdk/symbols/ |
| S-03 | Reduce Transparency device behavior | **blocked: device** — no physical iOS device to verify | blocked | n/a (PREFLIGHT.md §A) |
| S-04 | FCM HTTP v1 (Android) | auth = service-account OAuth2 token; payload fields `notification`+`data`, `android.notification.channel_id`, `android.priority`, `android.ttl`, `android.collapse_key`; error codes `UNREGISTERED`/`INVALID_ARGUMENT`/`QUOTA_EXCEEDED`/`UNAVAILABLE`/`SENDER_ID_MISMATCH`/`THIRD_PARTY_AUTH_ERROR` — **no drift found vs MASTER_PROMPT §10.5**; literal reference-table re-check recommended before Phase 5 coding | PASS (doc-verified, no device send) | https://firebase.google.com/docs/cloud-messaging/send-message ; https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages |
| S-04 | APNs token-auth (iOS) | contract already specified in MASTER_PROMPT §10.6 (HTTP/2, `.p8` key, `apns-push-type`, `apns-priority`, `apns-topic`, token via `expo-notifications getDevicePushTokenAsync`) | **blocked: account** (no Apple Developer Program membership) and **blocked: device** (no physical iPhone) | n/a (PREFLIGHT.md §B) |
| S-05 | RLS + connection-pool isolation test design | Interleaved two-tenant test on size-1 pool (+ repeated-iteration loop), missing-context zero-rows test, empty-array zero-rows test, worker-role isolation test, sequential-tenant control test — full design in `docs/spikes/S-05.md` for Phase 1 to implement | design complete, implementation deferred to Phase 1 | https://www.postgresql.org/docs/current/sql-set.html ; https://www.postgresql.org/docs/current/ddl-rowsecurity.html |
| S-06 | OCR engine — primary | **PaddleOCR** — Apache-2.0, actively maintained, explicit Hindi(`hi`)/Tamil(`ta`) + 109-language support | PASS | https://github.com/PaddlePaddle/PaddleOCR |
| S-06 | OCR engine — fallback | **Tesseract** — Apache-2.0, mature Indic `traineddata` packs (`hin`, `tam`), lighter CPU-only footprint | PASS | https://tesseractocr.org/ ; https://github.com/tesseract-ocr |
| S-06 | OCR engine — not recommended as primary | docTR (Mindee) — Apache-2.0, actively maintained, but Hindi/Tamil model support **not confirmed** | open item (re-check model zoo if revisited) | https://github.com/mindee/doctr |
| S-06 | OCR accuracy baseline | **deferred to Phase 3** — no sample documents available yet (PREFLIGHT.md §D) | deferred (by design) | n/a |
| S-07 | Material Symbols | Apache-2.0 licensed variable font (`fill`/`weight`/`grade`/`optical size` axes); canonical source `google/material-design-icons`; package `material-symbols` (npm) consumed via per-icon imports for tree-shaking | PASS | https://github.com/google/material-design-icons ; https://developers.google.com/fonts/docs/material_symbols |
| S-07 | RN variable-font-axis runtime support | not confirmed as reliable on current RN line — fallback to static icon variants (outlined/filled swap) recommended; re-check against pinned RN 0.88 at Phase 1 | open item | https://github.com/react-native-community/discussions-and-proposals/issues/829 |
| S-07 | Licence file | Apache-2.0 text from `google/material-design-icons`'s `LICENSE`, shipped at e.g. `packages/<mobile-assets>/THIRD_PARTY_LICENSES/material-symbols-APACHE-2.0.txt` | PASS (placement decision recorded; file itself to be added in Phase 1) | https://github.com/google/material-design-icons/blob/master/LICENSE |

## Blocked items (cannot be device-verified in this environment)
- iOS push round-trip (APNs token-auth): `blocked: account` + `blocked: device` — no Apple Developer Program membership, no physical iPhone. Per PREFLIGHT.md §B.
- `expo-glass-effect` / Reduce Transparency live device behavior: `blocked: device` — no physical iOS device. Per PREFLIGHT.md §A.
- Android/iOS "dev build succeeds" claim in the S-01 one-line spike definition: build execution itself deferred to Phase 1 scaffold/CI (this Phase 0 pass is version-matrix doc-verification only).

## Open re-check items carried into Phase 1 (not blocking, just unverified in this pass)
1. Android `compileSdkVersion`/`targetSdkVersion` for Expo SDK 58 — read `docs.expo.dev/versions/v58.0.0/` directly before editing `android/build.gradle`.
2. `@expo/ui`'s exact exports for segmented control, search bar, tabs, large-title nav, dialogs — read the installed package's own README/types directly (`node_modules/@expo/ui`) before writing any component depending on them; fall back to hand-built components per MASTER_PROMPT §13.3 if absent.
3. `expo-symbols` minimum iOS version.
4. FCM HTTP v1 literal JSON schema + full error-code enum table — re-read `firebase.google.com/docs/reference/fcm/rest/v1/projects.messages` directly before coding the Phase 5 adapter.
5. docTR's Hindi/Tamil model-zoo status, only if PaddleOCR proves operationally unworkable.
6. React Native 0.88's actual support for variable-font axis manipulation (`font-variation-settings` equivalent) on Android, before relying on runtime icon-weight morphing instead of the static-variant fallback.
