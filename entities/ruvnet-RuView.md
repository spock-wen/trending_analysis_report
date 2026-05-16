---
title: "ruvnet/RuView"
created: 2026-05-16
updated: 2026-05-17
type: entity
tags: [iot, tool, rust, trending]
sources: [raw/trending/2026-05-16.json]
confidence: medium
trending_count_daily: 2
trending_count_weekly: 0
trending_count_monthly: 0
consecutive_days: 2
first_trending: 2026-05-16
last_trending: 2026-05-17
peak_rank: 5
total_stars: 57787
language: Rust
license: Unknown
---

# ruvnet/RuView

## 概述

将普通 WiFi 信号转化为空间智能感知系统。利用 ESP32 传感器的 CSI（信道状态信息），实现穿墙人体检测、生命体征监测（呼吸/心率）、姿态估计和存在检测——完全无需摄像头或穿戴设备。

## 核心功能

- **WiFi 姿态估计** — CSI 子载波振幅/相位 → 17 个 COCO 关键点，M4 Pro 上 171K emb/s
- **生命体征检测** — 带通滤波提取呼吸（6-30 BPM）和心率（40-120 BPM）
- **穿墙感知** — 菲涅尔区几何 + 多径建模，支持 5m 深度穿墙检测
- **边缘智能** — 60 个 WASM 模块（5-30KB），直接在 ESP32 上运行，<10ms 延迟
- **零摄像头训练** — 10 个传感器信号，无需标签，M4 Pro 上 84 秒完成训练

^[raw/trending/2026-05-16.json]

## 技术栈

- Rust（核心）
- ESP32-S3 硬件 + WiFi CSI
- WASM 边缘模块
- 注意力机制 + 图算法 + 压缩模型

^[GitHub Trending 页面 + 项目 README]

## 使用场景

- 智能家居：无摄像头的存在检测和健康监测
- 医疗：睡眠呼吸暂停、心律失常、步态分析
- 安防：入侵检测、周界防护、恐慌动作识别
- 零售：客流热力图、排队长度、客户流分析
- 工业：叉车接近检测、密闭空间监测

## 上榜历史

| 日期 | 排名 | 当日新增 star | 总 star |
|------|------|--------------|---------|
| 2026-05-16 | 5 | +1859 | 57,787 |
| 2026-05-17 | 5 | +1,859 | 57,787 |

## 同类项目

- [[joeseesun-qiaomu-anything-to-notebooklm]] — 多源内容处理器
- [[agent-skills-ecosystem]] — Agent Skills 领域趋势分析

- [[supertone-inc-supertonic]] — 同为边缘设备 AI，专注语音而非空间感知
- [[NVIDIA-AI-Blueprints-video-search-and-summarization]] — 同为感知/监控领域，但基于视频
