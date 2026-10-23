# AICTE Security Deposit / FDR Management Portal — Build Plan

Source of truth for scope: `Blueprint.txt` (project spec) and the original brief (10 phases).
This file tracks what each phase requires, its acceptance criteria, and status.
`progress.md` (repo root) has the running session log.

## Repo layout

```
apps/web        React + Vite + TS SPA
apps/mobile     Expo (React Native) app
services/api    FastAPI modular monolith (institutions, instruments, documents,
                verification, lifecycle, releases, notifications, calls,
                agents, audit, reports, admin)
services/worker Celery worker + beat (reminders, OCR, agents)
services/voice  Pipecat voice bot process
packages/shared Shared TS types/zod schemas/i18n catalogs (web+mobile)
infra/docker    Compose files, Caddyfile, provisioning
docs/           plan.md, ADRs, runbooks, DPIA, user manuals
scripts/        check_providers.py, deploy scripts, backup/restore
```

## Phases (status)

- [x] **Phase 1 — Foundation.** Turborepo+pnpm root, uv-managed Python services,
      Docker Compose (db, valkey, minio, keycloak, api, worker, beat, caddy),
      GitHub Actions CI, pre-commit, `.env.example` handling.
      Accept: `docker compose up` works; `/health` is green.
- [x] **Phase 2 — Data, auth, audit.** Full schema (institutions, trusts,
      instruments, banks/branches, documents, verification_records,
      discrepancies, scrutiny_observations, reminders, escalations,
      release_requests, penalties, app_users, device_tokens, consent_records,
      notification_log, call_sessions, agent_runs, audit_log, sim_clock).
      RLS per role. Keycloak OIDC + mandatory TOTP for officers.
      Accept: pytest proves cross-tenant reads blocked; audit chain verifier
      detects tampering.
- [x] **Phase 3 — Core workflows.** Lifecycle state machine, rules engine,
      shortfall checker, release-eligibility checker w/ clause citations,
      maker-checker release approval.
      Accept: unit tests cover every transition + penalty path.
- [x] **Phase 4 — Documents & AI extraction** (extraction step uses a
      placeholder deterministic extractor pending the Phase 6 LLM gateway
      — see progress.md). Upload→quarantine→AV/magic-byte/
      sanitize→hash/pHash→encrypted store→OCR→redact→LLM→Pydantic→rules→L1
      confirm. Forgery/duplicate signals.
      Accept: 100 synthetic FDRs, 8 layouts, ≥95% field accuracy; seeded
      defects detected with explanations.
- [x] **Phase 5 — Verification (SIMULATED bank side).** Mock bank-confirmation
      API + mock SFMS/NeSL. Real: AICTE bank-statement CSV import w/ UTR match.
      Accept: declared-vs-confirmed diff view; evidence badges.
- [x] **Phase 6a — LLM gateway.** `llm_gateway` module, provider registry,
      discovery/health-check (`scripts/check_providers.py`), routing/
      fallback, resilience (buckets, breaker, backoff, cache, repair-retry,
      human queue), redaction (regex, not Presidio — see progress.md).
      Verified live against Groq (real key, real API). Langfuse traces and
      the LangGraph agents are **not yet built** — see Phase 6b below.
- [x] **Phase 6b — LangGraph agents** (partial — see progress.md for what's
      deferred to Phase 7/8). Document Intelligence (real LLM extractor,
      swapped into Phase 4's pipeline), Forgery/Anomaly explanation,
      Compliance RAG (synthetic corpus, lexical embeddings — real gaps,
      documented), Release-eligibility (genuine LangGraph `interrupt()` +
      resume, maker-checker enforced on resume), Insight/text2sql
      (sqlglot validation, allow-listed views, dedicated read-only DB
      role, 5s timeout, LIMIT). Maturity/Reminder, Escalation and Voice
      agents are Phase 7/8's own job (scheduling and telephony
      respectively) and were not duplicated here. No Langfuse export yet
      (needs another external account).
