#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""周报一图流 v3（手机可读性优先 + 布局重排）
画布 720px（原 1080）→ 飞书手机端缩放比 0.95，字号等效 ×1.5。
结构重排：
  头部 = 标题 + 日期 + 三格关键数字（总星/环比/换血率）
  一、本周主线（3 张叙事卡，标题胶囊 + 结论段）
  二、本周 TOP10（10 行，名字/星数同栏，标签+语言一行，描述一行）
  三、趋势三刀（2×2 网格）
  四、下周观测（3 条，图标 + 问题 + 阈值）
用法：python3 weekly_digest_html_v3.py <week_end YYYY-MM-DD>
"""
import sqlite3, sys, subprocess, os
import numpy as np
from PIL import Image

REPO = '/srv/www/github-trending-wiki'
DB = f'{REPO}/data/github_trending.db'

week_end = sys.argv[1] if len(sys.argv) > 1 else '2026-10-25'
from datetime import datetime, timedelta
week_start = (datetime.strptime(week_end, '%Y-%m-%d') - timedelta(days=6)).strftime('%Y-%m-%d')

db = sqlite3.connect(DB)
rows = list(db.execute(
    "SELECT repo_full_name, weekly_stars, language, rank, description FROM weekly_trending "
    "WHERE week_end=?", (week_end,)))
WK = {r[0]: r[1] for r in rows}
LANG = {r[0]: r[2] or '' for r in rows}
DESC = {r[0]: (r[4] or '').strip() for r in rows}

# ⚠️ 每周手填：新进 TOP10 的 repo 中文描述
ZH_DESC = {
 'cloudflare/security-audit-skill': 'Cloudflare 官方编码 Agent 安全审计 skill：六阶段审计，每个候选漏洞独立复核',
 'Graphify-Labs/graphify': '把代码库连同文档、SQL 结构、配置、PDF 变成可查询知识图谱，不用向量库',
 'akitaonrails/ai-memory': 'Rust 写的跨厂商 agent 长期记忆：Claude Code 停工、Codex 接手不用重讲架构',
 'ruvnet/ruflo': '面向 Claude Code 与 Codex 的 agent 元 harness：多智能体集群、自适应记忆',
 'morluto/rea': '用 agent 逆向一切：从应用行为到原生二进制，一个 MCP 统管逆向工具链',
 'anomalyco/opencode': '开源编码 agent：终端里的 agentic 编程工具',
 'HKUDS/CLI-Anything': '港大数据智能实验室：让所有软件 Agent 原生',
 'vllm-project/vllm': '高吞吐、省显存的 LLM 推理与服务引擎',
 'cathrynlavery/diagram-design': '编辑部风格图表设计：44 种图，自包含 HTML+SVG，拒绝 Mermaid 风',
 'stablyai/orca': '并行 Agent 机群的 ADE：用自己的订阅跑任意编码 Agent',
 'heygen-com/hyperframes': '写 HTML、渲染成视频，为 Agent 设计的视频生产管线',
 'Comfy-Org/ComfyUI': '最强模块化扩散模型 GUI 与后端，节点图驱动本地推理',
 'anthropics/claude-plugins-official': 'Anthropic 官方 Claude Code 插件目录',
 'anthropics/knowledge-work-plugins': 'Anthropic 知识工作插件官方仓库，服务 Claude Cowork',
 'Nutlope/hallmark': '反 AI 垃圾设计 skill：给 Claude Code / Cursor / Codex 的审美矫正包',
 'pbakaus/impeccable': '编码 agent 的设计词汇表：润色引导、批判评审、交付前审计',
 'YuJunZhiXue/dsh-purge': 'DeepSeek Harness 破甲：让所有模型都能越狱，提示词按模型换',
 'affaan-m/ECC': 'agent harness 性能优化系统：技能、直觉、记忆、安全一体',
 'obra/superpowers': 'agentic 技能框架与软件开发方法论，31 万星老项目',
 'TauricResearch/TradingAgents': '多智能体 LLM 金融交易框架',
 'Leonxlnx/taste-skill': '给编码 agent 品味的技能：艺术方向、参考图、浏览器自检',
 'AgriciDaniel/claude-seo': 'Claude Code 通用 SEO 技能包：26 个子技能 + 19 个子 agent',
 'thedotmack/claude-mem': '跨会话持久上下文：压缩 agent 会话记忆并按需注入',
 'multica-ai/andrej-karpathy-skills': '源自 Karpathy 观察的单文件 CLAUDE.md：矫正编码行为',
 'anthropics/skills': 'Anthropic 官方 Agent Skills 公共仓库',
 'AstrBotDevs/AstrBot': '多平台接入的 AI Agent 助手与开发框架',
 'pingdotgg/t3code': 'agent harness 控制台：手机 / 网页 / 桌面遥控本机编码 agent',
 'jakubkrehel/skills': '帮助 agent 做好界面的技能合集',
 'mattpocock/skills': '给真实工程师的技能包：直接搬自作者的 .agents 目录',
 'D4Vinci/Scrapling': '自适应网页抓取框架：单次请求到全站爬取一站搞定',
 'milind-soni/OpenMausBot': '开源 Grok 替代品：自带虚拟机供 bot 操作',
 'Donchitos/Claude-Code-Game-Studios': '把 Claude Code 变成游戏工作室：49 个 agent + 72 个工作流技能',
 'Renhuai123/ziwei-doushu': '紫微斗数开源排盘引擎：基于倪海厦《天纪》，含四化与格局库',
 'max-sixty/worktrunk': 'Git worktree 管理 CLI：为并行 agent 工作流设计',
 'github/spec-kit': 'GitHub 官方规范驱动开发（SDD）起步工具箱',
 'vercel-labs/agent-browser': 'Vercel 出品的浏览器自动化 CLI，给 agent 用',
 'The-PR-Agent/pr-agent': '老牌开源 PR 评审 agent：审查、建议、描述一站搞定',
 'shiyu-coder/Kronos': '金融市场基础模型：对 K 线时间序列做预训练',
 'hyprwm/Hyprland': '高可定制的动态平铺 Wayland 合成器',
}
total_stars = sum(WK.values())
n_projects = len(rows)

prev_end = None; prev_total = None; prev_names = set()
r = db.execute("SELECT MAX(week_end) FROM weekly_trending WHERE week_end<?", (week_end,)).fetchone()
if r and r[0]:
    prev_end = r[0]
    prev_total = db.execute("SELECT SUM(weekly_stars) FROM weekly_trending WHERE week_end=?", (prev_end,)).fetchone()[0] or 0
    prev_names = {x[0] for x in db.execute("SELECT repo_full_name FROM weekly_trending WHERE week_end=?", (prev_end,))}
wow = (total_stars - prev_total) / prev_total * 100 if prev_total else 0
churn = sum(1 for n in WK if n not in prev_names) / n_projects * 100 if prev_names else 0

def weeks_gone(name):
    r = db.execute("SELECT MAX(week_end) FROM weekly_trending WHERE repo_full_name=? AND week_end<?",
                   (name, week_end)).fetchone()
    if not r or not r[0]:
        return 99
    cur = datetime.strptime(r[0], '%Y-%m-%d') + timedelta(days=7)
    gap = 0
    while cur < datetime.strptime(week_end, '%Y-%m-%d'):
        gap += 1; cur += timedelta(days=7)
    return gap

GROUP = {}
for name in WK:
    if name in prev_names:
        GROUP[name] = ('连续上榜', 'orange')
    else:
        g = weeks_gone(name)
        GROUP[name] = (f'断档 {g} 周', 'purple') if g <= 15 else ('新面孔', 'blue')

daily = {}
for name, cnt in db.execute(
        "SELECT repo_full_name, COUNT(*) FROM trending_daily "
        "WHERE date BETWEEN ? AND ? AND repo_full_name IN ({}) GROUP BY repo_full_name".format(
            ','.join('?' * len(WK))), (week_start, week_end, *WK.keys())):
    daily[name] = cnt

def consec_weeks(name, week_end):
    cur = datetime.strptime(week_end, '%Y-%m-%d'); n = 0
    while True:
        r = db.execute("SELECT 1 FROM weekly_trending WHERE repo_full_name=? AND week_end=?",
                       (name, cur.strftime('%Y-%m-%d'))).fetchone()
        if not r: break
        n += 1; cur -= timedelta(days=7)
    return n

def subline(name):
    tag, color = GROUP[name]; parts = []
    if LANG[name]: parts.append(LANG[name])
    if name in prev_names: parts.append(f'连续 {consec_weeks(name, week_end)} 周')
    elif tag.startswith('断档'): parts.append(f'时隔 {tag[3:-1]} 周回归')
    if daily.get(name): parts.append(f'日榜 {daily[name]} 次')
    return ' · '.join(p for p in parts if p)

top10 = sorted(WK.items(), key=lambda kv: kv[1], reverse=True)[:10]

TAG_LABEL = {'blue': '新面孔', 'orange': '连续上榜', 'purple': '回归'}
C = {'blue': '#4C72B0', 'orange': '#E4572E', 'purple': '#8172B2', 'green': '#2E8B57'}

# ⚠️ 每周手填：三段主线叙事（结论前置，正文压到 3-4 行）
NARRATIVES = [
    (C['orange'], '#FDEEE8', '#D14A24', '总量回升 11%，换血率 61%',
     '18 项 98,104★，环比 <b>+11.1%</b>，近八周第三高，仍低于 10-18、10-25 两个脉冲周。上周 15 项里 <b>8 项出局</b>、仅 7 项留存（47%），本周 11 席换血：8 个首次上榜 + 3 个回归。'),
    (C['blue'], '#EAF0F9', '#3A62A8', 'Skills 退烧：9 席缩到 7 席，星数砍 35%',
     'Skill 类 <b>59,364★ → 38,830★（-34.6%）</b>。上周同榜的 security-audit-skill、taste-skill、claude-seo、karpathy-skills 四项全出局；<b>mattpocock/skills</b> 断档 2 周回归 +9,664★，新 skills 只进了 Game-Studios 一个。'),
    (C['purple'], '#F1EEF8', '#6D5CA8', '基建接棒：席位翻倍，t3code 单仓 17,100★',
     '编码基建 <b>3 项 14,673★ → 6 项 34,206★（+133%）</b>。t3code 周星 <b>17,100★</b> 列第一；claude-mem 登顶官方榜 #1；worktrunk 断档 6 周回归即官方 #2。注意力从「教 agent 做事」转向「让 agent 跑稳」。'),
]
# ⚠️ 每周手填：四张赛道卡
KNIVES = [
    (C['blue'], '减速', 'Skill 与插件生态', '7 项 38,830★<br>上周 9 项 59,364★，星数 -34.6%，二线 skills 四项出局'),
    (C['orange'], '加速', '编码 Agent 基础设施', '6 项 34,206★<br>上周 3 项 14,673★，星数 +133%，t3code 单仓贡献一半'),
    (C['purple'], '换挡', '其他 AI 应用', '2 项 10,014★<br>上周 3 项 14,261★，金融 AI 从 TradingAgents 换成 Kronos'),
    (C['red'] if 'red' in C else C['green'], '新增', '非 AI 工具进场', '3 项 15,054★<br>上周 0 项：Scrapling、紫微斗数、Hyprland 三个圈外项目'),
]
# ⚠️ 每周手填：三条观测
WATCH = [
    ('t3code 的 17,100★ 是起点还是脉冲？', '日榜 11-03 后已退出。下周周星 <b>≥10,000★</b> → 动能延续；<b>&lt;10,000★</b> → 确认透支回落'),
    ('Skills 是退烧还是固化？', '席位 <b>≥6 项</b>且新 skills 首上榜 <b>≥2 个</b> → 回暖；<b>≤4 项</b> → 存量固化，只剩老牌轮播'),
    ('圈外项目留得住吗？', '非 AI 工具留存 <b>≥2 项</b> → 回潮成立；<b>≤1 项</b> → 判定为单周噪音'),
]

def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;')

top10_html = ''
for i, (name, stars) in enumerate(top10):
    tag, color = GROUP[name]
    # 星数并入副信息行：序号 → 仓库名 → 描述 → 副信息（含星数）
    top10_html += f'''<div class="row">
    <div class="idx">{i+1}</div>
    <div class="main">
      <div class="l1"><span class="name">{esc(name)}</span><span class="tag" style="background:{C[color]}">{TAG_LABEL[color]}</span></div>
      <div class="desc">{esc(ZH_DESC.get(name) or DESC.get(name, ''))}</div>
      <div class="sub"><span class="st" style="color:{C[color]}">+{stars:,}★</span><span class="sep">·</span>{esc(subline(name))}</div>
    </div>
  </div>'''

narr_html = ''.join(f'''<div class="narr">
  <div class="spine" style="background:{c}"></div>
  <div class="body"><div class="ttl" style="background:{bg};color:{fg}">{t}</div><p>{p}</p></div>
</div>''' for c, bg, fg, t, p in NARRATIVES)

knife_html = ''.join(f'''<div class="knife"><span class="tag" style="background:{c}">{tag}</span>
  <h3>{t}</h3><p>{p}</p></div>''' for c, tag, t, p in KNIVES)

watch_html = ''.join(f'''<div class="watch"><div class="ico" style="background:{c}">◎</div>
  <div class="wbody"><div class="q">{q}</div><div class="m">{m}</div></div></div>'''
    for (q, m), c in zip(WATCH, [C['blue'], C['orange'], C['purple']]))

HTML = f'''<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Noto Sans CJK SC','Noto Sans SC',sans-serif; background:#EEF0F4; width:375px; }}
  .wrap {{ padding:0 14px; }}
  .head {{ padding:24px 14px 18px; }}
  .head h1 {{ font-size:26px; font-weight:900; color:#1A1B26; letter-spacing:.5px; }}
  .head .bar {{ width:52px; height:5px; background:#E4572E; border-radius:3px; margin:10px 0 11px; }}
  .head .meta {{ font-size:13px; color:#3F4459; font-weight:600; }}
  .stats {{ display:grid; grid-template-columns:1.3fr 1fr 1fr; gap:8px; margin:14px 0 2px; }}
  .stat {{ background:#fff; border-radius:11px; padding:11px 10px 9px; box-shadow:0 2px 8px rgba(26,27,38,.05); }}
  .stat .v {{ font-size:19px; font-weight:900; color:#1A1B26; line-height:1.15; font-variant-numeric:tabular-nums; white-space:nowrap; }}
  .stat .v.hl {{ color:#E4572E; }}
  .stat .v.down {{ color:#C0392B; }}
  .stat .k {{ font-size:11px; color:#8A90A5; margin-top:4px; font-weight:500; }}
  .sec {{ font-size:17px; font-weight:900; color:#1A1B26; margin:22px 0 11px; letter-spacing:.3px; }}
  .sec .no {{ color:#E4572E; margin-right:6px; }}
  .narr {{ background:#fff; border-radius:13px; margin-bottom:10px; overflow:hidden;
          box-shadow:0 2px 8px rgba(26,27,38,.05); display:flex; }}
  .narr .spine {{ width:5px; flex-shrink:0; }}
  .narr .body {{ padding:13px 14px 12px; flex:1; }}
  .narr .ttl {{ font-size:15px; font-weight:700; padding:6px 11px; border-radius:7px; margin-bottom:9px; display:inline-block; line-height:1.4; }}
  .narr p {{ font-size:15px; color:#3F4459; line-height:1.8; }}
  .row {{ background:#fff; border-radius:12px; margin-bottom:8px; padding:11px 13px 10px;
         box-shadow:0 2px 6px rgba(26,27,38,.04); display:flex; align-items:flex-start; }}
  .row .idx {{ font-size:15px; font-weight:900; color:#B8BECB; width:18px; flex-shrink:0; padding-top:1px; }}
  .row .main {{ flex:1; min-width:0; }}
  .row .l1 {{ display:flex; align-items:center; gap:7px; margin-bottom:4px; flex-wrap:wrap; }}
  .row .name {{ font-size:15px; font-weight:700; color:#1A1B26; }}
  .row .tag {{ font-size:10px; font-weight:700; color:#fff; padding:2px 7px; border-radius:11px; white-space:nowrap; }}
  .row .sub {{ font-size:12px; color:#8A90A5; margin-top:5px; line-height:1.5; }}
  .row .sub .st {{ font-weight:900; }}
  .row .sub .sep {{ margin:0 5px; color:#C8CDD8; }}
  .row .desc {{ font-size:14px; color:#3F4459; line-height:1.6; }}
  .knives {{ display:flex; flex-direction:column; gap:10px; }}
  .knife {{ background:#fff; border-radius:13px; padding:13px 14px 12px; box-shadow:0 2px 8px rgba(26,27,38,.05); }}
  .knife .tag {{ display:inline-block; font-size:11px; font-weight:700; color:#fff; padding:3px 9px; border-radius:11px; margin-bottom:7px; }}
  .knife h3 {{ font-size:15px; font-weight:700; color:#1A1B26; margin-bottom:5px; }}
  .knife p {{ font-size:13px; color:#3F4459; line-height:1.7; }}
  .knife p b {{ font-weight:900; }}
  .watch {{ background:#fff; border-radius:12px; margin-bottom:8px; padding:11px 13px;
           box-shadow:0 2px 6px rgba(26,27,38,.04); display:flex; align-items:flex-start; gap:9px; }}
  .watch .ico {{ width:20px; height:20px; border-radius:6px; color:#fff; display:flex; align-items:center; justify-content:center; font-size:11px; flex-shrink:0; margin-top:2px; }}
  .watch .wbody {{ flex:1; min-width:0; }}
  .watch .q {{ font-size:15px; font-weight:700; color:#1A1B26; line-height:1.45; }}
  .watch .m {{ font-size:13px; color:#3F4459; line-height:1.7; margin-top:4px; }}
  .watch .m b {{ color:#E4572E; font-weight:900; }}
  .foot {{ background:#E7E9EF; padding:12px 0 13px; margin-top:20px; text-align:center; font-size:11px; color:#8A90A5; }}
</style></head><body>
<div class="head">
  <h1>GitHub Trending 周报</h1><div class="bar"></div>
  <div class="meta">{week_start} ~ {week_end} ｜ {n_projects} 个项目</div>
  <div class="stats">
    <div class="stat"><div class="v hl">{total_stars:,}★</div><div class="k">本周总星</div></div>
    <div class="stat"><div class="v {('down' if wow < 0 else '')}">{wow:+.1f}%</div><div class="k">环比上周</div></div>
    <div class="stat"><div class="v">{churn:.1f}%</div><div class="k">换血率</div></div>
  </div>
</div>
<div class="wrap">
<div class="sec"><span class="no">一</span>本周主线</div>
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
                '--force-device-scale-factor=6', '--window-size=375,4000',
                f'--screenshot={png}.raw.png', tmp_html], check=True)
im = Image.open(f'{png}.raw.png')
a = np.asarray(im.convert('L'))
content_end = np.where((a < 235).any(axis=1))[0].max()
im.crop((0, 0, 2250, int(content_end) + 90)).save(png)
os.remove(f'{png}.raw.png')
print(f'saved: {png} | 2250x{int(content_end)+90}px')
print(f'手机可读性：正文 15px/375画布 → {15*343/375:.1f}px ({15*343/375/2:.1f}pt)')
print(f'  对比 v1: {17*343/1080:.1f}px ({17*343/1080/2:.1f}pt) / v4: {17*343/720:.1f}px ({17*343/720/2:.1f}pt)')
print(f'高度：CSS {int((content_end+90)/6)}px')
