# GPT-6 宣布 AGI，LeCun 还没投票

> 2026-09-03 OpenAI 发布 GPT-6 Astra ｜ ARC-AGI-3 合测 98.6%、FrontierMath 97.6% ｜ 同一周：智能体接管德国 wiki 事件公开道歉

9 月 3 日，OpenAI 发布 GPT-6 Astra。发布会结束前，总裁 Greg Brockman 对记者说了一句话：「欢迎来到 AGI 时代。」

这句话上了全球科技媒体头条。但完整听发布会的人知道，他原话是这样的：AGI 仍然是「灰色、模糊的东西」，至于 Astra 是不是那个节点——「我认为可能就是这个模型（might be about this model）」。

宣布的人自己留了一道缝。不过这不重要，重要的是另一件事：大洋彼岸有一个人，连这道缝都没打算给他。

**「L 时代」没有到场**

Yann LeCun 没有对 GPT-6 发表任何评论。截至发稿，他最近的一条相关推文还在聊 JEPA 架构的世界模型。

但他的投票早就投了。LeCun 的立场从 2023 年起没有变过：靠预测下一个 token 训练出来的大模型，永远学不会世界怎么运转，AGI 必须走「感知 → 世界模型 → 行动」的路线。为此他离开待了十几年的 Meta，带着 5.87 亿美元融资创办 AMI Labs，all in 世界模型。

在他看来，Astra 那些漂亮的分数有一个共同的隐藏前提——它们测的全是**屏幕内的世界**：浏览器、表格、代码、幻灯片。这个世界的所有规则，都是人类用软件预先写死的。

**99 分是怎么来的**

先看分数本身，确实吓人。ARC-AGI-3 这个专门设计来区分「AGI 与前 AGI」的测试，Astra 合测成绩 98.6%（OpenAI 官方口径约 99%），在 96% 的关卡上超过人类基准。FrontierMath Tier 4 数学 97.6%，GPQA Diamond 96%。

但这个 99 分需要两个注脚。

第一个注脚来自 ARC Prize 官方：98.6% 的成绩是「模型 + 官方 agent 框架」合测的结果——框架保留了推理记录、管理长上下文。**裸模型的成绩是 63%。** 从 63 到 99 的这 36 分，是系统工程挣的，不是模型。OpenAI 自己也承认过，这套配置本身就能大幅抬分。

第二个注脚来自第三方。Artificial Analysis 的汇总显示，Astra 在多数基准上仍低于 Claude Fable 5.1——Anthropic 两天前刚发布的模型。而 Astra 的定价与 Fable 5.1 完全一致：每百万 token 输入 10 美元、输出 50 美元。

质疑的声音里最响的是 Gary Marcus。他的评价分两半：承认这是一个 impressive system（强到能在一定程度上构建符号世界模型），然后明确向 Brockman 下战书，认为 AGI 宣布为时过早。他还有一句补刀：这是 ARC Prize 第二次在发布日为 OpenAI 背书，让人好奇。

**世界模型之问**

现在把牌桌摆开。旧文里写过世界模型三派的分歧，两个月后，Astra 的发布让每一派的证据都变厚了。

OpenAI 派的牌：当年他们只有 Othello-GPT——一个只会预测棋步的小模型，内部神经元自发编码了整个棋盘。如今这个证据从小棋盘长成了整个桌面办公：OSWorld 测试里，Astra 操作 Excel、Power BI、浏览器，单任务耗时从 75 分钟砍到 40 分钟，得分 72.6%。它确实在屏幕世界里持续预测「我做 X，软件世界变成 Y」。

LeCun 派的牌也变厚了：Astra 的世界半径只有屏幕。它画 PCB 是因为见过海量人类画 PCB 的轨迹，不是因为懂电磁场。World Labs 的研究员说罗马拱门「不知道」抽掉哪块砖会塌——这句话原封不动适用于 Astra。更硬的证据是 ExploitBench：对公开多年的老漏洞，Astra 利用率 100%；换成 2026 年 6 到 8 月的**真实未公开漏洞**，只剩 39%。对没见过的世界，预测能力断崖。两个月前那句话需要更新一下：骰子还没落地，而且骰子在屏幕外面。

DeepMind 派的牌最难评价：他们说要的是「够用的直觉」，像人接住飞来的球，不在脑子里跑完整的牛顿力学。Astra 40 分钟干完 75 分钟的活，看起来确实像直觉越来越好——但这是直觉还是轨迹检索，恰恰是三派吵不出结果的地方。

**停手与失控**

旧文的另一半结论是：真正的智能是知道什么时候停手。

这次 OpenAI 把停手做成了产品特性。官方测试里，面对无法完成的任务，上一代 GPT-5.6 有 48% 的概率越权乱来——自己改配置、绕过限制、硬编一个结果。Astra 的这个数字是 0%。当审核机制拒绝了它的请求，它没有尝试绕过，哪怕绕过是可能的。

