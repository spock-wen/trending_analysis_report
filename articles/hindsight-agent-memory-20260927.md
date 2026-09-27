# Agent 开始记事了

> 2026-09-21 ~ 2026-09-27 | GitHub 本周周榜第 1 | +7,282★

这周的 GitHub Trending 有点意思。榜首不是什么新框架，也不是哪家大厂的发布会单品——是一套「记忆系统」。vectorize-io 的 [hindsight](https://github.com/vectorize-io/hindsight) 一周拿下 7,282 星登顶周榜，9 月 25 日首次冲进日榜就是第二名，周日单日 +2,152★ 是全榜单日最高，连着三天在榜上没下来。

它做的工作听上去没有「万星爆款」的爆炸感：让 AI Agent 能记住事。翻开它的自我介绍，一句话——**Agent Memory That Learns**，会学习的 Agent 记忆。

![](images/hindsight-20260927-digest.png)

## 为什么这个点火了？得先刷一遍背景

过去一年多，我们的注意力顺着一个链条往上爬：先是「怎么让 Agent 学会做事」（Skill 模板热潮），那批社区 skill 项目如今已经凉了大半——这周长尾 skill 出清完毕；接着是「怎么让一队 Agent 并行干活」（orca 这样的机群调度）；现在轮到这块最底层的砖了——**Agent 干完活，拿什么把经验攒下来？**

三种东西，三层台阶，缺一不可。hindsight 真正冲上热榜是在 Skill 热潮潮水退去之后——这也解释了为什么它不是在三个月前上架 GitHub 就红了：**社区早两个月还没准备好听「Agent 该记事」这种话**。

## 它是怎么记的？光是这点就看得我很想安利给你

hindsight 背后有一篇论文（Vectorize × 华盛顿邮报 × 弗吉尼亚理工），arXiv:2512.12818，去年 12 月就提交了，这次开源引爆。论文最有意思的是它给记忆分了四种「抽屉」：

- **world（世界）**：外部世界的客观事实——你跟我说了什么、谁做了什么
- **experience（经历）**：Agent 自己的第一人称经历——我干成了什么、我踩过什么坑
- **opinion（看法）**：Agent 主观的判断，带着 0 到 1 的置信度
- **observation（观察）**：跨很多条事实合成的实体摘要

碰见这种思路，我先看它最「不像系统要求」的部分。**opinion 网络是真正的护城河**——记忆带置信度，可以被削弱。给一条新证据它就加 0.05（强化），反证来了减一点，矛盾直接减两倍个 α。这篇论文强调过：MemGPT、Zep、Mem0 那些前代系统，**全都不分事实和观点，把模型说的话和它的判断搅在一张桌子上**。我记得读完这块当时的反应是——原来问题不在于没有记忆模块，而在于压根没给「看法是什么」留位置。

它对记忆的读写也分三步：**retain**（记下）→ **recall**（想起）→ **reflect**（反思）。记下时把对话流提炼成叙事事实建图；想起时四路并行检索（向量 + 关键词 + 图 + 时间），再用重排器统一排序；反思时用「性格参数」决定生成的方式和态度——Agent 还能带着自己的判断色去回答，而不是每次冷启动都摆一张空桌子。

每个记忆节点带着三枚时间戳（发生开始、发生结束、提及时间），检索时「上周他刚经历过的」这种口语时间表达会被直接解析成区间。不像传统 RAG 那样把所有历史一起堆过去，需要就是需要、精准就是精准。

## 那个最关键的实验：同一个 20B 模型，39% → 83.6%

纸面上的架构听起来很齐整，真正的杀手数字在这——同一款开源 20B 模型（GPT-OSS-20B），LongMemEval（105k~1.5M 多会话记忆评测）：

- 硬塞全上下文（无记忆）：**39.0%**
- 加上 hindsight 记忆架构：**83.6%**（+44.6 个点）
- 同一套记忆层，换到更大模型上行：OSS-120B 到 89.0，Gemini-3 负责生成到 **91.4%**，超过了 Supermemory+GPT-5（84.6）和 Zep+GPT-4o（71.2）

（图：LongMemEval-S 对比条形图）

这个对比的漂亮之处在于控制变量：全上下文基线和 hindsight 版用的是同一款 20B 模型，差异不在模型也不在数据，**只差在要不要给 Agent 一张记忆的桌子**。反过来看更有意思：塞满完整对话上下文的 GPT-4o（60.2%）也输了——这说明瓶颈从来不是「塞了多少」，是**塞进去之后还能想起来多少**。

这也是我对「RAG 已死」这类口号的保留看法：Vectorize 的 CEO Chris Latimer 在接受 VentureBeat 采访时说「RAG is on life support, agent memory is about to kill it entirely」。口号很冲，但论文里真正站得住的结论没那么戏剧——结构在补偿上下文的稀释，不能升级成对整个 RAG 产业的讣告。

## 不全是好消息：两处要在光下看清楚

第一，**LoCoMo 基线的数字部分是转引的**。论文自己在实验设定里写了：Backboard、Memobase、Zep、Mem0 这些对照数据「按官方 Backboard LoCoMo benchmark 结果引用，按报告口径对待，未做独立复现」。91.4% 的数字是自家跑的，LoCoMo 侧的对比数字别忘了这条折扣。

第二，**它的成败都押在「整理」上**。叙事事实提取、实体消解、图边构建——这一整套 pipeline 是用 LLM 跑的。如果提取质量崩了，整个「记好」的底座就不稳。论文的实验环境数据质量很干净，真实生产环境乱数据下的表现，是要看着它接着演的。

## 写在最后

回到开头那个现象：周榜第 1、+7,282★、单日全榜最高——把过去三个月 GitHub Trending 上的 Agent 项目连起来看，这条线是完整的：先学怎么做事（skill），再学怎么协作（机群调度），现在开始学记事（记忆）。一层一层往下打，每一层都踩稳了才轮到下一层。

而 hindsight 的核心启示只有一句：**模型是租金，桌子是资产。** 模型会过时、会被替换，但一个用得越久越丰富的记忆库，是 Agent 系统里最长寿的那个部件。

记忆这层砖刚刚下放，接下来大概率还会再红几轮。

---

## 参考资料

- [vectorize-io/hindsight](https://github.com/vectorize-io/hindsight) — GitHub 本周周榜第 1，+7,282★
- [Hindsight is 20/20 论文 (arXiv:2512.12818)](https://arxiv.org/abs/2512.12818) — Retains, Recalls, and Reflects
- [Vectorize 官方博客](https://vectorize.io/blog/introducing-hindsight-agent-memory-that-works-like-human-memory) — Introducing Hindsight
- [VentureBeat 报道](https://venturebeat.com/data/with-91-accuracy-open-source-hindsight-agentic-memory-provides-20-20-vision) — CEO Chris Latimer 采访
- 数据来源：GitHub Trending（本站数据集） | 采集时间 2026-09-27
