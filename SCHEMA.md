# GitHub Trending LLM Wiki Schema

## Domain

GitHub Trending 项目的知识库。追踪每日上榜项目，分析趋势，建立项目间的关联。

## Conventions

- 文件名：`{owner}-{repo}.md`，小写，连字符分隔
- 每个 wiki 页面以 YAML frontmatter 开头
- 使用 `[[wikilinks]]` 链接页面，每个页面至少 2 个出站链接
- 更新页面时必须 bump `updated` 日期
- 新页面必须添加到 `index.md`
- 每个操作必须追加到 `log.md`

## Frontmatter

```yaml
---
title: "owner/repo"
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query
tags: [from taxonomy below]
sources: [raw/trending/YYYY-MM-DD.json]
confidence: high | medium | low
trending_count_daily: N
trending_count_weekly: 0
trending_count_monthly: 0
consecutive_days: N
first_trending: YYYY-MM-DD
last_trending: YYYY-MM-DD
peak_rank: N
total_stars: N
language: X
license: X
---
```

## Tag Taxonomy

**领域：** ai-agent, llm, web, cli, mobile, data, devops, security, game, blockchain, iot, ar-vr, education, healthcare, finance
**语言：** rust, python, typescript, go, java, cpp, c, zig, ruby, php, swift, kotlin, dart
**类型：** framework, tool, library, app, model, dataset, benchmark, tutorial, awesome-list
**状态：** trending, rising, viral, new, returning

Rule: 每个 tag 必须在此 taxonomy 中。新 tag 先加到这里再使用。

## Page Thresholds

- 所有上榜项目都创建页面（用 confidence 区分质量）
- 上榜 1 次 → confidence: low
- 上榜 2 次 → confidence: medium
- 上榜 3+ 次 → confidence: high
- consecutive_days >= 3 → tags 加 rising
- 领域 ≥3 个项目上榜时创建 concept 页面

## Entity Pages

每个 GitHub 项目一个 entity 页面，包含：
1. 概述 — 一句话 + 核心定位
2. 核心功能 — README 提炼的主要特性（3-5 个）
3. 技术栈 — 语言、框架、关键依赖
4. 使用场景 — 适合谁用、怎么用
5. 上榜历史 — 日期 + 排名 + 当日 star
6. 同类项目 — `[[wikilinks]]` 指向同领域其他 trending 项目
7. 变化记录 — star 增长趋势、描述变化

## Concept Pages

当某领域有 3+ 个项目上榜时创建，包含：
- 领域定义和范围
- 该领域 trending 项目汇总
- 趋势分析
- 相关概念链接

## Update Policy

- 每日更新：frontmatter 上榜数据（trending_count, consecutive_days, last_trending）
- README 变化时：更新核心功能、技术栈、描述
- 新信息与已有内容矛盾时：标记日期，新信息优先

## 数据源

- raw/trending/YYYY-MM-DD.json — 每日快照（不可变）
- SQLite: /root/data/github_trending.db — 历史统计
