# AI / OCR Provider Verification Register (Phase 8 / SPEC §14, §17)

**Document Status**: Official Verification Register  
**Governing Policies**: `docs/MASTER_PROMPT.md §14`, `config/LLM_PROVIDERS.yaml`, `OPEN_DECISIONS.md D-12`  
**Last Verified Date**: 2026-10-24  
**Audit Standard**: AICTE Regulation Bureau · Smart India Hackathon PS 26265  

---

## 1. Statutory Principles & Non-Negotiable AI Constraints

1. **Bounded AI Assistant Only (§14.1)**:
   - AI models never approve, reject, forfeit, renew, or release any FDR/security deposit.
   - AI models never alter evidence levels (`DECLARED`, `EXTRACTED`, `BANK_CONFIRMED`, `LEDGER_RECONCILED`).
   - AI output is strictly advisory, labeled `"AI-generated assistance — verify against the record"`, and subject to mandatory human officer review.
   - No speech/voice/calling simulation permitted in production builds per statutory user directive and mobile `M-21`.

2. **Data Tier Classification & Privacy (§14.2, D-12)**:
   - **Tier S (Sensitive Financial Data)**: Real FDR receipts, institution bank accounts, amounts, dates, IFSC codes, PAN, Aadhaar.
     - **Allowed Processors**: Local OCR engine (`tesseract` / native PDF rasteriser) and local LLM (`local_ollama` / `vLLM`) on isolated host with ZERO internet egress.
     - **External Cloud Providers**: Strictly **DISABLED** for Tier S per `OPEN_DECISIONS.md D-12`.
   - **Tier P (Public Policy & UI Strings)**: AICTE Approval Process Handbook (APH) clauses, synthetic test fixtures, public UI strings for draft translation.
     - **Allowed Processors**: Verified free-tier external providers with Presidio/regex PII redaction and citation validation.

3. **Global Kill Switch & Fail-Closed Posture**:
   - Setting `AI_GATEWAY_DISABLED=true` immediately shuts down all model invocations.
   - When external providers are down, rate-limited, or disabled, all UI features honestly report `"unavailable"`. Manual entry and human verification workflows remain 100% functional.

---

## 2. Provider Verification Matrix

