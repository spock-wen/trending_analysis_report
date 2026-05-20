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

## [2026-05-17] update | 第 2 日 trending 数据（12 个项目连续上榜）
- 来源：raw/trending/2026-05-17.json
- 12/12 项目全部连续第 2 天上榜，无新上榜项目
- 更新 12 个 entity 页面（consecutive_days=2, confidence→medium）
- 更新 concept: agent-skills-ecosystem（追加第 2 天数据）
- 生成 reports/2026-05-17.md
- 当日 star 增长 Top 3: mattpocock/skills +3132, ruvnet/RuView +1859, obra/superpowers +1648

## [2026-05-18] update | GitHub Trending 日报
- 采集 17 个项目（raw/trending/2026-05-18.json）
- 新建 entity: 8 个
- 更新 entity: 9 个
- 趋势: Python 5 个, TypeScript 4 个
- AI Agent 生态集中上榜

## [2026-05-19] update | GitHub Trending 日报
- 采集 13 个项目（raw/trending/2026-05-19.json）
- 新建 entity: 4 个（Imbad0202/academic-research-skills, CloakHQ/CloakBrowser, humanlayer/12-factor-agents, NVlabs/Sana）
- 更新 entity: 9 个
- 趋势: Python 6 个, Rust 2 个, TypeScript 2 个, Swift 1 个, Elixir 1 个, Jupyter Notebook 1 个
- 连续 4 天上榜: tinyhumansai/openhuman, K-Dense-AI/scientific-agent-skills, supertone-inc/supertonic, ruvnet/RuView（confidence → high）
- 连续 2 天上榜: HKUDS/CLI-Anything, tech-leads-club/agent-skills, BigBodyCobain/Shadowbroker, microsoft/ai-agents-for-beginners, plausible/analytics
- 当日 star 增长 Top 3: tinyhumansai/openhuman +3941, CloakHQ/CloakBrowser +1420, Imbad0202/academic-research-skills +1439

## [2026-05-20] update | GitHub Trending 日报
- 采集 18 个项目（raw/trending/2026-05-20.json）
- 新建 entity: 12 个（anthropics/claude-plugins-official, rohitg00/agentmemory, rtk-ai/rtk, msitarzewski/agency-agents, multica-ai/andrej-karpathy-skills, Diolinux/PhotoGIMP, Alishahryar1/free-claude-code, pascalorg/editor, frappe/erpnext, HKUDS/ViMax, Imbad0202/academic-research-skills, CloakHQ/CloakBrowser）
- 更新 entity: 6 个
- 趋势: Python 7 个, Rust 2 个, TypeScript 3 个, Shell 1 个, CSS 1 个, Jupyter Notebook 1 个
- 连续 5 天上榜: tinyhumansai/openhuman（confidence → high）
- 连续 3 天上榜: HKUDS/CLI-Anything, obra/superpowers, microsoft/ai-agents-for-beginners（confidence → high）
- 连续 2 天上榜: humanlayer/12-factor-agents
- 当日 star 增长 Top 3: tinyhumansai/openhuman +3991, Imbad0202/academic-research-skills +3184, multica-ai/andrej-karpathy-skills +1935

## [2026-05-20] update | GitHub Trending 日报
- 采集 18 个项目（raw/trending/2026-05-20.json）
- 新建 entity: 0 个（）
- 更新 entity: 18 个
- 趋势: Python 7个, TypeScript 4个, Rust 2个, Shell 2个, 其他 1个
- 连续 6 天上榜: "tinyhumansai/openhuman"
- 连续 4 天上榜: "K-Dense-AI/scientific-agent-skills"
- 连续 4 天上榜: "HKUDS/CLI-Anything"
- 连续 4 天上榜: "microsoft/ai-agents-for-beginners"
- 连续 4 天上榜: "obra/superpowers"
- 连续 4 天上榜: "ruvnet/RuView"
- 连续 4 天上榜: "supertone-inc/supertonic"
- 连续 3 天上榜: "humanlayer/12-factor-agents"
- 连续 2 天上榜: "NVIDIA-AI-Blueprints/video-search-and-summarization"
- 连续 2 天上榜: "Alishahryar1/free-claude-code"
- 连续 2 天上榜: "anthropics/claude-plugins-official"
- 连续 2 天上榜: "anthropics/skills"
- 连续 2 天上榜: "BigBodyCobain/Shadowbroker"
- 连续 2 天上榜: "CloakHQ/CloakBrowser"
- 连续 2 天上榜: "colbymchenry/codegraph"
- 连续 2 天上榜: "czlonkowski/n8n-mcp"
- 连续 2 天上榜: "Diolinux/PhotoGIMP"
- 连续 2 天上榜: "frappe/erpnext"
- 连续 2 天上榜: "HKUDS/ViMax"
- 连续 2 天上榜: "Imbad0202/academic-research-skills"
- 连续 2 天上榜: "influxdata/telegraf"
- 连续 2 天上榜: "joeseesun/qiaomu-anything-to-notebooklm"
- 连续 2 天上榜: "mattpocock/skills"
- 连续 2 天上榜: "msitarzewski/agency-agents"
- 连续 2 天上榜: "multica-ai/andrej-karpathy-skills"
- 连续 2 天上榜: "oven-sh/bun"
- 连续 2 天上榜: "pascalorg/editor"
- 连续 2 天上榜: "plausible/analytics"
- 连续 2 天上榜: "rohitg00/agentmemory"
- 连续 2 天上榜: "rtk-ai/rtk"
- 连续 2 天上榜: "tech-leads-club/agent-skills"
- 当日 star 增长 Top 3: tinyhumansai/openhuman +3991⭐, Imbad0202/academic-research-skills +3184⭐, multica-ai/andrej-karpathy-skills +1935⭐

