# analysis/parse_results.py
import json, glob, os
import pandas as pd
import numpy as np

def parse_k6_file(filepath):
    durations, statuses, timestamps = [], [], []
    with open(filepath) as f:
        for line in f:
            try:
                obj = json.loads(line.strip())
            except json.JSONDecodeError:
                continue
            if obj.get('type') != 'Point':
                continue
            metric = obj.get('metric', '')
            if metric == 'http_req_duration':
                durations.append(obj['data']['value'])
                statuses.append(obj['data'].get('tags', {}).get('status', '0'))
                timestamps.append(obj['data']['time'])
    return pd.DataFrame({'duration_ms': durations, 'status': statuses, 'time': timestamps})

def compute_stats(df):
    d    = df['duration_ms']
    succ = df[df['status'] == '200']['duration_ms']
    n    = len(d)
    return {
        'n_requests':  n,
        'mean_rt':     round(d.mean(), 2),
        'std_rt':      round(d.std(), 2),
        'p95_rt':      round(np.percentile(d, 95), 2),
        'p99_rt':      round(np.percentile(d, 99), 2),
        'throughput':  round(n / 600, 2),  # 10-min test = 600s
        'error_rate':  round((1 - len(succ)/n) * 100, 3) if n > 0 else 0,
    }

# ── Parse all files ──────────────────────────────────────────────────
all_files = glob.glob('results/**/*.json', recursive=True)
print(f'Found {len(all_files)} result files')

rows = []
for f in sorted(all_files):
    name  = os.path.basename(f).replace('.json', '')
    parts = name.split('_')
    # Parse filename: deployment_[vus_]run[N]
    df    = parse_k6_file(f)
    stats = compute_stats(df)
    stats['file'] = name
    rows.append(stats)
    print(f'  {name}: {stats["n_requests"]} requests, mean={stats["mean_rt"]}ms')

master = pd.DataFrame(rows)
master.to_csv('analysis/master_results.csv', index=False)
print(f'\nSaved analysis/master_results.csv ({len(master)} rows)')