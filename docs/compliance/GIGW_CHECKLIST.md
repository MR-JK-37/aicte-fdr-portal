# Guidelines for Indian Government Websites (GIGW 3.0) Compliance Checklist

> **Standard**: Guidelines for Indian Government Websites Version 3.0 (MeitY, STQC, NIC) & WCAG 2.1 Level AA.
> **Portal**: AICTE Security Deposit / FDR Management Portal (PS 26265).
> **Status**: Comprehensive Self-Audit & STQC Readiness Checklist.

---

## 1. Governance, Identity & Domain Mandates

| Requirement ID | GIGW Clause | Description | Compliance Status | Evidence / Implementation Reference |
|---|---|---|---|---|
| **GIGW-01** | §4.1 | Portal operates under approved government domain (`.gov.in`, `.nic.in`, or `aicte-india.org`) | **Compliant** | Host routing and DNS configured for official domain; staging clearly labeled with synthetic banner. |
| **GIGW-02** | §4.2 | National Emblem / AICTE Logo displayed in accordance with State Emblem of India Act | **Compliant** | Official AICTE emblem displayed on header with appropriate `alt` text in English, Hindi, and Tamil. |
| **GIGW-03** | §4.3 | Mandatory links present: About Portal, Terms & Conditions, Privacy Policy, Copyright, Hyperlinking Policy | **Compliant** | Available across web footer and `/help/compliance` navigation. |
| **GIGW-04** | §4.4 | Contact information of Nodal Officer / Grievance Redressal Officer published | **Compliant** | Displayed on Help & Support screen (`/support`) and public receipt verification footer. |
| **GIGW-05** | §4.5 | Clear distinction between official government notices and external links with disclaimer icon | **Compliant** | External links render with explicit external link icon and screen-reader announcement. |

---

## 2. Bilingual & Multilingual Content Presentation

| Requirement ID | GIGW Clause | Description | Compliance Status | Evidence / Implementation Reference |
|---|---|---|---|---|
| **GIGW-06** | §5.1 | Bilingual support for Hindi and English across all public navigation and official forms | **Compliant** | Fully implemented in `packages/i18n` with runtime language switch (en, hi, ta) in web and mobile. |
| **GIGW-07** | §5.2 | Consistent terminology across translations; no unreviewed raw machine translation in production | **Compliant** | AI translation drafts require human verification before publishing (`/v1/ai/translation-draft`). |
| **GIGW-08** | §5.3 | Proper `lang` attribute set on HTML document root and localized blocks | **Compliant** | Dynamically updated in `apps/web/index.html` (`lang="en"`, `lang="hi"`, `lang="ta"`). |

---

## 3. Universal Accessibility (WCAG 2.1 Level AA)

| Requirement ID | GIGW Clause | Description | Compliance Status | Evidence / Implementation Reference |
|---|---|---|---|---|
| **GIGW-09** | §6.1 | Text contrast ratio meets or exceeds 4.5:1 for normal text and 3:1 for large text | **Compliant** | Curated palette (`#050505`, `#3b0a6b`, `#00eeff`, `#ffffff`) tested in axe-core CI. |
| **GIGW-10** | §6.2 | Complete keyboard navigation support; visible focus indicator on all interactive elements | **Compliant** | Focus rings (`outline: 2px solid #00eeff; outline-offset: 2px`) present on all buttons and inputs. |
| **GIGW-11** | §6.3 | Screen reader compatibility with semantic HTML5 (`<header>`, `<nav>`, `<main>`, `<footer>`, `<dialog>`) | **Compliant** | Semantic structure verified in acceptance tests (`apps/web/src/App.test.tsx`). |
| **GIGW-12** | §6.4 | Non-text content has descriptive `alt` attributes; decorative images use `alt=""` | **Compliant** | Verified across all web components and mobile icon hygiene script. |
| **GIGW-13** | §6.5 | Form fields have explicit `<label>` bindings and descriptive ARIA error alerts | **Compliant** | Validated in FDR intake form and release workflow modal forms. |
| **GIGW-14** | §6.6 | Accessibility features: Dark Mode, High Contrast Mode, and Reduced Transparency | **Compliant** | Implemented in design system via CSS tokens and `@media (prefers-reduced-motion)`. |

---

## 4. Cyber Security & Privacy Compliance

| Requirement ID | GIGW Clause | Description | Compliance Status | Evidence / Implementation Reference |
|---|---|---|---|---|
| **GIGW-15** | §7.1 | STQC / CERT-In empanelled security audit compliance (Safe to Host Certificate) | **Ready** | Automated security checklist (`tests/test_security_matrix.py`) 100% green; ASVS CSV prepared. |
| **GIGW-16** | §7.2 | TLS 1.3 encryption with HTTP Strict Transport Security (HSTS) | **Compliant** | Reverse proxy Caddy configuration enforces TLS 1.3 and HSTS headers. |
| **GIGW-17** | §7.3 | Compliance with Digital Personal Data Protection (DPDP) Act 2023 | **Compliant** | Mapped in `docs/privacy/DPDP_MATRIX.md`; PII redaction and audit logging active. |
| **GIGW-18** | §7.4 | No sensitive information, bank balances, or FDR numbers logged in plaintext | **Compliant** | Cryptographic blind indexing and lock-screen sanitization enforced. |

---

## 5. Performance & Mobile Responsiveness

| Requirement ID | GIGW Clause | Description | Compliance Status | Evidence / Implementation Reference |
|---|---|---|---|---|
| **GIGW-19** | §8.1 | Responsive layout adapting across desktop (1920px), laptop (1280px), tablet (768px), and mobile (390px) | **Compliant** | Validated across full responsive breakpoints in web showcase and mobile client. |
| **GIGW-20** | §8.2 | Fast page loading and low-bandwidth optimization | **Compliant** | P95 latency under 15ms; lightweight client bundle without bloated dependencies. |
| **GIGW-21** | §8.3 | PWA offline capability and Progressive Web App installability | **Compliant** | Service worker and web manifest registered for offline compliance viewing. |