## [2026-05-20] update | GitHub Trending 日报
- 采集 18 个项目（raw/trending/2026-05-20.json）
- 新建 entity: 10 个（anthropics/claude-plugins-official, rohitg00/agentmemory, rtk-ai/rtk, msitarzewski/agency-agents, multica-ai/andrej-karpathy-skills...）
- 趋势: Python 7个, TypeScript 4个, Shell 2个, Rust 2个, CSS 1个
- 连续 3 天上榜: tinyhumansai/openhuman
- 连续 3 天上榜: HKUDS/CLI-Anything
- 连续 3 天上榜: microsoft/ai-agents-for-beginners
- 连续 2 天上榜: K-Dense-AI/scientific-agent-skills
- 连续 2 天上榜: BigBodyCobain/Shadowbroker
- 连续 2 天上榜: tech-leads-club/agent-skills
- 连续 2 天上榜: plausible/analytics
- 连续 2 天上榜: Imbad0202/academic-research-skills
- 连续 2 天上榜: CloakHQ/CloakBrowser
- 连续 2 天上榜: humanlayer/12-factor-agents
- 当日 star 增长 Top 3: tinyhumansai/openhuman +3991⭐, Imbad0202/academic-research-skills +3184⭐, multica-ai/andrej-karpathy-skills +1935⭐

## [2026-05-20] update | GitHub Trending 日报
- 采集 18 个项目（raw/trending/2026-05-20.json）
- 新建 entity: 10 个（anthropics/claude-plugins-official, rohitg00/agentmemory, rtk-ai/rtk, msitarzewski/agency-agents, multica-ai/andrej-karpathy-skills...）
- 趋势: Python 7个, TypeScript 4个, Shell 2个, Rust 2个, CSS 1个
- 连续 3 天上榜: tinyhumansai/openhuman
- 连续 3 天上榜: HKUDS/CLI-Anything
- 连续 3 天上榜: microsoft/ai-agents-for-beginners
- 连续 2 天上榜: K-Dense-AI/scientific-agent-skills
- 连续 2 天上榜: BigBodyCobain/Shadowbroker
- 连续 2 天上榜: tech-leads-club/agent-skills
- 连续 2 天上榜: plausible/analytics
- 连续 2 天上榜: Imbad0202/academic-research-skills
- 连续 2 天上榜: CloakHQ/CloakBrowser
- 连续 2 天上榜: humanlayer/12-factor-agents
- 当日 star 增长 Top 3: tinyhumansai/openhuman +3991⭐, Imbad0202/academic-research-skills +3184⭐, multica-ai/andrej-karpathy-skills +1935⭐

## [2026-05-20] update | GitHub Trending 日报
- 采集 18 个项目（raw/trending/2026-05-20.json）
- 新建 entity: 10 个（anthropics/claude-plugins-official, rohitg00/agentmemory, rtk-ai/rtk, msitarzewski/agency-agents, multica-ai/andrej-karpathy-skills...）
- 趋势: Python 7个, TypeScript 4个, Shell 2个, Rust 2个, CSS 1个
- 连续 3 天上榜: tinyhumansai/openhuman
- 连续 3 天上榜: HKUDS/CLI-Anything
- 连续 3 天上榜: microsoft/ai-agents-for-beginners
- 连续 2 天上榜: K-Dense-AI/scientific-agent-skills
- 连续 2 天上榜: BigBodyCobain/Shadowbroker
- 连续 2 天上榜: tech-leads-club/agent-skills
- 连续 2 天上榜: plausible/analytics
- 连续 2 天上榜: Imbad0202/academic-research-skills
- 连续 2 天上榜: CloakHQ/CloakBrowser
- 连续 2 天上榜: humanlayer/12-factor-agents
- 当日 star 增长 Top 3: tinyhumansai/openhuman +3973⭐, Imbad0202/academic-research-skills +3164⭐, multica-ai/andrej-karpathy-skills +1955⭐

