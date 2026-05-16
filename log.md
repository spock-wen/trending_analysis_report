# GitHub Trending Wiki Log

> 所有 wiki 操作的时序记录。只追加，不修改。
> 格式：`## [YYYY-MM-DD] action | subject`
> Actions: ingest, update, query, lint, create, archive, delete
> 超过 500 条时轮转为 log-YYYY.md

## [2026-05-16] create | Wiki 初始化
- 域名：GitHub Trending 项目追踪
- 目录结构：entities, concepts, comparisons, reports, raw/trending
- SCHEMA.md、index.md、log.md 创建完成
- SQLite 数据库：data/github_trending.db

## [2026-05-16] ingest | 首次 trending 数据 (12 个项目)
- 来源：raw/trending/2026-05-16.json
- 创建 12 个 entity 页面
- 创建 1 个 concept 页面：agent-skills-ecosystem
- 更新 index.md
- 生成 reports/2026-05-16.md

## [2026-05-16] update | 采集脚本 v2 (10 项修复)
- 修复重复运行去重、curl 解析、HTML 实体转义等
- 修复数据库 trending_count_daily 虚高
- 添加日志文件支持

## [2026-05-16] update | SCHEMA.md 补充
- 添加 provenance markers 规则
- 添加 contradiction detection 机制
- 标准化 log.md 格式
- 添加 lint/health-check 规则

## [2026-05-16] update | 目录迁移
- 从 /root/wiki/github 迁移到 /srv/www/github-trending-wiki/
- 统一管理所有系统文件
