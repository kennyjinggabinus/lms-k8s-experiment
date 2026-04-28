// k6-scripts/scalability.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

const errors   = new Counter('custom_errors');
const rtTrend  = new Trend('custom_rt');

export const options = {
  scenarios: {
    constant_load: {
      executor:  'constant-vus',
      vus:       __ENV.VUS ? parseInt(__ENV.VUS) : 10,
      duration:  '10m',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<10000'],
    http_req_failed:   ['rate<0.20'],
  },
};

const BASE = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  const uid = Math.floor(Math.random() * 200) + 1;
  const res = http.get(`${BASE}/lms/recommendations/${uid}`, {
    tags: { scenario: 'scalability', vus: __ENV.VUS || '10' },
  });

  const ok = check(res, {
    'status 200':      (r) => r.status === 200,
    'has recommendations': (r) => {
      try {
        const body = JSON.parse(r.body);
        return Array.isArray(body.recommended_courses);
      } catch { return false; }
    },
  });

  if (!ok) errors.add(1);
  rtTrend.add(res.timings.duration);
  sleep(1);
}

// ── HOW TO RUN ─────────────────────────────────────────────────────
// Docker Compose (10 VUs):
// k6 run --env VUS=10 --env BASE_URL=http://localhost:8000 \
//        --out json=results/scalability/docker_10vu_run1.json \
//        k6-scripts/scalability.js
//
// Kubernetes (port-forward must be active first):
// k6 run --env VUS=50 --env BASE_URL=http://localhost:8000 \
//        --out json=results/scalability/k8s_nohpa_50vu_run1.json \
//        k6-scripts/scalability.js