| Provider | Status | Key Env Var | Verified Free Models | Free-Tier Limits | Data Retention & Training Policy | Eligible Tiers | Verification Notes & Official Citations |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Local Ollama / vLLM** | **Enabled (Local)** | None (Localhost) | `llama3.2`, `qwen2.5:7b` | Bound only by local hardware (concurrency=2) | **Zero egress**: 100% on-premises. Zero retention/training. | **Tier S, Tier P** | Primary and only approved Tier S processor per D-12. |
| **Groq** | **Verified (Active)** | `GROQ_API_KEY` | `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `openai/gpt-oss-safeguard-20b`, `meta-llama/llama-prompt-guard-2-86m`, `llama-3.3-70b-versatile` | 30 RPM, 14,400 RPD, 6,000–8,000 TPM | Logs prompts for trust & safety monitoring. Unknown training retention. | **Tier P Only** | Verified live via `/v1/models` and test completions. Fast LPU inference. |
| **Cerebras** | **Verified (Active)** | `CEREBRAS_API_KEY` | `llama-3.3-70b`, `llama-3.1-8b` | 30 RPM, 60,000 TPM, 1M tokens/day | Standard operational logging. Wafer-scale inference cluster. | **Tier P Only** | High-throughput backup for Tier P policy Q&A. |
| **Google Gemini (AI Studio)** | **Verified (Active)** | `GEMINI_API_KEY` | `gemini-2.0-flash`, `gemini-1.5-flash` | 15 RPM, 1,000,000 TPM, 1,500 RPD | **Terms Warning**: Free tier prompt data may be used by Google to improve products. | **Tier P Only** | **STRICT RULE**: Never route Tier S data to Gemini under any circumstance. Tier P policy Q&A and translation drafts only. |
| **OpenRouter** | **Verified (Active)** | `OPENROUTER_API_KEY` | `meta-llama/llama-3.3-70b-instruct:free` | ~20 RPM, 200 RPD (model dependent) | Depends on underlying routed host; free models may log. | **Tier P Only** | Fallback route for Tier P tasks using `:free` models only. |
| **Cloudflare Workers AI** | **Verified (Active)** | `CLOUDFLARE_API_TOKEN` | `@cf/meta/llama-3.3-70b-instruct` | 10,000 Neurons/day free allocation | Cloudflare network edge execution. | **Tier P Only** | Requires account ID substitution. Low daily ceiling. |
| **Mistral AI** | **Verified (Active)** | `MISTRAL_API_KEY` | `mistral-small-latest`, `open-mistral-7b` | 1 RPS (60 RPM), 500k tokens/min | Standard experimentation terms. | **Tier P Only** | Secondary fallback for multilingual text. |
| **Sarvam AI** | **Verified (Active)** | `SARVAM_API_KEY` | `sarvam-2b` | Trial credits metered | Indian sovereign infrastructure claimed. | **Tier P Only** | UI translation drafts only. Human review mandatory before publishing. |
| **NVIDIA NIM** | **Disabled** | `NVIDIA_NIM_API_KEY` | `meta/llama-3.3-70b-instruct` | 1,000 trial credits (non-renewable) | Prototyping sandbox terms. | **Disabled** | No perpetual free-tier SLA; disabled to prevent sudden failure. |
| **Hugging Face Router** | **Disabled** | `HUGGINGFACE_API_KEY` | Dynamic serverless | Zero guaranteed free capacity | Community serverless rate limits. | **Disabled** | Disabled per §14 rules (unreliable free tier). |

---

## 3. Ordered Task Routing Chains

In accordance with `config/LLM_PROVIDERS.yaml`:

1. **`policy_qa` (Tier P)**:
   - Primary: `groq` (`openai/gpt-oss-120b` or `llama-3.3-70b-versatile`)
   - 1st Failover: `cerebras` (`llama-3.3-70b`)
   - 2nd Failover: `gemini` (`gemini-2.0-flash`)
   - 3rd Failover: `openrouter` (`meta-llama/llama-3.3-70b-instruct:free`)
   - 4th Failover: `local_ollama`
   - Final: **Honest Refusal** (`"AI assistance is currently unavailable. Please refer to the Approval Process Handbook or contact the Regulation Bureau."`)

2. **`ocr_field_structuring` / `extraction` (Tier S / Tier P assist)**:
   - OCR rasterisation is 100% local (Tesseract / native rendering).
   - Candidate field extraction routes to `groq` with strict regex PII tokenisation/redaction, OR local Ollama.
   - Extracted values must pass **value-in-source validation** (any candidate value must literally appear in the OCR source text).

3. **`case_summary` (Tier S)**:
   - Route: `[local_ollama]` only.
   - If local model is not running: return `"Feature unavailable — Tier S processing requires an approved local model per D-12."`
   - Output post-check: all numbers/dates/FDR numbers must strictly match the authorized database record.
   - Label: `"AI-generated assistance — verify against the record"`.

4. **`translation_draft` (Tier P)**:
   - Route: `[sarvam, gemini, openrouter, groq, local_ollama]`
   - Post-check: ICU placeholders (e.g. `{instrument_number}`, `{amount}`) must remain intact.
   - On exhausted: Keep English source text (`on_exhausted: keep_english`).
   - Catalog status: Marked as `machine_draft`; only `reviewed` strings are shown in production UI.

---

## 4. Resilience & Circuit Breaker Thresholds

- **Consecutive Failure Threshold**: 3 failures (429 rate limit, 5xx server error, or connection timeout).
- **Circuit Open Duration**: 60 seconds.
- **Retry Backoff**: Base 400ms, max 6,000ms with full randomized jitter.
- **Token Bucket Quotas**:
  - Per-user requests: 6 requests / minute.
  - Per-institution requests: 200 requests / day.
  - Per-provider limits: Respects verified RPM/TPM headers dynamically.
- **Cache TTL**: 24 hours in Valkey/Redis keyed by normalized prompt hash.
- **Metadata-Only Audit Logging**: Every invocation recorded to `agent_runs` table with `input_hash`, `tokens_in`, `tokens_out`, `latency_ms`, `provider`, `model`, and `status`. Raw prompts for Tier S are NEVER logged.
