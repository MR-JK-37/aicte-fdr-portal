import http from 'k6/http';
import { check, sleep } from 'k6';

// AICTE Security Deposit Portal — k6 Load Test Suite
// Complies with OPEN_DECISIONS.md D-13: Measure & record actual numbers; do not invent SLAs.

export const options = {
  stages: [
    { duration: '30s', target: 20 }, // Ramp-up to 20 virtual users
    { duration: '1m', target: 50 },  // Sustained load at 50 VUs
    { duration: '30s', target: 100 }, // Peak stress at 100 VUs
    { duration: '30s', target: 0 },   // Graceful ramp-down
  ],
  thresholds: {
    // Record baseline performance without failing the build arbitrarily
    http_req_duration: ['p(95)<2000'], // 95% of requests under 2s baseline
    http_req_failed: ['rate<0.05'],     // Error rate < 5%
  },
};

const BASE_URL = __ENV.API_BASE_URL || 'http://localhost:8000';

export default function () {
  // Scenario 1: System Health & Readiness Probe
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'health status is 200': (r) => r.status === 200,
  });

  const readyRes = http.get(`${BASE_URL}/readyz`);
  check(readyRes, {
    'readiness status is 200': (r) => r.status === 200,
  });

  // Scenario 2: Public Receipt Verification (F-20 / SPEC §18.1 Scenario 6)
  const testReceiptNumber = 'REC-2026-FDR-0001';
  const receiptRes = http.get(`${BASE_URL}/v1/receipts/verify/${testReceiptNumber}`);
  check(receiptRes, {
    'receipt query responds with 200 or 404': (r) => r.status === 200 || r.status === 404,
  });

  // Scenario 3: AI Policy Compliance Q&A (F-26 / SPEC §14.2)
  const policyPayload = JSON.stringify({
    question: 'What is the required security deposit for a new engineering college?',
    locale: 'en',
  });
  const policyParams = {
    headers: { 'Content-Type': 'application/json' },
  };
  const policyRes = http.post(`${BASE_URL}/v1/ai/policy-qa`, policyPayload, policyParams);
  check(policyRes, {
    'policy QA responds with 200 or honest 503 unavailable': (r) =>
      r.status === 200 || r.status === 503,
  });

  // Scenario 4: AI Gateway Status Check
  const aiStatusRes = http.get(`${BASE_URL}/v1/ai/status`);
  check(aiStatusRes, {
    'AI gateway status responds': (r) => r.status === 200,
  });

  sleep(1);
}
