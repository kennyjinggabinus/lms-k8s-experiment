# Replication Package: LMS–Kubernetes Pilot Study
## *Kubernetes-Orchestrated Reference Architecture for LMS–Recommender System Integration*

[![DOI](https://zenodo.org/badge/1223616279.svg)](https://doi.org/10.5281/zenodo.19857154)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Paper:** Jingga, K., et al. (2026). "Kubernetes-Orchestrated Reference Architecture for LMS–Recommender System Integration: Systematic Review and Design." *Proceedings of ICICEL 2026*.

---

## Overview

This repository contains the complete replication package for the **pilot study** reported in the paper above. The pilot empirically validated the scalability quality attribute scenario **ADD-SC-01** of the proposed reference architecture by comparing three deployment configurations under graduated load:

| Configuration | Description |
|---|---|
| **Docker Compose** | Single-node, no orchestration baseline |
| **Kubernetes (NoHPA)** | Single-node K8s, fixed 1-replica deployment |
| **Kubernetes (HPA)** | Single-node K8s with Horizontal Pod Autoscaler (1–5 replicas, 50% CPU target) |

Load was applied using [k6](https://k6.io/) at **10, 50, and 100 Virtual Users (VUs)** with **3 repeated runs** per condition (n = 9 runs per configuration). A failure-mode scenario was also run to measure error rates under overload conditions.

---

## Repository Structure

```
lms-k8s-experiment/
├── lms-service/            # FastAPI LMS service (Python)
│   ├── main.py             # Service implementation
│   ├── Dockerfile
│   └── requirements.txt
├── recommender-service/    # Recommender microservice
├── k8s/                    # Kubernetes manifests
│   ├── deployment-hpa.yaml     # Deployment WITH HPA (resource limits set)
│   ├── deployment-nohpa.yaml   # Deployment WITHOUT HPA (no resource limits)
│   ├── hpa.yaml                # HPA resource (autoscaling/v2, CPU 50%)
│   └── metrics-server.yaml     # Metrics Server for local K8s (e.g., minikube)
├── k6-scripts/             # k6 load test scripts
├── docker-compose.yml      # Docker Compose baseline configuration
└── analysis/
    ├── master_results.csv      # Raw per-run results (all conditions)
    ├── scalability_summary.csv # Aggregated mean ± SD, P95, P99, throughput
    ├── significance_test.txt   # Mann-Whitney U test output
    ├── parse_results.py        # Script to parse k6 JSON output
    └── compute_summary.py      # Script to compute summary statistics
```

---

## Key Results Summary

The full aggregated results are in [`analysis/scalability_summary.csv`](analysis/scalability_summary.csv).

| Load | Configuration | Mean RT (ms) | P95 RT (ms) | P99 RT (ms) | Throughput (req/s) |
|---|---|---|---|---|---|
| 10 VUs | Docker | 205.63 ± 45.98 | 728.56 | 1693.22 | 8.28 |
| 10 VUs | K8s NoHPA | 120.41 ± 3.36 | 164.25 | 252.71 | 8.93 |
| 10 VUs | K8s HPA | 148.01 ± 14.62 | 320.21 | 712.90 | 8.71 |
| 50 VUs | Docker | 680.31 ± 238.39 | 1537.63 | 3465.05 | 30.35 |
| 50 VUs | K8s NoHPA | 508.15 ± 18.89 | 759.28 | 1483.19 | 33.14 |
| 50 VUs | K8s HPA | 420.29 ± 16.14 | 700.99 | 1052.84 | 35.22 |
| 100 VUs | Docker | 1040.48 ± 130.43 | 2004.80 | 3680.79 | 49.25 |
| 100 VUs | K8s NoHPA | 718.76 ± 55.63 | 1197.30 | 2161.32 | 58.25 |
| 100 VUs | K8s HPA | 868.70 ± 100.68 | 1466.73 | 2466.71 | 53.70 |

**Statistical test:** Mann-Whitney U at 100 VUs (Docker vs K8s HPA): U = 5,936,658,366; *p* < 0.001 (significant).

**Failure-mode error rates:** Docker: ~76–79%; K8s NoHPA: ~0.3–0.6%; K8s HPA: ~1.0–2.8%.

---

## Environment

All experiments were conducted on a **single-node local cluster** (Apple M1, 8-core CPU, 16 GB RAM) using [minikube](https://minikube.sigs.k8s.io/) v1.32. This is an acknowledged **scope limitation** of the pilot — see the paper's Threats to Validity section. Multi-node and production-scale validation is designated as future work (RQ3).

**Software versions:**
- Python 3.11 / FastAPI 0.110
- Docker Desktop 4.28 / minikube 1.32 / Kubernetes 1.29
- k6 v0.49.0

---

## Reproduction Steps

### Prerequisites

```bash
# Install minikube and kubectl
brew install minikube kubectl   # macOS
# or see https://minikube.sigs.k8s.io/docs/start/

# Install k6
brew install k6   # macOS
# or see https://k6.io/docs/get-started/installation/
```

### 1. Build images

```bash
eval $(minikube docker-env)
docker build -t lms-service:v1 ./lms-service/
docker build -t recommender-service:v1 ./recommender-service/
```

### 2. Run Docker Compose baseline

```bash
docker-compose up -d
k6 run k6-scripts/load_test.js --vus 10 --duration 120s
```

### 3. Run Kubernetes (No HPA)

```bash
kubectl apply -f k8s/metrics-server.yaml
kubectl apply -f k8s/deployment-nohpa.yaml
kubectl wait --for=condition=ready pod -l app=lms --timeout=60s
k6 run k6-scripts/load_test.js --vus 10 --duration 120s
```

### 4. Run Kubernetes (HPA)

```bash
kubectl apply -f k8s/deployment-hpa.yaml
kubectl apply -f k8s/hpa.yaml
kubectl wait --for=condition=ready pod -l app=lms --timeout=60s
k6 run k6-scripts/load_test.js --vus 10 --duration 120s
```

### 5. Analyse results

```bash
pip install pandas scipy
python analysis/parse_results.py results/
python analysis/compute_summary.py
```

---

## HPA Configuration

The HPA is defined in `k8s/hpa.yaml`:
- **Target:** `recommender-deployment`
- **Min replicas:** 1 | **Max replicas:** 5
- **Trigger:** CPU utilisation ≥ 50% (averaged across pods)
- **Scale-up:** up to 4 pods per 15 s; **Scale-down:** 1 pod per 60 s with 300 s stabilisation window

> ⚠️ The 50% CPU threshold used here is specific to the single-node M1 environment and the synthetic workload. It should not be adopted as a production reference value without validation in the target deployment environment.

---

## Scope and Limitations

1. **Single-node only.** Inter-node latency, distributed scheduling, and network overlay performance are not captured.
2. **CPU-only HPA.** The multi-metric HPA scenario described in ADD-SC-01 (combining CPU + request-rate) is a design extension not yet empirically validated in this pilot.
3. **Synthetic workload.** The 200-user × 30-course interaction matrix is generated synthetically; real LMS usage patterns may differ significantly.
4. **Three repetitions per condition.** Statistical power is limited; results are indicative, not confirmatory.

---

## Citation

If you use this replication package, please cite:

```bibtex
@software{jingga2026lmsk8s,
  author    = {Jingga, Kenny},
  title     = {Replication Package: LMS–Kubernetes Pilot Study},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.19857155},
  url       = {https://doi.org/10.5281/zenodo.19857154}
}
```

---

## License

This replication package is released under the [MIT License](LICENSE).
