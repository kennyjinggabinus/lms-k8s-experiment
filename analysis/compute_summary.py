# analysis/compute_summary.py
import pandas as pd
import numpy as np
from scipy.stats import mannwhitneyu
import json, glob

def load_durations(pattern):
    """Load all raw duration values matching a glob pattern."""
    durations = []
    for f in glob.glob(pattern):
        with open(f) as fh:
            for line in fh:
                try:
                    obj = json.loads(line.strip())
                    if obj.get('type')=='Point' and obj.get('metric')=='http_req_duration':
                        durations.append(obj['data']['value'])
                except: pass
    return np.array(durations)

# ── Scalability Summary ───────────────────────────────────────────────
deployments = {
    'Docker':    'docker',
    'K8s NoHPA': 'k8s_nohpa',
    'K8s HPA':   'k8s_hpa',
}
vus_levels = [10, 50, 100]

print('\n=== SCALABILITY RESULTS (mean ± std across 3 runs) ===')
print(f'{"Load":<8} {"Deployment":<12} {"MeanRT(ms)":<20} {"P95RT":<10} {"P99RT":<10} {"Throughput":<12} {"ErrRate%"}')

summary_rows = []
for vus in vus_levels:
    for dep_label, dep_key in deployments.items():
        run_means, run_p95, run_p99, run_tp, run_err = [], [], [], [], []
        for run in [1, 2, 3]:
            d = load_durations(f'results/scalability/{dep_key}_{vus}vu_run{run}.json')
            if len(d) == 0: continue
            run_means.append(d.mean())
            run_p95.append(np.percentile(d, 95))
            run_p99.append(np.percentile(d, 99))
            run_tp.append(len(d) / 600)
            # error rate needs status parsing — simplified here

        if not run_means: continue
        mean_str = f'{np.mean(run_means):.2f} ± {np.std(run_means):.2f}'
        row = {
            'Load': f'{vus} VUs', 'Deployment': dep_label,
            'MeanRT': mean_str,
            'P95RT':  f'{np.mean(run_p95):.2f}',
            'P99RT':  f'{np.mean(run_p99):.2f}',
            'Throughput': f'{np.mean(run_tp):.2f}',
        }
        summary_rows.append(row)
        print(f'{str(vus)+" VUs":<8} {dep_label:<12} {mean_str:<20} {row["P95RT"]:<10} {row["P99RT"]:<10} {row["Throughput"]}')

pd.DataFrame(summary_rows).to_csv('analysis/scalability_summary.csv', index=False)

# ── Statistical Significance Test (100 VU: Docker vs K8s HPA) ────────
print('\n=== SIGNIFICANCE TEST: 100 VU Docker vs K8s HPA ===')
docker_d = load_durations('results/scalability/docker_100vu_run*.json')
k8s_d    = load_durations('results/scalability/k8s_hpa_100vu_run*.json')

if len(docker_d) > 0 and len(k8s_d) > 0:
    stat, p = mannwhitneyu(docker_d, k8s_d, alternative='two-sided')
    sig = 'SIGNIFICANT' if p < 0.05 else 'NOT significant'
    print(f'Mann-Whitney U = {stat:.0f},  p = {p:.6f}  → {sig} (alpha=0.05)')
    with open('analysis/significance_test.txt', 'w') as f:
        f.write(f'Mann-Whitney U test: Docker vs K8s HPA at 100 VUs\n')
        f.write(f'U = {stat:.0f}, p = {p:.6f}, significant = {p < 0.05}\n')

print('\nAnalysis complete. Check analysis/ folder for CSV outputs.')