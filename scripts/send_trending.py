# -*- coding: utf-8 -*-
import json, requests, subprocess, datetime

TODAY = datetime.date.today().isoformat()

# 获取 token
result = subprocess.run(
    ['bash', '-c', 'source /root/.hermes/profiles/radar/.env && echo $FEISHU_APP_SECRET'],
    capture_output=True, text=True
)
APP_SECRET = result.stdout.strip()
APP_ID = 'cli_a916e5b5a1b8dcd4'

resp = requests.post(
    'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
    json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=10
)
resp_json = resp.json()
if 'tenant_access_token' not in resp_json:
    print("ERROR: Failed to get token", resp_json)
    exit(1)
tenant_token = resp_json['tenant_access_token']

rows = []

# 标题
rows.append([{"tag": "md", "text": "📊 **GitHub Trending 日报** `" + TODAY + "`"}])
rows.append([{"tag": "text", "text": " "}])

# 概览
rows.append([{"tag": "md", "text": "**14** 个项目上榜 ｜ 语言分布：TypeScript 4 · Python 4 · JavaScript 2 · Shell 1 · C# 1 · HTML 1 · 其他 1"}])
rows.append([{"tag": "md", "text": "今日总 Star 增长：**16,724** ⭐ ｜ 最高单项目：Understand-Anything (+4,721)"}])
rows.append([{"tag": "text", "text": " "}])

# 深度分析
rows.append([{"tag": "md", "text": "🧠 **深度分析：AI Agent 的\u201c品味\u201d与\u201c精细化\u201d时代**"}])
rows.append([{"tag": "text", "text": " "}])

rows.append([{"tag": "md", "text": "🔍 **趋势洞察**：今天榜单最突出的信号是 AI Agent 输出品质的\u201c反身性\u201d需求爆发。stop-slop（去 AI 写作痕迹）和 taste-skill（给 AI 好品味）双双连续上榜，说明当 AI 生成内容成为常态后，开发者社区开始认真思考\u201c如何不让 AI 写的东西像 AI 写的\u201d。这是一个从\u201c能用\u201d到\u201c好用\u201d再到\u201c自然\u201d的演进信号。同时，Understand-Anything 连续 6 天霸榜（+4,721/日），把代码转化为可探索的知识图谱，代表了 Agent 工具链从\u201c对话\u201d到\u201c结构化理解\u201d的升级方向。"}])
rows.append([{"tag": "text", "text": " "}])

rows.append([{"tag": "md", "text": "💡 **亮点解读**：anthropics/knowledge-work-plugins（开源的知识工作者插件库）和 Anthropic-Cybersecurity-Skills（754 个结构化网络安全技能）代表了\u201c技能文件生态\u201d的快速扩展——不再只是单个 Agent 能力，而是将领域知识体系化、模块化、可复用地提供给 AI Agent。thedotmack/claude-mem（持久化上下文记忆）则直击 Agent 的核心痛点——会话之间的记忆断层。这些项目共同指向一个方向：Agent 正在从玩具进化成真正的生产力工具，而基础设施层（记忆、技能、知识图谱）正在快速补齐。"}])
rows.append([{"tag": "text", "text": " "}])

rows.append([{"tag": "md", "text": "📌 **行动建议**：如果你是 AI 应用开发者，今天榜单上最值得关注的是\u201cAgent 技能文件\u201d这条赛道——将特定领域的知识结构化、插件化，供给 LLM Agent 调用。网络安全、法律、医疗等结构化程度高的领域尤其值得切入。如果你是个人开发者，ai-engineering-from-scratch（连续 7 天上榜）是当前最热门的 AI 工程实战教程，适合系统学习 AI 工程最佳实践。"}])
rows.append([{"tag": "text", "text": " "}])

# 连续上榜
rows.append([{"tag": "md", "text": "🔥 **连续上榜（\u22652天）**"}])
rows.append([{"tag": "md", "text": "• **rohitg00/ai-engineering-from-scratch** — 连续 7 天 🔥 从零学 AI 工程，热度不减"}])
rows.append([{"tag": "md", "text": "• **Lum1104/Understand-Anything** — 连续 6 天 🔥 代码知识图谱，单日+4,721"}])
rows.append([{"tag": "md", "text": "• **anthropics/knowledge-work-plugins** — 连续 4 天 知识工作者插件库"}])
rows.append([{"tag": "md", "text": "• **mukul975/Anthropic-Cybersecurity-Skills** — 连续 4 天 网络安全技能集"}])
rows.append([{"tag": "md", "text": "• **affaan-m/ECC / stop-slop / taste-skill / awesome-free-apps** — 连续 2 天"}])
rows.append([{"tag": "text", "text": " "}])

