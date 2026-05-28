# -*- coding: utf-8 -*-
import json, requests, subprocess, datetime

TODAY = "2026-05-28"

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

# ===== 标题 =====
rows.append([{"tag": "md", "text": "\U0001f4ca GitHub Trending 日报 \uff5c " + TODAY}])
rows.append([{"tag": "text", "text": " "}])

# ===== 概览 =====
rows.append([{"tag": "text", "text": "概览：17 个项目上榜 \uff5c 语言分布：Python 5 \u00b7 TypeScript 3 \u00b7 Shell 3 \u00b7 JavaScript 2 \u00b7 Rust 1 \u00b7 HTML 1 \u00b7 其他 2"}])
rows.append([{"tag": "text", "text": "今日总 Star 增长：20,755 \u2b50 \uff5c 最高单项目：Understand-Anything (+4,466)"}])
rows.append([{"tag": "text", "text": " "}])

# ===== 今日完整榜单 =====
rows.append([{"tag": "md", "text": "\U0001f4cb 今日完整榜单"}])
rows.append([{"tag": "text", "text": " "}])

# 按排名排列
projects = [
    (1, "harry0703/MoneyPrinterTurbo", "利用 AI 大模型一键生成高清短视频", "Python", 1737, 61785, "https://github.com/harry0703/MoneyPrinterTurbo"),
    (2, "Lum1104/Understand-Anything", "将任何代码转化为交互式知识图谱，可探索、搜索和提问。支持 Claude Code、Codex、Cursor、Copilot、Gemini CLI 等", "TypeScript", 4466, 39616, "https://github.com/Lum1104/Understand-Anything"),
    (3, "hardikpandya/stop-slop", "去除 AI 写作痕迹的技能文件，让 AI 输出更自然", "\u2014", 664, 5637, "https://github.com/hardikpandya/stop-slop"),
    (4, "affaan-m/ECC", "Agent 性能优化系统。集技能、直觉、记忆、安全和研究优先开发于一体，支持 Claude Code、Codex、Cursor 等", "JavaScript", 2062, 195964, "https://github.com/affaan-m/ECC"),
    (5, "anthropics/knowledge-work-plugins", "Anthropic 开源的知识工作者插件库，主要用于 Claude Cowork 中的知识工作场景", "Python", 695, 17231, "https://github.com/anthropics/knowledge-work-plugins"),
    (6, "Leonxlnx/taste-skill", "给 AI 赋予「好品味」，阻止它生成无聊、套话式的通用内容", "Shell", 2715, 24109, "https://github.com/Leonxlnx/taste-skill"),
    (7, "p-e-w/heretic", "语言模型的审查自动去除工具，完全自动化移除内容限制", "Python", 219, 21989, "https://github.com/p-e-w/heretic"),
    (8, "shiyu-coder/Kronos", "金融市场的 Foundation Model，用大模型建模金融市场的语言", "Python", 402, 26860, "https://github.com/shiyu-coder/Kronos"),
    (9, "mukul975/Anthropic-Cybersecurity-Skills", "754 个结构化网络安全技能，覆盖 MITRE ATT&CK、NIST CSF 2.0 等 5 个框架、26 个安全领域", "Python", 885, 10906, "https://github.com/mukul975/Anthropic-Cybersecurity-Skills"),
    (10, "twentyhq/twenty", "Salesforce 的开源替代品，专为 AI 时代设计的 CRM 系统", "TypeScript", 520, 47306, "https://github.com/twentyhq/twenty"),
    (11, "Chachamaru127/claude-code-harness", "Claude Code 专用开发框架，通过自主的 Plan\u2192Work\u2192Review 循环实现高质量开发", "Shell", 143, 1798, "https://github.com/Chachamaru127/claude-code-harness"),
    (12, "DigitalPlatDev/FreeDomain", "DigitalPlat 免费域名服务，人人都可用的免费域名", "HTML", 2223, 169056, "https://github.com/DigitalPlatDev/FreeDomain"),
    (13, "obra/superpowers", "Agent 技能框架与软件开发方法论，经过实践验证的 Agent 开发方案", "Shell", 1680, 209460, "https://github.com/obra/superpowers"),
    (14, "byoungd/English-level-up-tips", "离谱的英语学习指南，从基础到高级的系统性英语学习方法", "\u2014", 1133, 46450, "https://github.com/byoungd/English-level-up-tips"),
    (15, "iii-hq/iii", "首个实现实时编排、扩展和观测所有服务的全栈 Rust 平台", "Rust", 427, 16829, "https://github.com/iii-hq/iii"),
    (16, "Axorax/awesome-free-apps", "PC 和移动端最佳免费应用的精选合集", "JavaScript", 728, 5841, "https://github.com/Axorax/awesome-free-apps"),
    (17, "moeru-ai/airi", "自托管的 AI 伴侣，支持实时语音对话、Minecraft/Factorio 游戏交互，类 Neuro-sama 的开源实现", "TypeScript", 56, 40196, "https://github.com/moeru-ai/airi"),
]

