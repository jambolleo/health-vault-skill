#!/usr/bin/env python3
"""Parse health data from natural language text into structured JSON."""

import re
import json
import sys
from datetime import datetime

# Keyword to field mapping
ALIASES = {
    '高压': 'sys_bp', '收缩压': 'sys_bp',
    '低压': 'dia_bp', '舒张压': 'dia_bp',
    '心率': 'heart_rate', '脉搏': 'heart_rate',
    '血糖': 'fbg', '空腹血糖': 'fbg',
    '尿酸': 'ua',
    '总胆固醇': 'tc', '胆固醇': 'tc',
    '甘油三酯': 'tg',
    '低密度': 'ldl', 'ldl': 'ldl', 'ldl-c': 'ldl',
    '高密度': 'hdl', 'hdl': 'hdl', 'hdl-c': 'hdl',
    '谷丙': 'alt', 'alt': 'alt',
    '谷草': 'ast', 'ast': 'ast',
    '肌酐': 'cr',
    '尿素氮': 'bun', 'bun': 'bun',
    '血红蛋白': 'hb', 'hb': 'hb',
    '白细胞': 'wbc', 'wbc': 'wbc',
    '血小板': 'plt', 'plt': 'plt',
    '糖化': 'hba1c', 'hba1c': 'hba1c', '糖化血红蛋白': 'hba1c',
    'tsh': 'tsh',
    'ggt': 'ggt', '谷氨酰': 'ggt',
    'vo2max': 'vo2max',
    '血氧': 'spo2',
}

# Reference ranges (male default)
REFERENCE = {
    'sys_bp': {'low': None, 'high': 139, 'unit': 'mmHg', 'name': '收缩压（高压）', 'ideal_high': 120},
    'dia_bp': {'low': None, 'high': 89, 'unit': 'mmHg', 'name': '舒张压（低压）', 'ideal_high': 80},
    'heart_rate': {'low': 60, 'high': 100, 'unit': 'bpm', 'name': '心率'},
    'fbg': {'low': 3.9, 'high': 6.1, 'unit': 'mmol/L', 'name': '空腹血糖'},
    'ua': {'low': 208, 'high': 428, 'unit': 'μmol/L', 'name': '尿酸'},
    'tc': {'low': None, 'high': 5.18, 'unit': 'mmol/L', 'name': '总胆固醇'},
    'tg': {'low': None, 'high': 1.7, 'unit': 'mmol/L', 'name': '甘油三酯'},
    'ldl': {'low': None, 'high': 3.37, 'unit': 'mmol/L', 'name': 'LDL-C（坏胆固醇）'},
    'hdl': {'low': 1.04, 'high': None, 'unit': 'mmol/L', 'name': 'HDL-C（好胆固醇）'},
    'alt': {'low': 9, 'high': 50, 'unit': 'U/L', 'name': 'ALT（谷丙转氨酶）'},
    'ast': {'low': 15, 'high': 40, 'unit': 'U/L', 'name': 'AST（谷草转氨酶）'},
    'ggt': {'low': 10, 'high': 60, 'unit': 'U/L', 'name': 'GGT'},
    'cr': {'low': 57, 'high': 111, 'unit': 'μmol/L', 'name': '肌酐'},
    'bun': {'low': 3.1, 'high': 8.0, 'unit': 'mmol/L', 'name': '尿素氮'},
    'hb': {'low': 130, 'high': 175, 'unit': 'g/L', 'name': '血红蛋白'},
    'wbc': {'low': 3.5, 'high': 9.5, 'unit': '×10⁹/L', 'name': '白细胞'},
    'plt': {'low': 125, 'high': 350, 'unit': '×10⁹/L', 'name': '血小板'},
    'hba1c': {'low': None, 'high': 6.0, 'unit': '%', 'name': '糖化血红蛋白'},
    'tsh': {'low': 0.27, 'high': 4.2, 'unit': 'mIU/L', 'name': 'TSH'},
    'spo2': {'low': 95, 'high': None, 'unit': '%', 'name': '血氧'},
    'vo2max': {'low': 40, 'high': None, 'unit': 'mL/min·kg', 'name': 'VO2Max'},
}

def parse_health_data(text: str) -> dict:
    """Extract health metrics from natural language text."""
    results = []
    
    # Pattern: keyword + number (support Chinese/comma/space separators)
    # Match patterns like "高压110" "高压 110" "尿酸 530" "收缩压：130"
    pattern = r'([\u4e00-\u9fa5A-Za-z\-]+)\s*[：:：]?\s*(\d+\.?\d*)'
    
    found_fields = set()
    for match in re.finditer(pattern, text):
        raw_name = match.group(1).lower().strip()
        value = float(match.group(2))
        
        # Find matching field
        field = None
        for alias, f in ALIASES.items():
            if alias in raw_name or raw_name in alias:
                field = f
                break
        
        if field and field not in found_fields and field in REFERENCE:
            found_fields.add(field)
            ref = REFERENCE[field]
            
            # Determine status
            status = '✅ 正常'
            if ref['low'] is not None and value < ref['low']:
                status = '⚠️ 偏低'
            elif ref['high'] is not None and value > ref['high']:
                status = '⚠️ 偏高'
            # Check ideal range for blood pressure
            if field == 'sys_bp' and value > 120:
                status = '⚠️ 偏高' if value >= 140 else '⚠️ 理想偏高'
            elif field == 'dia_bp' and value > 80:
                status = '⚠️ 偏高' if value >= 90 else '⚠️ 理想偏高'
            
            # Build reference range string
            if ref['low'] and ref['high']:
                ref_str = f"{ref['low']}-{ref['high']}"
            elif ref['high']:
                ref_str = f"<{ref['high']}"
            elif ref['low']:
                ref_str = f">{ref['low']}"
            else:
                ref_str = "-"
            
            results.append({
                'field': field,
                'name': ref['name'],
                'value': value,
                'unit': ref['unit'],
                'ref_low': ref['low'],
                'ref_high': ref['high'],
                'ref_str': ref_str,
                'status': status
            })
    
    return {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'parsed_count': len(results),
        'metrics': results
    }

def format_table(data: dict) -> str:
    """Format parsed data as markdown table."""
    if not data['metrics']:
        return "未识别到健康数据。请检查输入格式，如：高压120 低压80 心率70"
    
    lines = [f"## 健康数据提取结果（{data['date']}）\n"]
    lines.append("| 指标 | 结果 | 参考范围 | 状态 |")
    lines.append("|------|------|----------|------|")
    
    for m in data['metrics']:
        lines.append(f"| {m['name']} | {m['value']} {m['unit']} | {m['ref_str']} {m['unit']} | {m['status']} |")
    
    # Flag abnormal items
    abnormal = [m for m in data['metrics'] if '⚠️' in m['status'] or '🔴' in m['status']]
    if abnormal:
        lines.append(f"\n### ⚠️ 需要关注（{len(abnormal)}项）")
        for m in abnormal:
            lines.append(f"- **{m['name']}**: {m['value']} {m['unit']}（{m['status']}）")
    
    return '\n'.join(lines)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python extract.py <health data text>")
        sys.exit(1)
    
    text = sys.argv[1]
    data = parse_health_data(text)
    
    if '--json' in sys.argv:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(format_table(data))
