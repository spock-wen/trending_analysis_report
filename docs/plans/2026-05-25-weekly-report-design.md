# Weekly Report Design

## Overview

在现有 GitHub Trending Wiki 日报系统上，新增周报分析能力。每周自动生成一份结构化的趋势分析报告，推送飞书消息并写入飞书知识库。

## Data Sources

1. **现有每日榜数据**（SQLite `trending_daily` + `repo_stats`）——连续天数、累计天数、排名历史
2. **GitHub 官方周榜**（新增 `weekly_trending` 表）——周 star 增量、周排名

## Database

新增表 `weekly_trending`：

- repo_full_name
- week_start / week_end
- weekly_stars
- weekly_rank
- language
- description

每周日采集一次，覆盖旧数据，只保留最新一周。

## Signal Calculation (`weekly_signals.py`)

三轴信号体系：

1. **持续性轴**（来自每日 DB）
   - 连续天数、累计天数、本周首次上榜标记、排名波动

2. **爆发力轴**（来自周榜）
   - 周 star 增量、周增量排名、峰值单日增量

3. **交叉信号**（两轴合成）
   - 持久王：连续天数 ≥4 且 周增量排名前 10
   - 爆发王：周增量排名前 5 但 连续天数 ≤2
   - 二次爆发：之前掉出过榜、本周又杀回来且排名上升
   - 领域领跑：同领域项目综合排序 Top 1

输出 JSON，供 LLM 使用。

## Report Generation

LLM prompt 包含：
- 信号数据 JSON
- 本周活跃项目的 entity markdown 页面
- 上周周报（保持风格一致）
- 约束：禁止表格、分段清晰

六段结构：
1. 本周总览——总数、总 star、语言分布变化
2. 持续性趋势——霸榜项目分析
3. 本周新星——首次上榜亮点
4. 领域热度对比——赛道升温/降温
5. 交叉信号亮点——三类项目的深度解读
6. 下周关注——趋势预测

## Delivery

- **飞书消息**：send_message 推送到知识雷达
- **飞书知识库**：写入周报节点，附 entity 链接
- **触发时间**：每周日 20:00 CST

## Execution Flow

采集周榜 → 跑信号计算 → 加载 entity 内容 → LLM 写作 → 飞书消息推送 + 知识库存档
