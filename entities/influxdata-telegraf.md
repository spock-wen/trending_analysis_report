---
title: "influxdata/telegraf"
created: 2026-05-16
updated: 2026-05-16
type: entity
tags: [devops, tool, go, trending]
sources: [raw/trending/2026-05-16.json]
confidence: low
trending_count_daily: 1
trending_count_weekly: 0
trending_count_monthly: 0
consecutive_days: 1
first_trending: 2026-05-16
last_trending: 2026-05-16
peak_rank: 6
total_stars: 17479
language: Go
license: MIT
---

# influxdata/telegraf

## 概述

InfluxData 开发的开源数据采集 Agent，用于收集、处理、聚合和写入指标、日志及其他任意数据。插件驱动架构，300+ 插件覆盖系统监控、云服务、消息队列等场景。1,395+ 贡献者，16.9K star。

## 核心功能

- **300+ 插件** — 覆盖设备（OPC UA、Modbus）、日志、消息（AMQP、Kafka、MQTT）、监控（OpenTelemetry、Prometheus）、网络、系统等
- **单一静态二进制** — 无外部依赖，编译为单个可执行文件
- **TOML 配置** — 清晰易读的配置格式
- **用户自定义代码** — 支持自定义数据采集、转换和传输逻辑
- **活跃社区** — 1,200+ 社区贡献者

## 技术栈

- Go（99.5%）
- TOML 配置
- 插件架构（输入/处理器/聚合器/输出）

## 使用场景

- 基础设施监控：CPU、内存、磁盘、网络指标采集
- 云原生可观测性：与 Prometheus、OpenTelemetry 集成
- IoT 数据采集：Modbus、OPC UA 工业协议
- 日志聚合：文件、目录监控、消息队列

## 上榜历史

| 日期 | 排名 | 当日新增 star | 总 star |
|------|------|--------------|---------|
| 2026-05-16 | 6 | +212 | 17,479 |

## 同类项目

- [[czlonkowski-n8n-mcp]] — 同为数据/工作流自动化，但专注 n8n + MCP
- [[ruvnet-RuView]] — 同为感知/监控，但基于 WiFi 信号而非传统指标