- [x] **Phase 7 — Reminders/escalation/notifications.** Celery Beat 15-min +
      sim clock, T-90/60/30/7/0 windows, full ladder (in-app→FCM→in-app AI
      call→email→flagged PSTN/WhatsApp→Bureau). FCM push fails closed
      (no Firebase project configured — needs an external account, not
      done this session); every other step is real. Consolidated
      services/worker into services/api (see progress.md — the original
      split couldn't actually run DB-aware tasks).
      Accept met: sim-clock +300d fires full ladder (tested); idempotent
      (tested); quiet hours respected (tested, incl. edge cases);
      localized text en/hi/ta (templated, not LLM-generated — facts stay
      exact).
- [x] **Phase 8 — Voice agent.** Pipecat + Sarvam (Bhashini/AI4Bharat
      fallback), FCM-triggered full-screen call UI → WebRTC, disclosure→
      consent→PIN→brief→Q&A→confirm→audit. speak_amount/speak_date en/hi/ta.
      Accept: live call en/hi/ta over mobile data, interruptions work, wrong
      PIN locks channel, ack in audit log. PSTN adapter flagged.
- [x] **Phase 9 — Web UI, then mobile UI.** Liquid-glass design system per
      spec (Vanilla CSS tokens, dark mode palette, micro-animations, zero
      placeholders). React 19 + TypeScript SPA in `apps/web/` covering all 6
      PS scenarios:
      1. Intake & OCR extraction preview with confidence chips & L1 confirm.
      2. Active Instrument Register & KPI problem vs solution metrics.
      3. Bank verification (L2) & AICTE bank statement CSV UTR reconciliation (L3).
      4. Maturity ladder tracker (T-90 to T-0), quiet hours, interactive reminders.
      5. WebRTC AI voice agent interactive simulator with 4-digit PIN keypad,
         3-attempt channel lockout defense, multi-lingual transcripts (en/hi/ta),
         and SHA-256 audit chaining.
      6. Security deposit release workflow with automated APH Clause 6.46
         compliance verification, 3-tier maker-checker authorization segregation,
         and cryptographic QR release certificate issuance.
      Plus Copilot APH RAG & Text-to-SQL analytics, and interactive SHA-256
      audit chain viewer with bit-flip tamper detection. Expo mobile companion
      scaffolded in `apps/mobile/` sharing `@aicte-fdr/shared` types & i18n.
      Accept met: All 8 automated test suites passing cleanly; production bundle
      built with zero errors in 3.8s.
- [x] **Phase 10 — Hardening, deploy, docs.**
      - Executed disaster recovery backup and restore drill (`scripts/backup.sh`,
        `scripts/restore.sh`) with SHA-256 integrity verification.
      - Created comprehensive production deployment guide (`docs/deployment.md`)
        covering Oracle Cloud Always Free A1 / self-hosted Linux VM setup.
      - Authored Data Protection Impact Assessment (`docs/DPIA.md`) under the
        Digital Personal Data Protection (DPDP) Act 2023.
      - Authored Operations & Incident Response runbook (`docs/runbook.md`)
        for channel lockouts, tamper detection, and sim clock management.
      - Authored comprehensive Portal User Manual (`docs/user_manual.md`)
        covering all 6 Problem Statement scenarios.
      Accept met: All 10 phases completed, tested, documented, and production ready.

## External accounts needed (not yet created — flagged when reached)

Oracle Cloud (Always Free A1 VM), GitHub, Cloudflare (Pages+Tunnel), Firebase
(FCM), Keycloak (self-hosted, no account), Sarvam AI (STT/TTS credits),
Groq/OpenRouter/Workers AI/Cerebras/Mistral (LLM free tiers), Langfuse Cloud
(Hobby), Sentry. Each will be opened in-browser when that phase starts; login
if not already authenticated.

## What's simulated (per brief, always labelled)

Bank verification (mock confirmation API, mock SFMS/NeSL) and real outbound
PSTN telephony. Everything else is a real, working integration on a free
tier or self-hosted open-source component.
