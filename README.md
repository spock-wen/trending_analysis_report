# GitHub Trending LLM Wiki

> 每日自动抓取 GitHub Trending，为每个上榜项目编译深度 LLM Wiki 页面，追踪上榜历史，生成趋势分析报告。

基于 [Karpathy LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 模式构建。

## 特性

- **每日自动采集** — Python 脚本走代理抓取 GitHub Trending，写入 SQLite + raw JSON
- **深度 Wiki 编译** — LLM Agent 为每个项目生成结构化 wiki 页面（核心功能、技术栈、使用场景、交叉引用）
- **上榜历史追踪** — 统计每个项目的上榜次数、连续天数、排名变化
- **趋势分析报告** — 每日 Top 10、新面孔、连续霸榜、领域趋势
- **飞书自动推送** — 日报推送到飞书聊天
- **Lint 健康检查** — 8 项 wiki 质量检查（孤立页面、断裂链接、矛盾检测等）
- **Git 版本控制** — 所有 wiki 文件、脚本、报告统一管理

## 目录结构

```
/srv/www/github-trending-wiki/
├── SCHEMA.md                    # Wiki 维护规则、标签体系、页面模板
├── index.md                     # 内容目录索引
├── log.md                       # 操作日志（Karpathy 标准格式）
├── README.md                    # 本文件
├── .gitignore
│
├── scripts/
│   ├── github_trending_collector.py   # 采集脚本 v2
│   └── wiki_lint.py                   # Lint 健康检查脚本
│
├── data/                        # SQLite 数据库（gitignore）
│   └── github_trending.db
│
├── backups/                     # 数据库备份（gitignore）
│
├── logs/                        # 采集日志（按月轮转）
│   └── collector-2026-05.log
│
├── raw/trending/                # 每日原始 JSON 快照（不可变）
│   └── 2026-05-16.json
│
├── entities/                    # 项目 Wiki 页面
│   ├── tinyhumansai-openhuman.md
│   ├── obra-superpowers.md
│   └── ...
│
├── concepts/                    # 领域趋势概念页
│   └── agent-skills-ecosystem.md
│
├── reports/                     # 每日趋势报告 + Lint 报告
│   ├── 2026-05-16.md
│   └── lint-2026-05-16.md
│
└── comparisons/                 # 项目对比分析（按需生成）
```

## 快速开始

### 1. 采集今日数据

```bash
python3 scripts/github_trending_collector.py
```

输出：
- `raw/trending/YYYY-MM-DD.json` — 原始数据
- `data/github_trending.db` — SQLite 数据库更新

加 `--dry-run` 只解析不写入。

### 2. 运行 Lint 检查

```bash
python3 scripts/wiki_lint.py
```

检查项：
- 🔴 断裂链接（wikilinks 指向不存在的页面）
- 🟡 孤立页面、索引缺失、矛盾页面、frontmatter 验证
- 🔵 过期内容、页面大小、来源标注

### 3. 查看报告

```bash
cat reports/$(date +%Y-%m-%d).md
```

## 架构

```
┌─────────────────────────────────────────────────┐
│  Cron Job (每天 08:00)                           │
│                                                  │
│  1. Python 采集脚本 → SQLite + raw JSON          │
│  2. LLM Agent 读数据 → web_extract README        │
│  3. 编译 Wiki 页面（创建/更新 + 交叉引用）       │
│  4. 生成趋势报告                                 │
│  5. 运行 Lint 检查                               │
│  6. Git commit                                   │
│  7. 推送飞书                                     │
└─────────────────────────────────────────────────┘
         │                    │
         ▼                    ▼
   data/github_trending.db   entities/*.md
   raw/trending/*.json       reports/*.md
```

### 数据模型

**trending_daily（事实表）**
- date, period, repo_full_name, rank, description, language, stars_today, total_stars, url
- PRIMARY KEY (date, period, repo_full_name)

**repo_stats（聚合表）**
- repo_full_name (PK), trending_count_daily/weekly/monthly, consecutive_days, max_consecutive_days, peak_rank, max_stars_today
- 支持未来周报/月报扩展（period 字段）

### Wiki 页面模板

每个 entity 页面包含：
- YAML frontmatter（元数据 + 质量标签）
- 概述、核心功能、技术栈、使用场景
- 上榜历史（日期 + 排名 + star）
- 同类项目（[[wikilinks]] 交叉引用）
- 来源标注（^[raw/trending/...]）

### 代理配置

采集脚本走 sing-box 代理：`http://127.0.0.1:7890`

## Cron Job

- **Job ID:** `a793a609c78d`
- **Schedule:** 每天 08:00
- **Skill:** llm-wiki
- **Toolsets:** terminal, file, web, feishu
- **投递:** 飞书 (send_message 主动推送)

手动触发：
```bash
hermes cronjob run a793a609c78d
```

## Git 工作流

```bash
# 查看状态
git status

# 查看历史
git log --oneline

# 每次 cron 运行后自动 commit
git add -A && git commit -m "trending: YYYY-MM-DD"
```

## 标签体系

**领域：** ai-agent, llm, web, cli, mobile, data, devops, security, game, blockchain, iot, ar-vr, education, healthcare, finance
**语言：** rust, python, typescript, go, java, cpp, c, zig, ruby, php, swift, kotlin, dart, shell
**类型：** framework, tool, library, app, model, dataset, benchmark, tutorial, awesome-list
**状态：** trending, rising, viral, new, returning

## 质量标签

- `confidence: low` — 上榜 1 次
- `confidence: medium` — 上榜 2 次
- `confidence: high` — 上榜 3+ 次
- `rising` — 连续上榜 ≥3 天
- `contested: true` — 存在未解决的矛盾

## 未来扩展

- [ ] 周报/月报（脚本加 `--period weekly/monthly` 参数）
- [ ] 多语言过滤（`?spoken_language_code=zh`）
- [ ] Star 增长曲线可视化
- [ ] 和 arXiv 论文 wiki 交叉引用
- [ ] Obsidian 集成（headless sync）
- [ ] 数据库备份自动化

## 相关项目

- [Karpathy LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — 原始设计理念
- [Hermes Agent](https://github.com/NousResearch/hermes-agent) — LLM Agent 框架
- [llm-wiki skill](https://hermes-agent.nousresearch.com/docs) — Wiki 编译 skill

## License

内部使用。
