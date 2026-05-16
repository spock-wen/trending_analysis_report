# GitHub Trending LLM Wiki Schema

## Domain

GitHub Trending 项目的知识库。追踪每日上榜项目，分析趋势，建立项目间的关联。

## Conventions

- 文件名：`{owner}-{repo}.md`，小写，连字符分隔
- 每个 wiki 页面以 YAML frontmatter 开头
- 使用 `[[wikilinks]]` 链接页面，每个页面至少 2 个出站链接
- 更新页面时必须 bump `updated` 日期
- 新页面必须添加到 `index.md`
- 每个操作必须追加到 `log.md`（格式：`## [YYYY-MM-DD] action | subject`）

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
contested: true                    # 当页面有未解决的矛盾时设置
contradictions: [other-page-slug]  # 与哪些页面存在矛盾
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
**语言：** rust, python, typescript, go, java, cpp, c, zig, ruby, php, swift, kotlin, dart, shell
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

## Provenance Markers（来源标注）

在综合 3+ 个来源的页面中，段落末尾标注来源：
```
项目核心功能包括 X、Y、Z。^[raw/trending/2026-05-16.json]
```

- 单来源页面：`sources:` frontmatter 已足够，不需要额外标注
- 多来源页面：标注每个段落的来源文件
- 来源文件变化时：重新 ingest，更新标注

## Contradiction Detection（矛盾检测）

当新信息与已有内容矛盾时：
1. 检查日期 — 新来源优先
2. 如果矛盾真实存在（如项目描述重大变更），两个版本都保留，标注日期
3. 在 frontmatter 设置 `contested: true` 和 `contradictions: [相关页面]`
4. 在页面中添加矛盾说明段落

**触发条件：**
- 项目描述从 "X" 变为 "Y"（核心定位变化）
- 语言从 "A" 变为 "B"（技术栈迁移）
- license 变化

## Update Policy

- 每日更新：frontmatter 上榜数据（trending_count, consecutive_days, last_trending）
- README 变化时：更新核心功能、技术栈、描述
- 新信息与已有内容矛盾时：按 Contradiction Detection 处理

## Log Format

`log.md` 遵循 Karpathy 标准格式：
```markdown
## [YYYY-MM-DD] action | subject
- 详情1
- 详情2
```

Actions: `ingest`, `update`, `query`, `lint`, `create`, `archive`, `delete`

## Lint / Health Check

定期运行 lint 检查以下项目：
1. **孤立页面** — 没有任何其他页面通过 [[wikilinks]] 引用的页面
2. **断裂链接** — `[[wikilinks]]` 指向不存在的页面
3. **索引完整性** — 每个 wiki 页面都应出现在 index.md 中
4. **Frontmatter 验证** — 必填字段完整，tags 在 taxonomy 中
5. **过期内容** — `updated` 日期超过 30 天未更新的页面
6. **矛盾页面** — `contested: true` 的页面需要人工审查
7. **页面大小** — 超过 200 行的页面应拆分
8. **来源漂移** — raw/ 中的文件 sha256 变化

Lint 报告写入 `reports/lint-YYYY-MM-DD.md`。

## 数据源

- raw/trending/YYYY-MM-DD.json — 每日快照（不可变）
- SQLite: data/github_trending.db — 历史统计
