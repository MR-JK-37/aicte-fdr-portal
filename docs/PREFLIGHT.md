# PREFLIGHT.md — what you must provide so nothing has to be faked

Claude Code keeps this file current. Anything missing here stays honestly "not configured" in the product (never simulated). Items marked **$** involve a fee set by the provider — check current pricing; the build never depends on them for core functions.

## A. Needed to build and run everything locally (free)
- [ ] Docker + Docker Compose; Node (version required by the pinned Expo SDK) + pnpm; Python (supported stable) + uv; Git.
- [ ] Android Studio + emulator (or a physical Android phone with USB debugging); Xcode + iOS simulator (macOS only) — or EAS cloud builds.
- [ ] A GitHub repository (CI via Actions).

## B. Push notifications (the mobile advantage)
- [ ] **Android / FCM:** Firebase project (free tier) → add the Android app (package id) → service-account JSON with permission to send via FCM HTTP v1 → set `FCM_PROJECT_ID`, `FCM_SERVICE_ACCOUNT_JSON_PATH`. Real Android device recommended (emulators with Google Play services also work).
- [ ] **iOS / APNs ($):** paid Apple Developer Program membership → App ID with Push Notifications capability → APNs Auth Key (`.p8`), Key ID, Team ID, bundle id → set `APNS_*`. A **real iPhone** is required to receive push (simulator support is limited). Without this, iOS push is `blocked: account` and iOS still works with inbox + SSE.
- [ ] **Web push:** generate VAPID keys; site must be HTTPS (localhost is OK for dev); iOS Safari web push only works for an installed PWA after a user gesture.
- [ ] **Time-sensitive notifications (iOS):** entitlement/capability availability — verify in the Apple developer portal.

## C. Identity
- [ ] Keycloak (self-hosted in compose) — realm export is produced by Phase 1. For production AICTE decides the identity provider (D-08).
- [ ] SMTP/e-mail provider + verified sending domain with SPF/DKIM/DMARC (optional; e-mail stays "not configured" until done).

## D. Bank/finance evidence (real workflow, no fake bank)
- [ ] A sample of **authorised** bank statements in MT940 / CAMT.053 / CSV / XLSX from the AICTE finance team (redacted copies are fine for staging; real ones only on production).
- [ ] Named bank contacts for the legacy-FDR confirmation process and agreement on what proof is sufficient (D-05, D-06). The bank-verifier portal stays disabled until a bank is onboarded.
- [ ] Execution/refund system owner and route (D-03). Until then release stays `EXECUTION_PENDING`.

## E. Policy inputs
- [ ] Current APH (download the official PDF + all amendments/corrigenda) → give to the policy owner to sign the rule register (D-01).
- [ ] Written confirmation of penalty rules, exemptions, delegation limits and release authority (D-01, D-02). Until then: BLOCKED / deny.
- [ ] Official reminder windows, holiday/grace rules, escalation windows (D-10).
- [ ] Authorised AICTE institution list (CSV/XLSX) with official IDs, regions, programmes (D-04).

## F. Stores and distribution
- [ ] Android: EAS internal distribution (APK/AAB) needs no fee; Google Play publishing needs a developer account ($ one-time registration).
- [ ] iOS: TestFlight/App Store need the paid Apple Developer membership ($ annual).
- [ ] App identifiers decided (bundle id / package id) and domains for universal links / App Links (`apple-app-site-association`, `assetlinks.json`).

## G. AI (all optional; the product works with every one of these off)
- [ ] Local model host (Ollama or llama.cpp) if you want Tier-S AI features (D-12).
- [ ] Free-tier API keys (Groq, OpenRouter, Gemini, Cerebras, Cloudflare, Sarvam, …) for Tier-P features — only after reading each provider's current terms; record in `docs/ai-evals/PROVIDERS_VERIFIED.md`.

## H. Hosting
- [ ] Development/staging/hackathon demo: any free or low-cost VM/PaaS that can run containers (document limits). **Production hosting is AICTE's decision (D-09)** — free tiers are not a substitute for approved hosting.
- [ ] Domain + TLS (Let's Encrypt via Caddy is fine for staging).

## I. People/sign-offs (cannot be automated)
- [ ] Policy owner, legal, finance, security/CISO, privacy officer, process owner — named approvers for `docs/GO_LIVE_GATE.md`.
