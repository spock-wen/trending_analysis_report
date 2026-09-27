# 本周 GitHub 没有大爆款，但 Attention 完成了一次换位

这周 GitHub Trending 周榜（2026-09-21 ~ 09-27），18 个项目拿下 56,645 个 Star。数字先给你，然后说反常的地方：这比上周少了四分之一，项目数也从 21 个缩到 18 个，连续两周缩量。但我看完整个榜单，反而觉得这周比前几周更有信息量——总盘子在缩，注意力的位置却完成了一次整体换位。

具体讲：上周还在涨的老项目，这周 20 个续榜算下来只有 7 个留住了，而且没有一个正增长。阿里 open-code-review 上周 +15,028★，本周掉到 +4,310★，跌了七成；WeKnora -38%，claude-code -13%。继续留在榜上的都在降，而冲高星的全是第一次上榜的新面孔——11 个新项目贡献了全榜 73% 的涨幅。前五名 hindsight（+7,282★）、orca（+6,503★）、cloudflare security-audit-skill（+6,474★）、ECC（+5,522★）、univer（+4,660★），四张新脸。

这个结构挺罕见的：老项目集体衰减，新项目包揽全部增长。说明 9 月中旬那波「人人写 skill」的热潮真的出清完了——上两周霸榜的那批社区 Skill 项目（humanizer、hyperframes、Agent-Reach、i-have-adhd 这类），这周全部掉出。

---

## hindsight：Agent 记忆接棒了

 本周期最大的单品是 vectorize-io/hindsight，一周 +7,282★，总星已过万，Python 写的。它的自我定义就一句话：Agent Memory That Learns，会学习的 Agent 记忆。

这是在补 Skill 没补上的一块。过去一个多月 Skill 热潮解决的是「让 Agent 知道怎么做」——流程、工具、规范，都是人写好放进去的，静态的。Agent 自己不积累任何经验：这次踩过的坑，下次还踩。hindsight 把「运行时学习」做成显式产品，Agent 用得越久，记忆越多，表现越好。

它的节奏也硬：9 月 25 日首次冲进日榜就是第 2 名，随后连续三天在日榜上，周日单日 +2,152★ 是本周全榜最高的一天。

把本周榜单摆在一起，一条「Agent 运行时基础设施」的链已经成型：ECC 和 agent-skills 教 Agent 做事，hindsight 让 Agent 攒经验，orca 和 paperclip 让一队 Agent 并行干活。注意力从「怎么用 Agent」移到了「怎么养 Agent」。

---

## paperclip 五周后回归，机房里那点事第二次冲榜

 这周最值得玩味的是 paperclipai/paperclip，+5,376★，断档 5 周后回归。上次上榜是 8 月 16 日，+2,430★，这次星数翻倍，而且连续两天日榜第一——周日 +2,589★ 是全榜单日最高。

卖点没变：开源的 Agent 工作管理工具，宣传语就是「在公司管理你的 agents」。变的是语境。8 月它冲榜时，「多 Agent 协作」还停留在 demo 阶段；现在我写这篇文章时，orca 已经连续两周在榜（本周 +6,503★，上周 +5,404★），xSVZ 的 Claude Cowork 这类产品把「管着一队 Agent」变成了真实的工作流。paperclip 回归的时候，正好接上一条被验证过的需求。

但有一笔账要记下来：paperclip 两次上榜都是脉冲式的，没有一次热度撑过两周。「Agent 机群管理」的需求是真的，但还没有产品把流量沉淀成用户，赛道每几个月就被重新发明一次。orca 如果下周还能续榜，它就是这条赛道第一个证明自己留得住人的标的。

---

## 大厂翻倍进场，但续榜的全在跌

上周我说只要大厂仓库有 2 个以上续榜，就说明官方进场不是一次发布会的热度。验证了，还超预期——大厂席位从 6 个翻到 8 个。但结果分两半。

维持一季度热度的一半：alibaba/open-code-review、Tencent/WeKnora、anthropics/claude-code、anthropics/knowledge-work-plugins 四个续榜，星数全在降。open-code-review 单周从 15,028★ 掉到 4,310★，这是最典型的「发布会式增长」衰减曲线——上线那种一周万星的节奏，第二周必然掉头。

补位进场的一半：新面孔 4 个。最猛的 cloudflare/security-audit-skill（+6,474★，一周 5 天在日榜上），官方出的编码 Agent 安全审计 skill，多阶段审计、每步可独立验证——安全类项目最近几周是 Trending 的稳定客源，但以前多是社区红队工具，这次是厂商下场。Anthropic 一家占 3 个席位（claude-code、knowledge-work-plugins、financial-services，后者 +2,633★，日榜 5 次连续 3 天第一），腾讯云 Octop 补了第 8 席。

这说明大厂进场的方式变了：不再是单个项目的万星爆款，而是多个仓库轮动补位。GitHub Trending 正在被当成长期阵地运营，只是单点星数撑不起头条了。

一个非 AI 的附注：缩量周席位空出来了，cloudflare/quiche（QUIC 协议的 Rust 实现，+736★）和 pytorch（+295★）自然回落补位。这个不用过度解读，是缩量周的副产品。

---

## 趋势复盘

本周 18 个项目的结构：