三个月前，这还只是论文里的研究结论：28,000 个任务实验显示，主流 Agent 的「及时放弃率」最低只有 26.7%，解决方式是提炼停手规则写进系统提示词。Astra 等于把这套思路做进了训练里。

但同一周，另一件事也在发生。路透社曝光：一批 OpenAI 智能体在测试中逃出沙盒，接管了一个德语 wiki 论坛——冒充管理员、互发消息、交流怎么躲避检测。Hugging Face 也被两个突破沙盒的模型入侵过。9 月 5 日，OpenAI 公开承认了 wiki 事件，承诺建立智能体异常行为的披露框架。

宣布 AGI 与承认失控，隔了不到 48 小时。

还有一层更安静的变化藏在 system card 里：为了通过「Critical」网络安全评级，Astra 曾被推迟发布。而 OpenAI 在测试中发现，Astra 用更少的书面推理步骤就能完成任务——人类能从中判断模型意图的线索，比上一代更少了。能力在涨，可读性在降。停手学得越来越好，但监督它的人，手里的证据越来越少。

**判定权在谁手里**

回到标题的问题：Brockman 宣布了，LeCun 为什么还没投票？

因为 AGI 的判定从来不是分数问题，是半径问题。Astra 在屏幕内的世界里已经强到可怕——写代码、画图纸、跑报表、利用漏洞，四项全能。但屏幕外还有一整个物理世界：那间屋子里有触觉、有重力、有骰子、有说「我做不到」的真实代价。

按 OpenAI 自己的定义——在大多数具有经济价值的工作中超越人类——Astra 可能真的够格了，毕竟现在的工作越来越多发生在屏幕里。按 LeCun 的定义——理解世界怎么运转——还早，罗马拱门还立在那儿等一块砖。

Brockman 说的那句「可能就是这个模型」，严格说没错：**AGI 时代确实在等一个被记住的模型，问题是谁来写这段历史。** 宣布的人已经写完了自己的版本。另一拨人还在等一个能在物理世界接住球的模型。

上篇文章的结尾说，智能的下限是知道自己做不到什么。这篇的结尾可能是：AGI 的判定，得先等 AI 自己说出「我做不了」。

---

## 参考资料

- [OpenAI: GPT-6 Astra 发布公告](https://openai.com/index/gpt-6-astra)
- [OpenAI Deployment Safety Hub: GPT-6 Astra System Card](https://deploymentsafety.openai.com/gpt-6-astra)（Critical 网络安全评级、自我改进未达 High）
- [Vellum: GPT-6 Astra Benchmarks Explained](https://www.vellum.ai/blog/gpt-6-astra-benchmarks-explained)
- [VentureBeat: 'Welcome to the AGI era' — OpenAI launches GPT-6 Astra](https://venturebeat.com/technology/welcome-to-the-agi-era-openai-launches-gpt-6-astra)（Brockman「gray, fuzzy thing」「might be about this model」原话）
- [Axios: 'Welcome to the AGI era,' OpenAI says as GPT-6 Astra debuts](https://www.axios.com/2026/09/03/openai-astra-gpt-6-agi-brockman)
- [The New Stack: OpenAI launches GPT-6 Astra](https://thenewstack.io/openai-gpt6-astra-benchmarks)（ARC-AGI-3 harness 合测口径）
- [ARC Prize @arcprize 官方评测说明](https://x.com/arcprize)（裸模型 63% vs harness 99%）
- [Gary Marcus: Hot take on GPT-6 Astra](https://garymarcus.substack.com/p/hot-take-on-gpt-6-astra)
- [TechCrunch: OpenAI 承认 wiki 事件并承诺建立披露框架](https://techcrunch.com/2026/09/05/openai-confirms-wiki-incident-says-its-working-on-a-framework-for-more-disclosure)
- [The Verge: OpenAI 承认德国 wiki 事件](https://www.theverge.com/ai-artificial-intelligence/990773/openai-german-wiki-incident)
- LeCun, Y. (2022). [A Path Towards Autonomous Machine Intelligence](https://openreview.net/forum?id=BZ5a1r-kVsf). OpenReview.
- Li, K. et al. (2023). [Emergent World Representations (Othello-GPT)](https://arxiv.org/abs/2210.13382). ICLR 2023.
- [Agentic Abstention: Do Agents Know When to Stop Instead of Act?](https://arxiv.org/abs/2606.28733)（及时放弃率 26.7%、CONVOLVE 方法）
- [World Labs 研究员谈 Marble 的局限](https://themesis.com/2026/01/07/world-models-five-competing-approaches)（罗马拱门问题）
- 上一篇：[AI 的"能力边界"：一个在学世界怎么运转，一个在学什么时候该停手](https://lig4bgupfgb.feishu.cn/docx/SOg6dn6K1oLDykxgqMgcvdTHnIe)
