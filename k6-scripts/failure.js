// k6-scripts/failure.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    constant_load: {
      executor: 'constant-vus',
      vus:      40,
      duration: '8m',
    },
  },
  thresholds: {
    http_req_failed: ['rate<1.0'],   // No threshold — we WANT to observe failures
  },
};

const BASE = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  const uid = Math.floor(Math.random() * 200) + 1;
  const res = http.get(`${BASE}/lms/recommendations/${uid}`, {
    tags:    { scenario: 'failure' },
    timeout: '15s',   // Allow longer timeout to capture error responses
  });
  check(res, {
    'status 200':        (r) => r.status === 200,
    'response under 2s': (r) => r.timings.duration < 2000,
  });
  sleep(1);
}

// ── FAILURE INJECTION ───────────────────────────────────────────────
// At exactly t=120s after starting k6, run the failure injection
// command in a SECOND terminal. Use the correct command for each
// deployment (see Phase 6 for exact commands).