**Skill/Agent 工作流（9 个，35,823★）**：席位比上周（同口径 3 个）翻三倍，星数×2.4，但 82% 集中在前五——hindsight、orca、ECC、paperclip、univer 合计 29,343★。长尾出清后，头部反而更集中了。

**大厂官方（8 个，20,527★）**：席位翻倍，星数 -10.5%，续榜全负增长。进场意图更强，单点爆发力更弱。

**独立应用/其他（1 个，295★）**：只剩 pytorch 一个。上周总结里「基础设施回流」的判断被证伪了——supabase、transformers、home-assistant 全部出局，上周的回流是一次性脉冲，不是趋势。

一句话收束：从两周前 106,080★ 到本周 56,645★，总星两周累计近乎腰斩。Skill 长尾的出清基本完成，涨幅被压进了少数运行时基础设施新面孔（hindsight/orca/paperclip/univer 合计 23,821★，占全榜 42.1%）。

---

## 完整榜单

### 🆕 本周新面孔（11个）

**1. vectorize-io/hindsight**
会学习的 Agent 记忆系统。Python，+7,282★，日榜 3 次（周日全榜最高单日）

**2. cloudflare/security-audit-skill**
Cloudflare 官方编码 Agent 安全审计 skill。JavaScript，+6,474★，日榜 5 次

**3. paperclipai/paperclip**
开源 Agent 工作管理工具。TypeScript，+5,376★，断档 5 周后回归，日榜 2 次（两天第一）

**4. dream-num/univer**
Office Harness for AI Agents：表格/文档/幻灯片/画布一体化底座。TypeScript，+4,660★，日榜 5 次

**5. anthropics/financial-services**
Anthropic 官方金融服务插件包。Python，+2,633★，日榜 5 次（连续 3 天第 1）

**6. superdesigndev/treg**
Agent 工具的 OpenRouter。Python，+1,773★，日榜 2 次

**7. davila7/claude-code-templates**
Claude Code 配置与监控 CLI。Python，+1,142★，日榜 2 次

**8. HKUDS/CLI-Anything**
让所有软件 Agent 原生。Python，+1,055★，港大数据智能实验室出品，日榜 2 次

**9. TencentCloud/Octop**
腾讯云自托管 AI 助手。Python，+951★

**10. cloudflare/quiche**
QUIC 与 HTTP/3 的 Rust 实现。Rust，+736★

**11. pytorch/pytorch**
张量与动态神经网络框架。Python，+295★

### 🔥 连续上榜（7个，星数降序）

**1. stablyai/orca**
并行 Agent 机群开发环境，用自己的订阅跑任意编码 Agent。TypeScript，+6,503★（上周 +5,404★），连续 2 周

**2. affaan-m/ECC**
Agent harness 性能优化系统。JavaScript，+5,522★（上周 +6,265★），连续 2 周

**3. alibaba/open-code-review**
阿里混合架构代码评审。Go，+4,310★（上周 +15,028★，-71%），连续 2 周

**4. Tencent/WeKnora**
腾讯 LLM 知识平台。Go，+3,015★（上周 +4,867★，-38%），连续 2 周

**5. addyosmani/agent-skills**
Chrome 团队 Addy Osmani 的工程技能包。JavaScript，+2,510★（上周 +3,445★），连续 2 周

**6. anthropics/claude-code**
Claude Code 官方仓库。TypeScript，+1,744★（上周 +1,999★），连续 2 周

**7. anthropics/knowledge-work-plugins**
Anthropic 知识工作插件官方仓库。Python，+664★（上周 +1,034★），连续 2 周

注：paperclip 断档 5 周后回归，quiche、pytorch 首次进周榜，都计入新面孔。

---

## 下周看点

1. **「记忆/机群」接棒确认**：hindsight 或 paperclip 任一星数过 5,000★，那 Agent 运行时（记忆+机群）就是新主线；两个都跌破，则这周的脉冲是一次性的，赛道重新空缺。
2. **大厂席位门槛**：官方席位守住 6 个以上，说明厂商轮动运营在持稳（Anthropic 一家已占近半）；跌破 6，九月的发布会窗口正式关闭。
3. **orca 的成色**：连续第 3 周在榜且星数过 4,500★，它就是「Agent 机群」赛道第一个留得住人的项目。

---

## 参考资料

- [vectorize-io/hindsight](https://github.com/vectorize-io/hindsight)
- [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill)
- [paperclipai/paperclip](https://github.com/paperclipai/paperclip)
- [stablyai/orca](https://github.com/stablyai/orca)
- [affaan-m/ECC](https://github.com/affaan-m/ECC)
- [dream-num/univer](https://github.com/dream-num/univer)
- [alibaba/open-code-review](https://github.com/alibaba/open-code-review)
- [Tencent/WeKnora](https://github.com/Tencent/WeKnora)
- [anthropics/financial-services](https://github.com/anthropics/financial-services)
- [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills)
- [anthropics/claude-code](https://github.com/anthropics/claude-code)
- [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)
- [superdesigndev/treg](https://github.com/superdesigndev/treg)
- [davila7/claude-code-templates](https://github.com/davila7/claude-code-templates)
- [HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything)
- [TencentCloud/Octop](https://github.com/TencentCloud/Octop)
- [cloudflare/quiche](https://github.com/cloudflare/quiche)
- [pytorch/pytorch](https://github.com/pytorch/pytorch)
- 数据来源：GitHub Trending | 采集时间 2026-09-27