## [2026-05-20] update | GitHub Trending 日报
- 采集 18 个项目（raw/trending/2026-05-20.json）
- 新建 entity: 10 个（anthropics/claude-plugins-official, rohitg00/agentmemory, rtk-ai/rtk, msitarzewski/agency-agents, multica-ai/andrej-karpathy-skills...）
- 趋势: Python 7个, TypeScript 4个, Shell 2个, Rust 2个, CSS 1个
- 连续 3 天上榜: tinyhumansai/openhuman
- 连续 3 天上榜: HKUDS/CLI-Anything
- 连续 3 天上榜: microsoft/ai-agents-for-beginners
- 连续 2 天上榜: K-Dense-AI/scientific-agent-skills
- 连续 2 天上榜: BigBodyCobain/Shadowbroker
- 连续 2 天上榜: tech-leads-club/agent-skills
- 连续 2 天上榜: plausible/analytics
- 连续 2 天上榜: Imbad0202/academic-research-skills
- 连续 2 天上榜: CloakHQ/CloakBrowser
- 连续 2 天上榜: humanlayer/12-factor-agents
- 当日 star 增长 Top 3: tinyhumansai/openhuman +3973⭐, Imbad0202/academic-research-skills +3164⭐, multica-ai/andrej-karpathy-skills +1955⭐

## [2026-05-20] update | GitHub Trending 日报
- 采集 18 个项目（raw/trending/2026-05-20.json）
- 新建 entity: 10 个（anthropics/claude-plugins-official, rohitg00/agentmemory, rtk-ai/rtk, msitarzewski/agency-agents, multica-ai/andrej-karpathy-skills...）
- 趋势: Python 7个, TypeScript 4个, Shell 2个, Rust 2个, CSS 1个
- 连续 3 天上榜: tinyhumansai/openhuman
- 连续 3 天上榜: HKUDS/CLI-Anything
- 连续 3 天上榜: microsoft/ai-agents-for-beginners
- 连续 2 天上榜: K-Dense-AI/scientific-agent-skills
- 连续 2 天上榜: BigBodyCobain/Shadowbroker
- 连续 2 天上榜: tech-leads-club/agent-skills
- 连续 2 天上榜: plausible/analytics
- 连续 2 天上榜: Imbad0202/academic-research-skills
- 连续 2 天上榜: CloakHQ/CloakBrowser
- 连续 2 天上榜: humanlayer/12-factor-agents
- 当日 star 增长 Top 3: tinyhumansai/openhuman +3973⭐, Imbad0202/academic-research-skills +3164⭐, multica-ai/andrej-karpathy-skills +1955⭐

## [2026-05-21] update | GitHub Trending 日报
- 采集 15 个项目（raw/trending/2026-05-21.json）
- 新建 entity: 5 个（rohitg00/ai-engineering-from-scratch, can1357/oh-my-pi, rmyndharis/OpenWA, truelockmc/streambert, opentoonz/opentoonz）
- 趋势: Python 5个, TypeScript 4个, Shell 2个, 其他 1个, C++ 1个
- 连续 4 天上榜: tinyhumansai/openhuman
- 连续 4 天上榜: HKUDS/CLI-Anything
- 连续 3 天上榜: microsoft/ai-agents-for-beginners
- 连续 3 天上榜: Imbad0202/academic-research-skills
- 连续 2 天上榜: obra/superpowers
- 连续 2 天上榜: K-Dense-AI/scientific-agent-skills
- 连续 2 天上榜: BigBodyCobain/Shadowbroker
- 连续 2 天上榜: tech-leads-club/agent-skills
- 连续 2 天上榜: plausible/analytics
- 连续 2 天上榜: colbymchenry/codegraph
- 连续 2 天上榜: CloakHQ/CloakBrowser
- 连续 2 天上榜: humanlayer/12-factor-agents
- 连续 2 天上榜: anthropics/claude-plugins-official
- 连续 2 天上榜: rohitg00/agentmemory
- 连续 2 天上榜: msitarzewski/agency-agents
- 连续 2 天上榜: multica-ai/andrej-karpathy-skills
- 连续 2 天上榜: HKUDS/ViMax
- 当日 star 增长 Top 3: tinyhumansai/openhuman +3603⭐, multica-ai/andrej-karpathy-skills +2620⭐, colbymchenry/codegraph +1910⭐
