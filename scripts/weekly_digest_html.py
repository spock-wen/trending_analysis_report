#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""周报一图流生成器（HTML → Chromium 截图）
用法：python3 weekly_digest_html.py <week_end YYYY-MM-DD>
数据源：/srv/www/github-trending-wiki/data/github_trending.db（weekly_trending / trending_daily / repo_stats）
输出：reports/weekly/weekly-<week_end>-digest.png（2160px 宽）
叙事文案需人工审校：本脚本只生成骨架 + 榜单数据，NARRATIVES/KNIVES/WATCH 内容按周报正文替换。
"""
import sqlite3, sys, subprocess, os
import numpy as np
from PIL import Image

REPO = '/srv/www/github-trending-wiki'
DB = f'{REPO}/data/github_trending.db'

week_end = sys.argv[1] if len(sys.argv) > 1 else '2026-09-06'
from datetime import datetime, timedelta
week_start = (datetime.strptime(week_end, '%Y-%m-%d') - timedelta(days=6)).strftime('%Y-%m-%d')

db = sqlite3.connect(DB)

# ── 基础数据 ──
rows = list(db.execute(
    "SELECT repo_full_name, weekly_stars, language, rank, description FROM weekly_trending "
    "WHERE week_end=?", (week_end,)))
WK = {r[0]: r[1] for r in rows}
LANG = {r[0]: r[2] or '' for r in rows}
DESC = {r[0]: (r[4] or '').strip() for r in rows}

ZH_DESC = {'ayghri/i-have-adhd': '强制编码 Agent 把结论放在输出最前面，告别翻找答案（ADHD 友好）', 'bilawalsidhu/gods-eye-view': '浏览器里的侦察卫星模拟器：写实 3D 地球 + 真实开源空间情报', 'tt-a1i/archify': 'Agent 架构/工作流/时序图生成 skill，自包含 HTML 可导出', 'DietrichGebert/ponytail': '让 Agent 像"屋里最懒的资深工程师"一样思考：能不写的代码就不写', 'mattpocock/skills': 'TypeScript 教育者 Matt Pocock 的工程技能集', 'affaan-m/ECC': 'Agent 性能调优系统：技能、本能、记忆、安全，支持多平台', 'cathrynlavery/diagram-design': '38 种编辑部风格图表模板，自包含 HTML+SVG，拒绝 Mermaid 风', 'heygen-com/hyperframes': '写 HTML、渲染成视频，为 Agent 设计的视频生产管线', 'microsoft/markitdown': '微软官方文件转 Markdown 工具，Office/图片/音频全支持', 'THU-MAIC/OpenMAIC': '清华开源多 Agent 互动课堂，一键搭建沉浸式教学',
    'alibaba/open-code-review': '阿里开源混合架构代码评审：确定性流水线 + LLM 判断，内部规模验证', 'stablyai/orca': '并行 Agent 机群的 ADE：用自己的订阅跑任意编码 Agent', 'Tencent/WeKnora': '腾讯 LLM 知识平台：文档转 RAG、自主推理 Agent、自维护 Wiki', 'Panniantong/Agent-Reach': '给 Agent 全网视野：读搜 Twitter、Reddit、YouTube、B站、小红书', 'addyosmani/agent-skills': 'Chrome 团队 Addy Osmani 的生产级工程技能包', 'blader/humanizer': '去除文本中 AI 生成痕迹的 Agent skill', 'anthropics/claude-code': 'Claude Code 官方仓库：终端里的 agentic 编码工具', 'danny-avila/LibreChat': '增强版多模型聊天 UI，Agents/MCP/Skills 全支持', 'supabase/supabase': 'Postgres 开发平台，Web/移动/AI 应用的后端底座', 'mksglu/context-mode': 'Agent 上下文窗口优化：工具输出沙箱化、会话记忆持久化', 'huggingface/transformers': 'Hugging Face 模型定义框架，文本/视觉/音频全覆盖', 'max-sixty/worktrunk': 'Git worktree 管理 CLI，为并行 AI Agent 工作流设计', 'kunchenguid/firstmate': '"指挥一个 Agent，用一队人马交付"，单入口多 Agent 协作', 'anthropics/knowledge-work-plugins': 'Anthropic 知识工作插件官方仓库，服务 Claude Cowork', 'openai/plugins': 'OpenAI 官方插件仓库', 'home-assistant/core': '开源自托管家庭自动化主打项目，本地优先',
    'vectorize-io/hindsight': '会学习的 Agent 记忆系统：运行时积累经验',
    'paperclipai/paperclip': '开源 Agent 工作管理，"在公司管好你的 agents"',
    'Panniantong/Agent-Reach': '给 Agent 全网视野：读搜 Twitter、Reddit、YouTube、B站、小红书',
    'pbakaus/impeccable': '给 AI 编码 Agent 的设计语言：24 条命令 + 61 条确定性检测规则',
    'debpalash/VoiceStudio': '全本地语音工作台：ElevenLabs 的开源平替，646 种语言克隆/配音',
    'heygen-com/hyperframes': '写 HTML、渲染成视频，为 Agent 设计的视频生产管线',
    'rohitg00/ai-engineering-from-scratch': 'AI 工程从零到实战：学它、建它、交付它',
    'harry0703/MoneyPrinterTurbo': '一个主题词生成整条高清短视频的自动化流水线',
    'pablostanley/yoinks': '终端里的视频下载工具，无套路无广告',
    'boykopovar/AnyPS5': '把 PS5 可执行文件自动移植到 Linux 和 Windows',
    'HunxByts/GhostTrack': '位置与手机号追踪 / OSINT 信息收集工具',
    'TencentCloud/Octop': '腾讯云自托管 AI 助手，多用户、多 Agent',
    'alirezarezvani/claude-skills': '380 个 Claude Code 技能与插件，覆盖 8 类编码 Agent',
    'longbridge/gpui-kit': '基于 GPUI 的跨平台桌面 Rust GUI 组件库',
    'tile-ai/tilelang': 'GPU/加速器内核开发专用语言，简化高性能算子编写',
    'Effect-TS/effect': 'TypeScript 生产级应用开发框架',
    'pytorch/pytorch': 'PyTorch 深度学习框架官方仓库',
    'flutter/flutter': 'Google 跨平台 UI 工具包',
    'cloudflare/security-audit-skill': 'Cloudflare 官方编码 Agent 安全审计 skill，多阶段可独立验证',
    'paperclipai/paperclip': '开源 Agent 工作管理，"在公司管好你的 agents"',
    'dream-num/univer': 'AI Agent 的 Office 运行时：表格/文档/幻灯片一体化',
    'anthropics/financial-services': 'Anthropic 官方金融服务插件包',
    'superdesigndev/treg': 'Agent 工具的 OpenRouter，社区工具市场',
    'davila7/claude-code-templates': 'Claude Code 配置与监控 CLI',
    'HKUDS/CLI-Anything': '港大数据智能实验室：让所有软件 Agent 原生',
    'TencentCloud/Octop': '腾讯云自托管 AI 助手',
    'cloudflare/quiche': 'QUIC/HTTP3 的 Rust 实现，Chrome 同款协议栈',
    'pytorch/pytorch': 'PyTorch 深度学习框架官方仓库',
    'boykopovar/AnyPS5': '把 PS5 可执行文件自动移植到 Linux 和 Windows：relinker 直接转原生格式，无模拟器',
    'DuarteSantos8/openGym': '自托管健身追踪：训练计划、组数记录、肌肉疲劳度，数据自持',
    'tester-army/e2e': '面向 Web 与移动应用的下一代 e2e 测试框架，Apache-2.0',
    'thedotmack/claude-mem': '跨会话持久上下文：捕获 agent 行为、AI 压缩、注入后续会话',
    'earthtojake/text-to-cad': '给 agent 加 CAD 超能力',
    'pingdotgg/t3code': 'agent harness 控制面：四端远程控制本机所有编码 agent',
    'mvschwarz/openrig': '用 YAML 定义 agent 团队网络，一条命令启动',
    'cursor/plugins': 'Cursor 插件规范与官方插件',
    'EpicGames/raddebugger': '原生用户态、多进程图形调试器，Epic Games 出品',
    'flutter/flutter': 'Google 跨平台 UI 工具包',
    'ranxianglei/billion-context': '上下文压缩插件：100K 窗口、省 5 倍 token、支撑数十亿 token 单会话',
    'morluto/rea': '用 agent 逆向一切：从应用行为到原生二进制，一个 MCP 统管逆向工具链',
    'storytold/artcraft': '面向艺术家与电影人的 AI 创作 IDE：2D 合成 + 3D 场景搭建 + 角色姿态',
    'cathrynlavery/diagram-design': '编辑部风格图表设计：44 种图，自包含 HTML+SVG，拒绝 Mermaid 风',
    'NationalSecurityAgency/ghidra': 'NSA 开源的软件逆向工程框架，反汇编/反编译/脚本全能',
    'anthropics/claude-plugins-official': 'Anthropic 官方 Claude Code 插件目录',
}
total_stars = sum(WK.values())
n_projects = len(rows)

# 上周数据（环比 + 换血）
prev_end = None
prev_total = None
prev_names = set()
r = db.execute("SELECT MAX(week_end) FROM weekly_trending WHERE week_end<?", (week_end,)).fetchone()
if r and r[0]:
    prev_end = r[0]
    prev_total = db.execute("SELECT SUM(weekly_stars) FROM weekly_trending WHERE week_end=?", (prev_end,)).fetchone()[0] or 0
    prev_names = {x[0] for x in db.execute("SELECT repo_full_name FROM weekly_trending WHERE week_end=?", (prev_end,))}
wow = (total_stars - prev_total) / prev_total * 100 if prev_total else 0
churn = sum(1 for n in WK if n not in prev_names) / n_projects * 100 if prev_names else 0

# 组别推导：连续 / 回归（断档周数）/ 新面孔
def weeks_gone(name):
    """断档周数：本次 week_end 之前最后一次上榜周，到本次之间缺席的周数。
    终点必须是本周 week_end（不是上周 prev_end），否则所有断档数少算 1。"""
    r = db.execute("SELECT MAX(week_end) FROM weekly_trending WHERE repo_full_name=? AND week_end<?",
                   (name, week_end)).fetchone()
    if not r or not r[0]:
        return 99
    from datetime import datetime
    import datetime as dt
    cur = datetime.strptime(r[0], '%Y-%m-%d') + dt.timedelta(days=7)
    gap = 0
    while cur < datetime.strptime(week_end, '%Y-%m-%d'):
        gap += 1
        cur += dt.timedelta(days=7)
    return gap

GROUP = {}
for name in WK:
    if name in prev_names:
        GROUP[name] = ('连续上榜', 'orange')
    else:
        g = weeks_gone(name)
        GROUP[name] = (f'断档 {g} 周', 'purple') if g <= 11 else ('新面孔', 'blue')

# 日榜次数（本周期内）
daily = {}
for name, cnt in db.execute(
        "SELECT repo_full_name, COUNT(*) FROM trending_daily "
        "WHERE date BETWEEN ? AND ? AND repo_full_name IN ({}) GROUP BY repo_full_name".format(
            ','.join('?' * len(WK))), (week_start, week_end, *WK.keys())):
    daily[name] = cnt

# ── TOP10 副信息行 ──
def consec_weeks(name, week_end):
    """真实连续上榜周数：从 week_end 往前逐周回数，遇断档即停。"""
    from datetime import datetime
    import datetime as dt
    cur = datetime.strptime(week_end, '%Y-%m-%d')
    n = 0
    while True:
        r = db.execute("SELECT 1 FROM weekly_trending WHERE repo_full_name=? AND week_end=?",
                       (name, cur.strftime('%Y-%m-%d'))).fetchone()
        if not r:
            break
        n += 1
        cur -= dt.timedelta(days=7)
    return n


def subline(name):
    tag, color = GROUP[name]
    parts = []
    if LANG[name]:
        parts.append(LANG[name])
    if name in prev_names:
        parts.append(f'连续 {consec_weeks(name, week_end)} 周')
    elif tag.startswith('断档'):
        parts.append(f'时隔 {tag[3:-1]} 周回归')
    if daily.get(name):
        parts.append(f'日榜 {daily[name]} 次')
    return ' · '.join(p for p in parts if p)

top10 = sorted(WK.items(), key=lambda kv: kv[1], reverse=True)[:10]

# ══ 生成 HTML（叙事区留占位，按周改） ══
TAG_LABEL = {'blue': '新面孔', 'orange': '连续上榜', 'purple': '回归'}
C = {'blue': '#4C72B0', 'orange': '#E4572E', 'purple': '#8172B2', 'green': '#2E8B57'}

# TODO(每周手填)：NARRATIVES / KNIVES / WATCH 按周报正文更新
NARRATIVES = [
    (C['orange'], '#FDEEE8', '#D14A24', '一个项目贡献 75.8% 的星，榜单被"逆向"接管',
     '10 个项目 316,460★（上周 13 项 61,769★，<b>+412.3%</b>，近 20 周最高）。但 239,923★ 来自 <b>morluto/rea</b> 一个仓库，占全榜 <b>75.8%</b>、是第二名 artcraft 的 <b>13 倍</b>；剔除它，其余 9 项合计 76,537★、环比仅 +23.9%。换血率 60.0%（上周 76.9%），上周 13 席只留住 4 席。'),
    (C['blue'], '#EAF0F9', '#3A62A8', '逆向工程从"专家工具"变成"agent 的一个 MCP"',
     'rea 是一个 MCP 服务器：把 Hopper / Ghidra / IDA、JavaScript/Electron 静态分析、Android APK、SQLite、固件、抓包分析全部接到 agent 手上，10 月 13 日 rea.tools 登上 HN 首页（<b>805 赞、337 评论</b>）。它不自研反编译器——深度分析仍依赖你装好的 Ghidra/IDA/Hopper，rea 做的是把这堆工具包成带契约、带 Evidence ID、可存快照的 MCP 接口。'),
    (C['purple'], '#F1EEF8', '#6D5CA8', '上下文管理连续两周占位，创作与硬件同步降温',
     '<b>mksglu/context-mode</b>（+4,438★）时隔 3 周回归：工具输出沙箱化（315KB → 5.4KB）、会话记忆落 SQLite，是本周唯一"基础设施型"续榜项目。与此同时，上周的硬件移植 <b>AnyPS5 周星 -23.9%</b>（+21,365★ → +16,250★）、AI 内容创作上周仅剩 hyperframes 一席（+4,081★）本周 +38.2% 回血，而 e2e、openGym、text-to-cad、claude-mem、t3code、openrig 六个上周项目全部出局。'),
]
KNIVES = [
    (C['orange'], '换挡', 'Agent/Skill 工作流', '5 项 264,903★ vs 上周 7 项 21,387★<br>其中 rea 一项占 239,923★，席位由 7 缩到 5'),
    (C['blue'], '加速', '大厂官方与产品级', 'Ghidra + claude-plugins 2 项 11,189★<br>vs 上周 2 项 1,003★（raddebugger、flutter）'),
    (C['purple'], '降温', '独立应用与硬件工具', 'AnyPS5 一项 16,250★，环比 -23.9%<br>上周 openGym/e2e 合计 13,933★ 全部出局'),
    (C['green'], '新品类', '逆向工程进入 agent 视野', 'rea 一周 239,923★ + Ghidra 时隔 6 周回归<br>DX-Ball 3,205 个用例、63 字节全对上'),
]
WATCH = [
    ('rea 是脉冲还是新品类？', '周星 <b>≥50,000★</b> 则"agent 逆向"从首发脉冲变常驻主线；跌破 <b>20,000★</b> 且 HN 热度不再，则视为一次性传播事件'),
    ('逆向赛道能否扩容？', '除 rea 外再出现 <b>≥1 个逆向/安全类</b>项目且周星 <b>≥3,000★</b>，则 Ghidra 回归不是巧合，赛道成立；否则只有单一玩家'),
    ('上下文管理能否回到上周水位？', 'context-mode + billion-context 合计周星回到 <b>≥8,000★</b>（本周 5,326★），则"上下文工程"仍是常驻需求'),
]

def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;')

top10_html = ''
for i, (name, stars) in enumerate(top10):
    tag, color = GROUP[name]
    s = f'+{stars:,}<span style="font-size:15px">★</span>'
    top10_html += f'''<div class="row">
    <div class="idx">{i+1:02d}</div>
    <div class="main">
      <div class="l1"><span class="name">{esc(name)}</span><span class="tag" style="background:{C[color]}">{TAG_LABEL[color]}</span></div>
      <div class="desc">{esc(ZH_DESC.get(name) or DESC.get(name, ''))}</div>
      <div class="sub">{esc(subline(name))}</div>
    </div>
    <div class="stars"><div class="wk" style="color:{C[color]}">{s}</div></div>
  </div>'''

narr_html = ''.join(f'''<div class="narr">
  <div class="spine" style="background:{c}"></div>
  <div class="body"><div class="ttl" style="background:{bg};color:{fg}">{t}</div><p>{p}</p></div>
</div>''' for c, bg, fg, t, p in NARRATIVES)

knife_html = ''.join(f'''<div class="knife"><span class="tag" style="background:{c}">{tag}</span>
  <h3>{t}</h3><p>{p}</p></div>''' for c, tag, t, p in KNIVES)

watch_html = ''.join(f'''<div class="watch"><div class="ico" style="background:{c}">◎</div>
  <div class="q">{q}</div><div class="m">{m}</div></div>'''
    for (q, m), c in zip(WATCH, [C['blue'], C['orange'], C['purple']]))

HTML = f'''<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Noto Sans CJK SC','Noto Sans SC',sans-serif; background:#EEF0F4; width:1080px; }}
  .wrap {{ padding:0 36px; }}
  .head {{ padding:44px 36px 34px; display:flex; justify-content:space-between; align-items:flex-start; }}
  .head h1 {{ font-size:40px; font-weight:900; color:#1A1B26; letter-spacing:1px; }}
  .head .bar {{ width:96px; height:7px; background:#E4572E; border-radius:4px; margin:14px 0 16px; }}
  .head .meta {{ font-size:19px; color:#4A4F66; font-weight:500; }}
  .head .toc {{ font-size:16px; color:#9AA0B5; margin-top:8px; }}
  .head .right {{ text-align:right; padding-top:6px; }}
  .head .num {{ font-size:42px; font-weight:900; color:#E4572E; }}
  .head .lbl {{ font-size:15px; color:#9AA0B5; margin-top:4px; }}
  .sec {{ font-size:28px; font-weight:900; color:#1A1B26; margin:38px 0 20px; letter-spacing:1px; }}
  .sec .no {{ color:#E4572E; margin-right:10px; }}
  .narr {{ background:#fff; border-radius:16px; margin-bottom:16px; overflow:hidden;
          box-shadow:0 2px 10px rgba(26,27,38,.05); display:flex; }}
  .narr .spine {{ width:7px; flex-shrink:0; }}
  .narr .body {{ padding:22px 26px 20px; flex:1; }}
  .narr .ttl {{ font-size:21px; font-weight:700; padding:10px 16px; border-radius:9px; margin-bottom:14px; display:inline-block; }}
  .narr p {{ font-size:17px; color:#4A4F66; line-height:1.65; }}
  .row {{ background:#fff; border-radius:14px; margin-bottom:16px; padding:20px 26px 18px;
         box-shadow:0 2px 8px rgba(26,27,38,.04); display:flex; align-items:flex-start; }}
  .row .idx {{ font-size:26px; font-weight:900; color:#C3C8D4; width:52px; flex-shrink:0; padding-top:2px; }}
  .row .main {{ flex:1; min-width:0; padding-right:20px; }}
  .row .l1 {{ display:flex; align-items:center; gap:14px; margin-bottom:8px; }}
  .row .name {{ font-size:20px; font-weight:700; color:#1A1B26; }}
  .row .tag {{ font-size:13px; font-weight:700; color:#fff; padding:4px 12px; border-radius:20px; white-space:nowrap; }}
  .row .desc {{ font-size:16px; color:#4A4F66; margin-bottom:5px; }}
  .row .sub {{ font-size:14px; color:#9AA0B5; margin-top:2px; }}
  .row .stars {{ text-align:right; flex-shrink:0; padding-top:2px; }}
  .row .wk {{ font-size:22px; font-weight:900; }}
  .knives {{ display:flex; gap:20px; }}
  .knife {{ flex:1; background:#fff; border-radius:16px; padding:24px 24px 20px; box-shadow:0 2px 10px rgba(26,27,38,.05); }}
  .knife .tag {{ display:inline-block; font-size:14px; font-weight:700; color:#fff; padding:5px 16px; border-radius:20px; margin-bottom:14px; }}
  .knife h3 {{ font-size:20px; font-weight:700; color:#1A1B26; margin-bottom:10px; }}
  .knife p {{ font-size:15.5px; color:#4A4F66; line-height:1.55; }}
  .watch {{ background:#fff; border-radius:14px; margin-bottom:16px; padding:18px 26px;
           box-shadow:0 2px 8px rgba(26,27,38,.04); display:flex; align-items:center; gap:18px; }}
  .watch .ico {{ width:34px; height:34px; border-radius:9px; color:#fff; display:flex; align-items:center; justify-content:center; font-size:18px; flex-shrink:0; }}
  .watch .q {{ font-size:18px; font-weight:700; color:#1A1B26; width:250px; flex-shrink:0; }}
  .watch .m {{ font-size:16px; color:#4A4F66; }}
  .watch .m b {{ color:#E4572E; }}
  .foot {{ background:#E7E9EF; padding:20px 0 22px; margin-top:36px; text-align:center; font-size:14px; color:#9AA0B5; }}
</style></head><body>
<div class="head">
  <div class="left"><h1>GitHub Trending 周报</h1><div class="bar"></div>
    <div class="meta">{week_start} ~ {week_end} ｜ {n_projects} 个项目 · 环比 {wow:+.1f}% · 换血率 {churn:.1f}%</div>
    <div class="toc">本图结构 ｜ 一、核心叙事 · 二、本周 TOP10 · 三、趋势三刀 · 四、下周观测</div></div>
  <div class="right"><div class="num">{total_stars:,}★</div><div class="lbl">本周总星</div></div>
</div>
<div class="wrap">
<div class="sec"><span class="no">一</span>核心叙事</div>
{narr_html}
<div class="sec"><span class="no">二</span>本周 TOP10（按周星排序）</div>
{top10_html}
<div class="sec"><span class="no">三</span>趋势三刀</div>
<div class="knives">{knife_html}</div>
<div class="sec"><span class="no">四</span>下周观测</div>
{watch_html}
</div>
<div class="foot">数据源：GitHub Trending ｜ 统计口径：周榜 7 天累计星数 ｜ 完整榜单与项目链接见知识库原文</div>
</body></html>'''

tmp_html = f'/tmp/weekly_digest_{week_end}.html'
open(tmp_html, 'w').write(HTML)
png = f'{REPO}/reports/weekly/weekly-{week_end}-digest.png'
subprocess.run(['chromium', '--headless=new', '--no-sandbox', '--disable-gpu',
                '--disable-dev-shm-usage', '--hide-scrollbars',
                '--force-device-scale-factor=2', '--window-size=1080,3600',
                f'--screenshot={png}.raw.png', tmp_html], check=True)
im = Image.open(f'{png}.raw.png')
a = np.asarray(im.convert('L'))
content_end = np.where((a < 235).any(axis=1))[0].max()
im.crop((0, 0, 2160, int(content_end) + 46)).save(png)
os.remove(f'{png}.raw.png')
print(f'saved: {png} | 2160x{int(content_end)+46}px | total {total_stars:,}★ wow {wow:+.1f}% churn {churn:.1f}%')
print('NOTE: NARRATIVES/KNIVES/WATCH 为上周内容，每周发文前需按周报正文更新')
