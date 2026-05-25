# Weekly Report Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** 在现有 GitHub Trending Wiki 系统上新增周报功能，每周自动生成趋势分析报告并推送到飞书消息和知识库。

**Architecture:** 新增三个组件：周榜采集器（复用日榜爬取模式）、信号计算模块（分析 DB 数据）、cron job（编排整个流程）。不修改现有日报流水线。

**Tech Stack:** Python 3, SQLite, GitHub Trending (HTML 爬取), Feishu API

---

### Task 1: 在 DB 中创建 weekly_trending 表

**Objective:** 新增一张表存储 GitHub 周榜数据，独立于每日榜。

**Files:**
- Create: `scripts/init_weekly_db.py`
- `data/github_trending.db`（修改）

**Step 1: 创建初始化脚本**

```python
#!/usr/bin/env python3
"""初始化 weekly_trending 表"""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'github_trending.db')

conn = sqlite3.connect(DB_PATH)
conn.execute('''
    CREATE TABLE IF NOT EXISTS weekly_trending (
        week_start TEXT NOT NULL,
        week_end TEXT NOT NULL,
        repo_full_name TEXT NOT NULL,
        rank INTEGER,
        weekly_stars INTEGER,
        description TEXT,
        language TEXT,
        PRIMARY KEY (week_start, repo_full_name)
    )
''')
conn.commit()
conn.close()
print("weekly_trending table ready")
```

**Step 2: 运行初始化脚本**

Run: `python3 scripts/init_weekly_db.py`
Expected: `weekly_trending table ready`

**Step 3: Commit**

```bash
cd /srv/www/github-trending-wiki
git add scripts/init_weekly_db.py
git commit -m "feat: add weekly_trending table to DB"
```

---

### Task 2: 编写周榜采集脚本

**Objective:** 每周爬一次 GitHub Trending `?since=weekly` 页面，解析项目列表写入 DB。

**Files:**
- Create: `scripts/github_weekly_collector.py`

**Step 1: 创建采集脚本**

脚本复用日榜采集器的代理配置和 HTML 解析逻辑，但：
- URL 改为 `https://github.com/trending?since=weekly`
- 写入 `weekly_trending` 表
- 覆盖同一周的数据（幂等）
- 输出采集到的项目数和 JSON 摘要

关键逻辑：
- 通过 PROXY（环境变量 `GITHUB_TRENDING_PROXY`）走代理抓取页面
- 解析 HTML 提取每个项目的 repo 名、描述、语言、本周 star 增量、排名
- 计算本周的起止日期（周一 00:00 ~ 周日 23:59）
- 写入 DB 前先 DELETE 本周已有数据再 INSERT（幂等）

**Step 2: 验证脚本可运行**

Run: `python3 scripts/github_weekly_collector.py --dry-run`
Expected: 打印解析到的项目列表，不写 DB

**Step 3: 正式运行测试**

Run: `python3 scripts/github_weekly_collector.py`
Expected: 输出本周采集的项目数

**Step 4: 验证 DB 数据**

Run:
```bash
cd /srv/www/github-trending-wiki
python3 -c "
import sqlite3
conn = sqlite3.connect('data/github_trending.db')
rows = conn.execute('SELECT repo_full_name, weekly_stars, rank FROM weekly_trending ORDER BY rank').fetchall()
print(f'共 {len(rows)} 个项目')
for r in rows[:5]:
    print(f'  #{r[2]} {r[0]} - {r[1]} stars')
"
```
Expected: 正确的周榜数据

**Step 5: Commit**

```bash
git add scripts/github_weekly_collector.py
git commit -m "feat: add weekly trending collector script"
```

---

### Task 3: 编写信号计算模块

**Objective:** 从 DB 中计算三轴信号指标，输出 JSON。

**Files:**
- Create: `scripts/weekly_signals.py`

**Step 1: 创建信号模块**

