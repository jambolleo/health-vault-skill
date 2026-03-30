#!/usr/bin/env python3
"""Save health records to Obsidian vault."""

import json
import os
import sys
import csv
from datetime import datetime

VAULT_PATH = "/mnt/e/homeObs/homeObs"

def save_record(person: str, data_json: str, vault: str = VAULT_PATH):
    """Save health record to member file and tracking CSV."""
    data = json.loads(data_json)
    date = data['date']
    metrics = data['metrics']
    
    # 1. Create/update member checkup archive
    member_dir = os.path.join(vault, "成员模板")
    os.makedirs(member_dir, exist_ok=True)
    
    member_file = os.path.join(member_dir, f"体检档案-{person}.md")
    
    if not os.path.exists(member_file):
        # Create new member file from template
        content = f"""---
type: health-checkup-archive
person: {person}
---

# {person} 体检档案

> 自动生成于 {date}

## 体检记录

### {date}

| 项目 | 结果 | 参考范围 | 趋势 | 备注 |
|------|------|----------|------|------|
"""
        for m in metrics:
            note = "⚠️ 异常" if "⚠️" in m['status'] else ""
            content += f"| {m['name']} | {m['value']} {m['unit']} | {m['ref_str']} {m['unit']} | — | {note} |\n"
    else:
        # Read existing file, check if this date already exists
        with open(member_file, 'r', encoding='utf-8') as f:
            existing = f.read()
        
        if f"### {date}" in existing:
            return {"status": "exists", "file": member_file, "message": f"{date} 的记录已存在"}
        
        # Append new record
        content = existing.rstrip() + f"""

### {date}

| 项目 | 结果 | 参考范围 | 趋势 | 备注 |
|------|------|----------|------|------|
"""
        # For trend: read last values from previous records
        prev_values = _extract_last_values(existing)
        
        for m in metrics:
            note = "⚠️ 异常" if "⚠️" in m['status'] else ""
            trend = _calc_trend(m['field'], m['value'], prev_values)
            content += f"| {m['name']} | {m['value']} {m['unit']} | {m['ref_str']} {m['unit']} | {trend} | {note} |\n"
    
    with open(member_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 2. Append to tracking CSV
    csv_file = os.path.join(vault, "tracking", "体检指标.csv")
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)
    
    file_exists = os.path.exists(csv_file) and os.path.getsize(csv_file) > 0
    
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['日期', '项目', '结果', '参考范围', '是否异常', '状态'])
        for m in metrics:
            abnormal = "是" if "⚠️" in m['status'] else "否"
            writer.writerow([date, m['name'], f"{m['value']} {m['unit']}", f"{m['ref_str']} {m['unit']}", abnormal, m['status']])
    
    return {
        "status": "ok",
        "member_file": member_file,
        "csv_file": csv_file,
        "metrics_count": len(metrics),
        "date": date
    }

def _extract_last_values(content: str) -> dict:
    """Extract last known values from existing records."""
    values = {}
    import re
    # Match: | 指标名 | 数值 单位 | ... |
    pattern = r'\|\s*([^|]+?)\s*\|\s*([\d.]+)\s*(\S+)\s*\|'
    for match in re.finditer(pattern, content):
        name = match.group(1).strip()
        value = float(match.group(2))
        # Map name back to field
        for field, ref_info in _get_reference().items():
            if ref_info['name'] in name:
                values[field] = value
    return values

def _calc_trend(field: str, value: float, prev: dict) -> str:
    """Calculate trend arrow."""
    if field not in prev:
        return "—"
    old = prev[field]
    diff = value - old
    pct = abs(diff) / old * 100 if old != 0 else 0
    if pct < 2:
        return "→ 稳定"
    elif diff > 0:
        return "↑ 升高"
    else:
        return "↓ 降低"

def _get_reference():
    """Import reference ranges."""
    ref = {
        'sys_bp': {'name': '收缩压（高压）'},
        'dia_bp': {'name': '舒张压（低压）'},
        'heart_rate': {'name': '心率'},
        'fbg': {'name': '空腹血糖'},
        'ua': {'name': '尿酸'},
        'tc': {'name': '总胆固醇'},
        'tg': {'name': '甘油三酯'},
        'ldl': {'name': 'LDL-C（坏胆固醇）'},
        'hdl': {'name': 'HDL-C（好胆固醇）'},
        'alt': {'name': 'ALT（谷丙转氨酶）'},
        'ast': {'name': 'AST（谷草转氨酶）'},
        'cr': {'name': '肌酐'},
        'bun': {'name': '尿素氮'},
        'hb': {'name': '血红蛋白'},
        'wbc': {'name': '白细胞'},
        'plt': {'name': '血小板'},
        'hba1c': {'name': '糖化血红蛋白'},
        'tsh': {'name': 'TSH'},
    }
    return ref

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--person', required=True)
    parser.add_argument('--data', required=True, help='JSON string of parsed health data')
    parser.add_argument('--vault', default=VAULT_PATH)
    args = parser.parse_args()
    
    result = save_record(args.person, args.data, args.vault)
    print(json.dumps(result, ensure_ascii=False, indent=2))
