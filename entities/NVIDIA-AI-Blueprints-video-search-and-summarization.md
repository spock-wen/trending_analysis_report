---
title: "NVIDIA-AI-Blueprints/video-search-and-summarization"
created: 2026-05-16
updated: 2026-05-17
type: entity
tags: [ai-agent, framework, python, trending]
sources: [raw/trending/2026-05-16.json]
confidence: medium
trending_count_daily: 2
trending_count_weekly: 0
trending_count_monthly: 0
consecutive_days: 2
first_trending: 2026-05-16
last_trending: 2026-05-17
peak_rank: 9
total_stars: 1261
language: Python
license: Unknown
---

# NVIDIA-AI-Blueprints/video-search-and-summarization

## 概述

NVIDIA 视频搜索与摘要（VSS）蓝图，提供 GPU 加速视觉 Agent 和 AI 视频分析应用的参考架构。集成视觉语言模型（VLM）、大语言模型（LLM）和 NVIDIA NIM 微服务，支持实时视频智能、下游分析和 Agent 离线处理。

## 核心功能

- **实时视频智能** — 特征提取、嵌入、流理解，结果发布到消息代理
- **下游分析** — 元数据富化为轨迹、事件和验证告警
- **Agent 工作流** — 通过 MCP 编排搜索、Q&A、摘要和片段检索
- **5 大工作流** — Q&A 报告生成、告警验证、实时告警、视频搜索、长视频摘要
- **10 个 VSS 技能** — alerts、deploy、report、rt-vlm、video-analytics 等

^[raw/trending/2026-05-16.json]

## 技术栈

- Python（57.2%）+ TypeScript（35.5%）
- NVIDIA NIM 微服务（Cosmos-Reason2-8B、Nemotron-Nano-9B-v2）
- Next.js UI
- Docker Compose 部署
- MCP（Model Context Protocol）

^[GitHub Trending 页面 + 项目 README]

## 使用场景

- 智慧空间监控
- 仓库自动化
- SOP 验证
- 视频存档的自然语言搜索

## 上榜历史

| 日期 | 排名 | 当日新增 star | 总 star |
|------|------|--------------|---------|
| 2026-05-16 | 9 | +308 | 1,261 |
| 2026-05-17 | 9 | +308 | 1,261 |

## 同类项目

- [[joeseesun-qiaomu-anything-to-notebooklm]] — 多源内容处理器
- [[agent-skills-ecosystem]] — Agent Skills 领域趋势分析

- [[ruvnet-RuView]] — 同为感知/监控领域，但基于 WiFi 而非视频
- [[influxdata-telegraf]] — 同为数据采集，但专注指标而非视频分析