```python
#!/usr/bin/env python3
"""计算周报用的三轴信号指标"""
import json, sqlite3, os, sys
from datetime import date, timedelta

BASE = '/srv/www/github-trending-wiki'
DB_PATH = os.path.join(BASE, 'data', 'github_trending.db')

def get_week_range():
    """获取本周一和本周日的日期"""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday.isoformat(), sunday.isoformat()

def calculate_signals(week_start, week_end):
    conn = sqlite3.connect(DB_PATH)
    
    # 1. 从每日榜计算持续性信号
    daily = conn.execute('''
        SELECT repo_full_name, COUNT(*) as days, 
               MAX(stars_today) as peak_stars,
               MIN(rank) as best_rank
        FROM trending_daily 
        WHERE date >= ? AND date <= ? AND period = 'daily'
        GROUP BY repo_full_name
    ''', (week_start, week_end)).fetchall()
    
    # 2. 从周榜表读取爆发力信号
    weekly = conn.execute('''
        SELECT repo_full_name, weekly_stars, rank
        FROM weekly_trending
        WHERE week_start = ?
    ''', (week_start,)).fetchall()
    weekly_map = {r[0]: {'weekly_stars': r[1], 'rank': r[2]} for r in weekly}
    
    # 3. 查历史数据判断"本周首次上榜"
    # 如果上周不在 trending_daily 中
    prev_week_start = (date.fromisoformat(week_start) - timedelta(days=7)).isoformat()
    prev_week_end = (date.fromisoformat(week_end) - timedelta(days=7)).isoformat()
    prev_active = set(r[0] for r in conn.execute(
        'SELECT DISTINCT repo_full_name FROM trending_daily WHERE date >= ? AND date <= ?',
        (prev_week_start, prev_week_end)).fetchall())
    
    # 4. 组装信号
    projects = []
    for repo, days, peak_stars, best_rank in daily:
        w = weekly_map.get(repo, {})
        signals = {
            'repo': repo,
            'consecutive_days': days,
            'peak_daily_stars': peak_stars,
            'best_rank': best_rank,
            'weekly_stars': w.get('weekly_stars', 0),
            'weekly_rank': w.get('rank', 999),
            'is_new_this_week': repo not in prev_active,
        }
        
        # 交叉信号分类
        if signals['consecutive_days'] >= 4 and signals['weekly_rank'] and signals['weekly_rank'] <= 10:
            signals['signal_type'] = 'persistent_leader'
        elif signals['weekly_rank'] and signals['weekly_rank'] <= 5 and signals['consecutive_days'] <= 2:
            signals['signal_type'] = 'burst_star'
        elif repo in prev_active and signals['consecutive_days'] >= 2:
            signals['signal_type'] = 'comeback'
        else:
            signals['signal_type'] = 'normal'
        
        projects.append(signals)
    
    conn.close()
    return {
        'week_start': week_start,
        'week_end': week_end,
        'total_projects': len(projects),
        'total_weekly_stars': sum(p.get('weekly_stars', 0) for p in projects),
        'new_projects': sum(1 for p in projects if p['is_new_this_week']),
        'projects': sorted(projects, key=lambda p: p.get('weekly_stars', 0), reverse=True)
    }

if __name__ == '__main__':
    ws, we = get_week_range()
    signals = calculate_signals(ws, we)
    print(json.dumps(signals, ensure_ascii=False, indent=2))
```

**Step 2: 验证输出**

Run: `python3 scripts/weekly_signals.py`
Expected: 输出 JSON，包含本周各项目的信号指标

**Step 3: Commit**

```bash
git add scripts/weekly_signals.py
git commit -m "feat: add weekly signal calculation module"
```

---

### Task 4: 创建 cron job（周报生成 + 推送）

**Objective:** 设置 cron job，每周日 20:00 CST 自动生成周报并推送到飞书。

**Step 1: 编写 cron prompt**

创建 cron job，prompt 包含以下步骤：

1. 运行 `python3 scripts/github_weekly_collector.py` 采集周榜数据
2. 运行 `python3 scripts/weekly_signals.py` 获取信号 JSON
3. 读取本周活跃项目的 entity markdown 页面（从 DB 查 repo_full_name 列表后读文件）
4. 读取上周周报（从知识库或本地存档）
5. 用 LLM 生成周报（六段结构，禁止表格）
6. 推送到飞书消息（send_message）
7. 写入飞书知识库周报节点

**Step 2: 注册 cron job**

```bash
hermes cron create \
  --name "weekly-report" \
  --prompt "[上面的完整 prompt]" \
  --schedule "0 20 * * 0" \
  --deliver "local" \
  --enabled-toolsets "terminal,web,file"
```

**Step 3: 验证**

手动触发一次 cron job 测试：`hermes cron run --job-id <id>`
检查输出和飞书推送

---

### Task 5: 数据完整性检查

**Objective:** 确保周报不产生孤立数据，lint 覆盖周报相关文件。

**Files:**
- Modify: `scripts/wiki_lint.py`

**Step 1: 添加周报 lint 规则**

- weekly_trending 表数据完整性检查
- 信号输出 JSON 字段完整性检查

**Step 2: Commit**

```bash
git add scripts/wiki_lint.py
git commit -m "feat: add weekly report data lint checks"
```

---

## 执行顺序

1. Task 1: 创建 weekly_trending 表
2. Task 2: 周榜采集脚本
3. Task 3: 信号计算模块
4. Task 4: cron job 注册
5. Task 5: lint 检查（可选）

每个 task 完成后验证再提交，确保不破坏现有功能。
