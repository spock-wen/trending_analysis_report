---
title: "supertone-inc/supertonic"
created: 2026-05-16
updated: 2026-05-16
type: entity
tags: [ai-agent, tool, swift, trending]
sources: [raw/trending/2026-05-16.json]
confidence: low
trending_count_daily: 1
trending_count_weekly: 0
trending_count_monthly: 0
consecutive_days: 1
first_trending: 2026-05-16
last_trending: 2026-05-16
peak_rank: 4
total_stars: 6294
language: Swift
license: MIT (sample code), OpenRAIL-M (model)
---

# supertone-inc/supertonic

## 概述

闪电般快速的端侧多语言 TTS（文本转语音）系统，通过 ONNX Runtime 原生运行。完全本地推理，无云端依赖，支持 31 种语言，约 99M 参数，可在树莓派和浏览器上实时运行。

## 核心功能

- **端侧推理** — 无云端、无 API 调用，完全本地运行
- **31 语言支持** — 英语、韩语、日语、阿拉伯语、西班牙语、法语等
- **极致轻量** — ~99M 参数，CPU 上比部分 GPU 模型更快
- **自然文本处理** — 自动解析货币、电话号码、单位等复杂文本（如 "$5.2M" → "five point two million dollars"）
- **跨平台 SDK** — Python、Node.js、Browser（WebGPU/WASM）、Java、C++、C#、Go、Swift、iOS、Rust、Flutter

^[raw/trending/2026-05-16.json]

## 技术栈

- Swift（核心）
- ONNX Runtime
- SupertonicTTS 架构（语音自编码器 + flow-matching）
- Length-Aware RoPE（改进文本-语音对齐）

^[GitHub Trending 页面 + 项目 README]

## 使用场景

- 移动端/嵌入式 TTS 应用
- 电子阅读器语音朗读（如 Onyx Boox Go 6）
- Chrome 扩展：网页转音频（<1秒）
- 树莓派等低功耗设备的实时语音合成

## 上榜历史

| 日期 | 排名 | 当日新增 star | 总 star |
|------|------|--------------|---------|
| 2026-05-16 | 4 | +719 | 6,294 |

## 同类项目

- [[joeseesun-qiaomu-anything-to-notebooklm]] — 多源内容处理器
- [[agent-skills-ecosystem]] — Agent Skills 领域趋势分析

- [[ruvnet-RuView]] — 同为边缘设备 AI，但专注空间感知而非语音
- [[tinyhumansai-openhuman]] — 集成 TTS 的 AI 助手（ElevenLabs TTS）
