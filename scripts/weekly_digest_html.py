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

ZH_DESC = {'ayghri/i-have-adhd': '强制编码 Agent 把结论放在输出最前面，告别翻找答案（ADHD 友好）', 'bilawalsidhu/gods-eye-view': '浏览器里的侦察卫星模拟器：写实 3D 地球 + 真实开源空间情报', 'tt-a1i/archify': 'Agent 架构/工作流/时序图生成 skill，自包含 HTML 可导出', 'DietrichGebert/ponytail': '让 Agent 像"屋里最懒的资深工程师"一样思考：能不写的代码就不写', 'mattpocock/skills': 'TypeScript 教育者 Matt Pocock 的工程技能集', 'affaan-m/ECC': 'Agent 性能调优系统：技能、本能、记忆、安全，支持多平台', 'cathrynlavery/diagram-design': '38 种编辑部风格图表模板，自包含 HTML+SVG，拒绝 Mermaid 风', 'heygen-com/hyperframes': '写 HTML、渲染成视频，为 Agent 设计的视频生产管线', 'microsoft/markitdown': '微软官方文件转 Markdown 工具，Office/图片/音频全支持', 'THU-MAIC/OpenMAIC': '清华开源多 Agent 互动课堂，一键搭建沉浸式教学'}
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
    """断档周数：按日历周差算（DB 可能缺周，如 2026-08-02），上周减上次上榜周的周数差"""
    r = db.execute("SELECT MAX(week_end) FROM weekly_trending WHERE repo_full_name=? AND week_end<?", (name, prev_end)).fetchone()
    if not r or not r[0]:
        return 99
    from datetime import datetime
    import datetime as dt
    cur = datetime.strptime(r[0], '%Y-%m-%d') + dt.timedelta(days=7)
    gap = 0
    while cur < datetime.strptime(prev_end, '%Y-%m-%d'):
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
def subline(name):
    tag, color = GROUP[name]
    parts = []
    if LANG[name]:
        parts.append(LANG[name])
    if name in prev_names:
        n_weeks = db.execute("SELECT COUNT(DISTINCT week_end) FROM weekly_trending WHERE repo_full_name=? AND week_end<=?", (name, week_end)).fetchone()[0]
        parts.append(f'连续 {n_weeks} 周' if tag == '连续上榜' else '')
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
    (C['blue'], '#EAF0F9', '#3A62A8', 'Skill 从 4 个赛道变成半个榜单',
     '14 个 Skill 类项目合计 <b>81,680★，占全榜 77.0%</b>（上周 4 项 32,412★、39.4%）。总榜新增的 23,887★ 里 Skill 贡献 +49,268★，非 Skill 项目总星反而腰斩——AI 项目形态正在向 Skill 单点收敛。'),
    (C['orange'], '#FDEEE8', '#D14A24', '输出体验成为新卖点',
     '榜首 <b>i-have-adhd（+15,924★）</b>只做一件事：让 Agent 把结论放最上面。加上去 AI 味的 humanizer、no-ai-slop，表达规范类集体上榜——用户的痛点从「Agent 能不能干」转向「Agent 的产出顺不顺手」。'),
    (C['purple'], '#F1EEF8', '#6D5CA8', '官方仓库首次成组进场',
     '<b>openai/skills、openai/plugins、markitdown、chrome-devtools-mcp</b> 四项合计 8,305★（上周仅 1 项 958★）。社区定流行，官方定标准——Skill 正从社区实践升格为平台接口。'),
]
KNIVES = [
    (C['blue'], '加速', 'Skill 生态', '占比 39.4% → 77.0%<br>14 项 81,680★，总榜增量全由它贡献'),
    (C['orange'], '减速', '非 Skill 项目', '总星 49,781★ → 24,400★（-51%）<br>科研 Agent、语音工具本周全部出局'),
    (C['green'], '换挡', '大厂官方仓库', '1 项 958★ → 4 项 8,305★<br>OpenAI / 微软 / 谷歌首次成组上榜'),
]
WATCH = [
    ('Skill 席位守得住吗？', '14 席大概率是峰值，回落至 <b>≥8 席</b>才算市场真扩容'),
    ('新面孔留存几个？', '16 个新面孔留存 <b>≥2 个</b>为健康；上周 19 个只留 4 个（21%）'),
    ('官方仓库会续榜吗？', 'openai/skills、markitdown 若下周继续在榜，官方进场即成趋势'),
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
