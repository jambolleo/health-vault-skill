---
name: health-vault
description: 家庭健康数据管理系统。当用户发送体检数据（如血压、心率、血糖、尿酸等数值）、体检报告文字、健康指标时触发。支持：健康数据提取与异常标记、写入 Obsidian 成员档案、历史趋势分析、健康建议。触发词：血压、心率、血糖、尿酸、体检、健康、肌酐、胆固醇、甘油三酯、血红蛋白、白细胞等。
---

# Health Vault

家庭健康数据管理，数据存入 Obsidian，本地私有。

## Obsidian 路径

`/mnt/e/homeObs/homeObs/`

## 工作流程

### 1. 提取健康数据

收到用户的健康数据后，调用提取脚本：

```bash
python3 /root/.openclaw/workspace/skills/health-vault/scripts/extract.py "<用户输入的数据>" --json
```

脚本返回 JSON，包含每个指标的：
- 名称、数值、单位
- 参考范围
- 状态（✅正常 / ⚠️偏高 / ⚠️偏低）

### 2. 异常分析与建议

根据提取结果，对每个异常项给出简要健康建议。参考 `references/metrics-reference.md` 中的说明。

常见异常建议模板：
- **尿酸偏高**：减少高嘌呤食物（海鲜、内脏、啤酒），多饮水（>2L/天），建议 1-3 个月复查
- **血压偏高**：低盐饮食、规律运动、控制体重，建议持续监测，持续偏高需就医
- **血糖偏高**：控制碳水摄入、增加运动，>6.1 需复查空腹血糖+糖化血红蛋白
- **ALT/AST偏高**：避免饮酒、注意休息，持续偏高建议查肝胆B超
- **肌酐偏高**：多饮水、避免肾毒性药物，建议复查肾功能
- **总胆固醇/TG偏高**：减少油腻食物、增加运动，LDL>3.37 建议就医

### 3. 保存到 Obsidian

调用保存脚本（阶段 2 实现）：

```bash
python3 /root/.openclaw/workspace/skills/health-vault/scripts/save_record.py \
    --person "<姓名>" \
    --data '<JSON数据>' \
    --vault "/mnt/e/homeObs/homeObs"
```

### 4. 趋势分析

保存后，调用趋势分析脚本：

```bash
python3 /root/.openclaw/workspace/skills/health-vault/scripts/trend_analysis.py
```

如果有 2 次以上记录，输出趋势报告（改善/恶化/波动指标）。

### 5. 回复用户

将以下内容合并后回复用户：
1. 健康数据表格（从 extract.py 输出）
2. 异常项分析和建议（agent 根据 reference 生成）
3. 趋势分析（如有历史数据）
4. 确认已保存到 Obsidian

询问用户姓名用于建档。首次使用时记录姓名，后续自动使用。

## 支持的指标

血压（高压/低压）、心率、血糖、尿酸、总胆固醇、甘油三酯、LDL、HDL、ALT、AST、肌酐、尿素氮、血红蛋白、白细胞、血小板、糖化血红蛋白、TSH、血氧、VO2Max 等。

用户可以用自然语言输入，如：
- "高压110 低压80 心率85，尿酸530"
- "收缩压128 舒张压82 心率72 空腹血糖5.6"
- "总胆固醇5.2 甘油三酯1.8 低密度3.4 高密度1.2"

## 参考值

详细参考值和健康建议见 `references/metrics-reference.md`。
