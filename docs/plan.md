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

- [ ] **Phase 1 — Foundation.** Turborepo+pnpm root, uv-managed Python services,
      Docker Compose (db, valkey, minio, keycloak, api, worker, beat, caddy),
      GitHub Actions CI, pre-commit, `.env.example` handling.
      Accept: `docker compose up` works; `/health` is green.
- [ ] **Phase 2 — Data, auth, audit.** Full schema (institutions, trusts,
      instruments, banks/branches, documents, verification_records,
      discrepancies, scrutiny_observations, reminders, escalations,
      release_requests, penalties, app_users, device_tokens, consent_records,
      notification_log, call_sessions, agent_runs, audit_log, sim_clock).
      RLS per role. Keycloak OIDC + mandatory TOTP for officers.
      Accept: pytest proves cross-tenant reads blocked; audit chain verifier
      detects tampering.
- [ ] **Phase 3 — Core workflows.** Lifecycle state machine, rules engine,
      shortfall checker, release-eligibility checker w/ clause citations,
      maker-checker release approval.
      Accept: unit tests cover every transition + penalty path.
- [ ] **Phase 4 — Documents & AI extraction.** Upload→quarantine→AV/magic-byte/
      sanitize→hash/pHash→encrypted store→OCR→redact→LLM→Pydantic→rules→L1
      confirm. Forgery/duplicate signals.
      Accept: 100 synthetic FDRs, 8 layouts, ≥95% field accuracy; seeded
      defects detected with explanations.
- [ ] **Phase 5 — Verification (SIMULATED bank side).** Mock bank-confirmation
      API + mock SFMS/NeSL. Real: AICTE bank-statement CSV import w/ UTR match.
      Accept: declared-vs-confirmed diff view; evidence badges.
- [ ] **Phase 6 — LLM gateway + agents.** `llm_gateway` module, provider
      registry, discovery/health-check, routing/fallback, resilience
      (buckets, breaker, backoff, cache, repair-retry, human queue),
      redaction (Presidio+custom), Langfuse traces. LangGraph agents:
      Document Intelligence, Forgery, Verification, Maturity/Reminder,
      Escalation, Compliance RAG, Release-eligibility (interrupt), Insight
      (text2sql), Voice.
      Accept: evals for extraction/RAG/text2sql/prompt-injection in CI.
- [ ] **Phase 7 — Reminders/escalation/notifications.** Celery Beat 15-min +
      sim clock, T-90/60/30/7/0 windows, full ladder (in-app→FCM→in-app AI
      call→email→flagged PSTN/WhatsApp→Bureau).
      Accept: sim-clock +300d fires full ladder; idempotent, quiet hours,
      localized text.
- [ ] **Phase 8 — Voice agent.** Pipecat + Sarvam (Bhashini/AI4Bharat
      fallback), FCM-triggered full-screen call UI → WebRTC, disclosure→
      consent→PIN→brief→Q&A→confirm→audit. speak_amount/speak_date en/hi/ta.
      Accept: live call en/hi/ta over mobile data, interruptions work, wrong
      PIN locks channel, ack in audit log. PSTN adapter flagged.
- [ ] **Phase 9 — Web UI, then mobile UI.** Liquid-glass design system per
      spec. Accept: six PS scenarios pass as Playwright e2e.
- [ ] **Phase 10 — Hardening, deploy, docs.** ZAP, Trivy, Semgrep, gitleaks,
      axe-core, backup/restore drill, deploy scripts, full docs.
      Accept: clean deploy from docs alone; CI green.

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
