---
title: "tinyhumansai/openhuman"
created: 2026-05-16
updated: 2026-05-20
type: tool
tags: [rust, rising]
sources: [raw/trending/2026-05-20.json]
confidence: high
trending_count_daily: 5
trending_count_weekly: 0
trending_count_monthly: 0
consecutive_days: 5
first_trending: 2026-05-16
last_trending: 2026-05-20
peak_rank: 1
total_stars: 17201
language: Rust
---

# tinyhumansai/openhuman

## 概述

个人 AI 超级智能助手，强调隐私、简洁和强大。开源桌面 UI 驱动的 Agent，集成 118+ 第三方服务，具备本地记忆树和 Obsidian 兼容知识库。Rank #1 今日，新增 1271 star。

## 核心功能

- **118+ 集成** — 一键 OAuth 连接 Gmail、Notion、GitHub、Slack、Stripe、Jira 等
- **自动数据拉取** — 每 20 分钟自动同步数据到本地记忆树，无需手动触发
- **Memory Tree + Obsidian Vault** — 本地 SQLite 存储，数据压缩为 ≤3k token 的 Markdown 块，生成 Obsidian 兼容知识库
- **TokenJuice 压缩** — 所有工具调用结果、抓取内容、邮件等在发送给 LLM 前压缩，降低 80% 成本和延迟
- **模型路由** — 自动将任务分配给合适的 LLM（推理、快速或视觉模型）

^[raw/trending/2026-05-16.json]

## 技术栈

- Rust + Node.js（桌面应用）
- SQLite 本地存储
- Obsidian 兼容 Markdown
- 支持 Ollama 本地模型

^[GitHub Trending 页面 + 项目 README]

## 使用场景

- 个人 AI 助手：整合邮件、日历、代码仓库、文档等全量个人数据
- 隐私优先的 AI 使用：数据本地加密存储
- 知识管理：自动构建个人知识图谱

## 上榜历史

| 日期 | 排名 | 当日新增 star | 总 star |
|------|------|--------------|---------|
| 2026-05-16 | 1 | +1271 | 9,679 |
| 2026-05-17 | 1 | +1,271 | 9,679 |

## 同类项目

- [[joeseesun-qiaomu-anything-to-notebooklm]] — 多源内容处理器
- [[agent-skills-ecosystem]] — Agent Skills 领域趋势分析

- [[oven-sh-bun]] — 同为 Rust 构建的高性能工具，但专注 JS 运行时
- [[obra-superpowers]] — 同为 AI Agent 框架，但专注开发工作流