for rank, name, desc, lang, stars, total, url in projects:
    lang_str = " \u00b7 " + lang if lang != "\u2014" else ""
    rows.append([{"tag": "md", "text": f"{rank}. **{name}** \u2014 {desc}{lang_str} \u00b7 +{stars}\u2b50 \uff5c 总 {total}\u2b50"}])

rows.append([{"tag": "text", "text": " "}])

# ===== 连续上榜 =====
rows.append([{"tag": "md", "text": "\U0001f525 连续上榜（连续 2 天以上）"}])
rows.append([{"tag": "text", "text": " "}])

consecutive = [
    ("Lum1104/Understand-Anything", "Understand-Anything", 7, 4466, "代码知识图谱工具，连续 7 天霸榜，单日 +4,466\u2b50，热度持续飙升"),
    ("anthropics/knowledge-work-plugins", "Anthropic", 5, 695, "知识工作者插件库，连续 5 天上榜"),
    ("mukul975/Anthropic-Cybersecurity-Skills", "Anthropic-Cybersecurity-Skills", 5, 885, "结构化网络安全技能集，连续 5 天备受关注"),
    ("hardikpandya/stop-slop", "stop-slop", 3, 664, "去 AI 写作痕迹工具，连续 3 天上榜，反映社区对 AI 输出自然度的追求"),
    ("Leonxlnx/taste-skill", "taste-skill", 3, 2715, "AI 品味提升工具，连续 3 天热度不减，单日 +2,715\u2b50"),
    ("affaan-m/ECC", "ECC", 3, 2062, "Agent 性能优化系统，连续 3 天在榜"),
    ("Axorax/awesome-free-apps", "awesome-free-apps", 3, 728, "免费应用合集，连续 3 天有新关注"),
    ("DigitalPlatDev/FreeDomain", "FreeDomain", 2, 2223, "免费域名服务，连续 2 天上榜，+2,223\u2b50 增长强劲"),
    ("twentyhq/twenty", "twenty", 2, 520, "开源 CRM，连续 2 天在榜"),
]

for name, org, days, stars, note in consecutive:
    rows.append([{"tag": "text", "text": "\u00b7 " + name + "\uff08" + org + "\uff09\u2014 连续 " + str(days) + " 天 \uff5c +" + str(stars) + "\u2b50"}])

rows.append([{"tag": "text", "text": " "}])

# ===== 深度分析 =====
rows.append([{"tag": "md", "text": "\U0001f9e0 深度分析"}])
rows.append([{"tag": "text", "text": " "}])

rows.append([{"tag": "text", "text": "今天榜单释放出一个强烈信号：AI Agent 生态正在从「能做」向「做好」全面转型。连续 7 天霸榜的 Understand-Anything（+4,466\u2b50/日）把代码转化为交互式知识图谱，解决了 Agent 开发中的核心痛点——代码理解。这不是一个锦上添花的工具，而是 Agent 工作流的底层基础设施。"}])
rows.append([{"tag": "text", "text": " "}])

rows.append([{"tag": "text", "text": "另一个值得关注的趋势是「AI 输出品质」主题的爆发。stop-slop（去 AI 痕迹，连续 3 天）、taste-skill（好品味赋予，+2,715\u2b50/日，连续 3 天）和 ECC（Agent 优化系统，连续 3 天）同时出现在榜单上，说明开发者社区已经不满足于让 AI「能写」，而是追求「写得像人」、「写得有品味」。这种从量到质的转变，标志着 AI 内容生产进入精细化运营阶段。"}])
rows.append([{"tag": "text", "text": " "}])

rows.append([{"tag": "text", "text": "再看「技能文件生态」：Anthropic-Cybersecurity-Skills（连续 5 天）和 knowledge-work-plugins（连续 5 天）代表了大厂对 Agent 技能模块化的押注——将 754 个网络安全技能映射到 MITRE ATT&CK 等框架，让 AI Agent 能像拼乐高一样组合领域知识。这可能是未来 Agent 开发的核心范式：领域知识颗粒化、可复用、可组合。此外，superpowers（+1,680\u2b50）作为一个 Agent 技能框架与开发方法论，也在验证这条路径。"}])
rows.append([{"tag": "text", "text": " "}])

rows.append([{"tag": "text", "text": "行动建议：如果你在寻找创业或副业方向，不妨关注「Agent 技能文件」赛道——选择一个结构化程度高的垂直领域（网络安全、金融合规、医疗诊断等），将领域知识系统化为 Agent 可调用的技能包。这波浪潮的赢家不会是做大模型的，而是让大模型在具体领域真正好用的人。"}])

# ===== 发送 =====
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