# 完整榜单
rows.append([{"tag": "md", "text": "📋 **今日完整榜单**"}])
rows.append([{"tag": "text", "text": " "}])

rows.append([{"tag": "md", "text": "1️⃣ **Lum1104/Understand-Anything** ⭐+4,721\n   TypeScript \u00b7 总 35,613 ⭐\n   把代码转化为交互式知识图谱，支持 Claude Code、Codex、Cursor 等。可探索、搜索、提问的代码理解工具。"}])

rows.append([{"tag": "md", "text": "2️⃣ **affaan-m/ECC** ⭐+1,912\n   JavaScript \u00b7 总 194,266 ⭐\n   Agent 性能优化系统。技能、直觉、记忆、安全一体化，专为 Claude Code、Codex、Cursor 等设计。"}])

rows.append([{"tag": "md", "text": "3️⃣ **rohitg00/ai-engineering-from-scratch** ⭐+2,169\n   Python \u00b7 总 20,635 ⭐\n   AI 工程从零到实战。学会、构建、交付——三阶段 AI 工程教程，连续 7 天霸榜。"}])

rows.append([{"tag": "md", "text": "4️⃣ **anthropics/knowledge-work-plugins** ⭐+1,698\n   Python \u00b7 总 16,620 ⭐\n   Anthropic 开源的知识工作者插件库，主要用于 Claude Cowork 环境中的知识工作场景。"}])

rows.append([{"tag": "md", "text": "5️⃣ **mukul975/Anthropic-Cybersecurity-Skills** ⭐+871\n   Python \u00b7 总 10,061 ⭐\n   754 个结构化网络安全技能，覆盖 MITRE ATT&CK、NIST CSF 等 5 个安全框架、26 个安全领域。"}])

rows.append([{"tag": "md", "text": "6️⃣ **hardikpandya/stop-slop** ⭐+547\n   总 4,978 ⭐\n   从文案中去除 AI 写作痕迹的技能文件。为追求自然、人类化的 AI 输出而生。"}])

rows.append([{"tag": "md", "text": "7️⃣ **Leonxlnx/taste-skill** ⭐+1,440\n   Shell \u00b7 总 21,459 ⭐\n   给 AI 赋予\u201c好品味\u201d，阻止它生成无聊、套话式的内容。连续 2 天热度飙升。"}])

rows.append([{"tag": "md", "text": "8️⃣ **DigitalPlatDev/FreeDomain** ⭐+1,127\n   HTML \u00b7 总 167,235 ⭐\n   人人都可用的免费域名服务。"}])

rows.append([{"tag": "md", "text": "9️⃣ **jellyfin/jellyfin** ⭐+91\n   C# \u00b7 总 52,358 ⭐\n   自由软件媒体系统，开源 NAS/媒体中心的服务器后端。"}])

rows.append([{"tag": "md", "text": "🔟 **Axorax/awesome-free-apps** ⭐+738\n   JavaScript \u00b7 总 5,222 ⭐\n   PC 和移动端最佳免费应用的精选合集。连续 2 天上榜。"}])

rows.append([{"tag": "md", "text": "1️⃣1️⃣ **twentyhq/twenty** ⭐+237\n   TypeScript \u00b7 总 46,820 ⭐\n   Salesforce 的开源替代品，专为 AI 时代设计的企业 CRM。"}])

rows.append([{"tag": "md", "text": "1️⃣2️⃣ **Open-Dev-Society/OpenStock** ⭐+128\n   TypeScript \u00b7 总 12,064 ⭐\n   开源股票追踪平台。实时价格、个性化提醒、公司深度分析，永久免费。"}])

rows.append([{"tag": "md", "text": "1️⃣3️⃣ **thedotmack/claude-mem** ⭐+319\n   TypeScript \u00b7 总 78,606 ⭐\n   Agent 跨会话持久化上下文记忆。记录、压缩、注入——解决 AI Agent 的记忆断层问题。"}])

rows.append([{"tag": "md", "text": "1️⃣4️⃣ **st-tech/ppf-contact-solver** ⭐+207\n   Python \u00b7 总 3,460 ⭐\n   物理仿真接触求解器，支持布料、固体和杆状物体的基于物理的仿真。"}])

# 发送
post_payload = json.dumps({"zh_cn": {"content": rows}}, ensure_ascii=False)
headers = {"Authorization": "Bearer " + tenant_token, "Content-Type": "application/json; charset=utf-8"}

response = requests.post(
    "https://open.feishu.cn/open-apis/im/v1/messages",
    params={"receive_id_type": "chat_id"},
    headers=headers,
    json={"receive_id": "oc_b269ff6fab6e321a35e344ea5984e985", "msg_type": "post", "content": post_payload},
    timeout=10
)

print("Send result:", response.status_code, response.text)
