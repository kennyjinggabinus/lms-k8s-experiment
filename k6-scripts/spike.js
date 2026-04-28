// k6-scripts/spike.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m',  target: 20  },  // Warm-up at low load
    { duration: '30s', target: 150 },  // Rapid spike
    { duration: '3m',  target: 150 },  // Sustained high load
    { duration: '30s', target: 20  },  // Ramp down
    { duration: '4m',  target: 20  },  // Recovery observation
  ],
  thresholds: {
    http_req_failed: ['rate<0.20'],
  },
};

const BASE = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  const uid = Math.floor(Math.random() * 200) + 1;
  const res = http.get(`${BASE}/lms/recommendations/${uid}`, {
    tags: { scenario: 'spike' },
  });
  check(res, { 'status 200': (r) => r.status === 200 });
  sleep(1);
}

// ── HOW TO RUN ─────────────────────────────────────────────────────
// k6 run --env BASE_URL=http://localhost:8000 \
//        --out json=results/spike/docker_run1.json \
//        k6-scripts/spike.js
