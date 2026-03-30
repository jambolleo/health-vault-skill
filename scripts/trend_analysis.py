#!/usr/bin/env python3
"""Analyze health trends from tracking CSV data."""

import csv
import json
import sys
import os
from collections import defaultdict

VAULT_PATH = "/mnt/e/homeObs/homeObs"

def analyze_trends(person: str, vault: str = VAULT_PATH) -> dict:
    """Read CSV history and analyze trends."""
    csv_file = os.path.join(vault, "tracking", "体检指标.csv")
    
    if not os.path.exists(csv_file):
        return {"status": "no_data", "message": "暂无历史数据，至少需要 2 次记录"}
    
    # Parse CSV
    metrics_by_date = defaultdict(dict)
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = row['日期']
            name = row['项目']
            result_str = row['结果'].split()[0]  # Extract number
            try:
                value = float(result_str)
                metrics_by_date[date][name] = value
            except ValueError:
                continue
    
    dates = sorted(metrics_by_date.keys())
    if len(dates) < 2:
        return {"status": "insufficient", "message": f"仅 {len(dates)} 次记录，至少需要 2 次", "dates": dates}
    
    # Collect all metric names
    all_metrics = set()
    for d in metrics_by_date.values():
        all_metrics.update(d.keys())
    
    improved = []
    worsened = []
    volatile = []
    
    for name in sorted(all_metrics):
        values = [(d, metrics_by_date[d].get(name)) for d in dates if name in metrics_by_date[d]]
        if len(values) < 2:
            continue
        
        first_val = values[0][1]
        last_val = values[-1][1]
        diff = last_val - first_val
        pct = abs(diff) / first_val * 100 if first_val != 0 else 0
        
        # Check if any abnormal
        last_abnormal = False
        for d in dates:
            # Re-read CSV to check abnormality
            pass
        
        if pct < 2:
            trend = "→ 稳定"
            category = "stable"
        elif diff > 0:
            trend = f"↑ 升高 {pct:.1f}%"
            category = "up"
        else:
            trend = f"↓ 降低 {pct:.1f}%"
            category = "down"
        
        # Check volatility (max swing)
        vals = [v for _, v in values]
        swing = (max(vals) - min(vals)) / min(vals) * 100 if min(vals) != 0 else 0
        
        entry = {
            "name": name,
            "first": f"{first_val} ({values[0][0]})",
            "last": f"{last_val} ({values[-1][0]})",
            "trend": trend,
            "swing": f"{swing:.1f}%"
        }
        
        if swing > 10:
            volatile.append(entry)
        elif category == "up":
            # Need reference to know if up is bad
            worsened.append(entry)
        elif category == "down":
            improved.append(entry)
    
    return {
        "status": "ok",
        "total_records": len(dates),
        "date_range": f"{dates[0]} ~ {dates[-1]}",
        "improved": improved,
        "worsened": worsened,
        "volatile": volatile,
        "all_trends": [{"name": name, "values": [(d, metrics_by_date[d].get(name)) for d in dates if name in metrics_by_date[d]]} for name in sorted(all_metrics)]
    }

def format_trend_report(data: dict) -> str:
    """Format trend analysis as readable text."""
    if data['status'] != 'ok':
        return data.get('message', '无法分析')
    
    lines = [f"## 📊 健康趋势分析\n"]
    lines.append(f"**记录区间：** {data['date_range']}（共 {data['total_records']} 次）\n")
    
    if data['improved']:
        lines.append("### ✅ 持续改善")
        for m in data['improved']:
            lines.append(f"- {m['name']}: {m['first']} → {m['last']} ({m['trend']})")
    
    if data['worsened']:
        lines.append("### ⚠️ 需关注")
        for m in data['worsened']:
            lines.append(f"- {m['name']}: {m['first']} → {m['last']} ({m['trend']})")
    
    if data['volatile']:
        lines.append("### 📈 波动较大")
        for m in data['volatile']:
            lines.append(f"- {m['name']}: 波动幅度 {m['swing']}")
    
    if not data['improved'] and not data['worsened'] and not data['volatile']:
        lines.append("所有指标稳定，继续保持！")
    
    return '\n'.join(lines)

if __name__ == '__main__':
    if '--json' in sys.argv:
        result = analyze_trends("user")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        result = analyze_trends("user")
        print(format_trend_report(result))
