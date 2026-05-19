---
title: "obra/superpowers"
created: 2026-05-16
updated: 2026-05-20
type: framework
tags: [shell, ai-agent, framework, rising]
sources: [raw/trending/2026-05-20.json]
confidence: high
trending_count_daily: 4
trending_count_weekly: 0
trending_count_monthly: 0
consecutive_days: 4
first_trending: 2026-05-16
last_trending: 2026-05-20
peak_rank: 2
total_stars: 193299
language: Shell
---

# obra/superpowers

## 概述

面向编码 Agent 的技能框架和软件开发方法论。通过可组合的技能和结构化指令，确保 Agent 遵循纪律化的工作流程——从头脑风暴到 TDD 到代码审查。193K star，是 Agent 技能生态中 star 数最高的项目。

## 核心功能

- **结构化工作流** — 强制执行：头脑风暴 → Git Worktree → 写计划 → 执行 → TDD → 代码审查 → 完成
- **TDD 强制** — 红-绿-重构，拒绝测试前写的代码
- **子 Agent 调度** — `subagent-driven-development` 模式，分派子 Agent 执行并审查
- **跨平台兼容** — 支持 Claude Code、Codex CLI/App、Gemini CLI、Cursor、GitHub Copilot CLI
- **v5.1 性能优化** — 用轻量内联自审清单（~30秒）替代子 Agent 审查循环（~25分钟）

^[raw/trending/2026-05-16.json]

## 技术栈

- Shell（66.4%）+ JavaScript（24.8%）
- Git Worktree 隔离工作区
- 多平台插件系统

^[GitHub Trending 页面 + 项目 README]

## 使用场景

- AI 辅助软件开发的工作流规范化
- 团队中统一 Agent 编码标准
- 需要 TDD 和代码审查的质量敏感项目

## 上榜历史

| 日期 | 排名 | 当日新增 star | 总 star |
|------|------|--------------|---------|
| 2026-05-16 | 2 | +1648 | 193,299 |
| 2026-05-17 | 2 | +1,648 | 193,299 |

## 同类项目

- [[joeseesun-qiaomu-anything-to-notebooklm]] — 多源内容处理器
- [[agent-skills-ecosystem]] — Agent Skills 领域趋势分析

- [[mattpocock-skills]] — 同为 Agent 技能框架，更聚焦工程实践四大失败模式
- [[anthropics-skills]] — Anthropic 官方技能库，偏展示性质
- [[K-Dense-AI-scientific-agent-skills]] — 科研领域专用 Agent 技能
