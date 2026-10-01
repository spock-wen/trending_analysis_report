#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""月报一图流生成器（HTML → Chromium 截图）
用法：python3 monthly_digest_html.py 2026-09
数据源：reports/monthly/monthly-2026-09.md（月报正文，cron 先写正文再跑本脚本）
输出：reports/monthly/monthly-2026-09-digest.png（2160px 宽）
结构（全自动解析正文，无需手填文案）：
  头部统计 / 一、本月格局（三个结构性变化）/ 二、月度 TOP10 / 三、三大王冠 / 四、关键指标环比
着色口径：daily_signals CATEGORY_RULES，与月报「领域热度趋势」表及条形图一致。
"""
import re, sys, os, subprocess
import numpy as np
from PIL import Image

REPO = '/srv/www/github-trending-wiki'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from daily_signals import classify_category

month = sys.argv[1] if len(sys.argv) > 1 else '2026-09'
md_path = f'{REPO}/reports/monthly/monthly-{month}.md'
text = open(md_path, encoding='utf-8').read()
lines = text.split('\n')

# ── 通用小工具 ──
def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def mdhtml(s):
    """转义后把 **bold** 转 <b>"""
    s = esc(s.strip())
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)

def parse_table(start):
    """从 start 行起返回表格数据行（跳过空行/表头/分隔线），(header, rows, end_idx)"""
    header = None
    rows = []
    i = start
    while i < len(lines) and not lines[i].strip():  # 跳过表格前空行
        i += 1
    while i < len(lines) and lines[i].strip().startswith('|'):
        cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
        if set(''.join(cells)) <= set('-: '):   # 分隔线
            pass
        elif header is None:
            header = cells
        else:
            rows.append(cells)
        i += 1
    return header, rows, i

def find_h2(key):
    for i, l in enumerate(lines):
        if l.startswith('## ') and key in l:
            return i
    return -1

def h3_blocks(sec_start, sec_end):
    """(h3_title, table_end, first_row) for each h3 in section"""
    out = []
    i = sec_start
    while i < sec_end:
        if lines[i].startswith('### '):
            title = lines[4:].strip() if False else lines[i][4:].strip()
            _, rows, end = parse_table(i + 1)
            out.append((title, rows[0] if rows else [], end))
            i = end
        else:
            i += 1
    return out

# ── 头部：标题 + 统计行块quote ──
h1 = next((l[2:].strip() for l in lines if l.startswith('# ')), f'GitHub Trending 月报 {month}')
bq = next((l[2:].strip() for l in lines if l.startswith('> 统计周期')), '')
def grab(pat, default=''):
    mm = re.search(pat, bq)
    return mm.group(1) if mm else default
p_start = grab(r'统计周期：([\d-]+) ~ ([\d-]+)', '')
mm = re.search(r'统计周期：([\d-]+) ~ ([\d-]+)', bq)
p1, p2 = (mm.group(1), mm.group(2)) if mm else (f'{month}-01', f'{month}-31')
n_projects = grab(r'共收录 \*\*(\d+)\*\* 个项目', '0')
n_records = grab(r'（(\d+) 条上榜记录）', '0')
total_stars = grab(r'月度新增 \*\*([\d,]+)\*\*', '0')
y, m = month.split('-')
mm_label = f'{y}年{int(m)}月'

# ── 一、本月格局（环比表 + 三个结构性变化）──
narratives = []
mom_rows, mom_header = [], []
sec = find_h2('本月格局')
if sec >= 0:
    end = sec + 1
    while end < len(lines) and not lines[end].startswith('## ') and lines[end] != '---':
        end += 1
    _, mom_rows, _ = parse_table(sec + 1)
    hdr_idx = next((i for i in range(sec, end) if lines[i].strip().startswith('| 指标')), None)
    if hdr_idx is not None:
        mom_header, _, _ = parse_table(hdr_idx)
    for i in range(sec, end):
        if re.match(r'^\d+\.\s+\*\*', lines[i]):
            mm2 = re.match(r'^\d+\.\s+\*\*(.+?)\*\*(.*)$', lines[i])
            if not mm2:
                continue
            lead, body = mm2.group(1), mm2.group(2)
            body = body.lstrip('：: ').strip()
            # 贪心拼句，最多 95 字
            sents = [s for s in body.split('。') if s]
            acc = ''
            for s in sents:
                cand = (acc + '。' + s).strip('。') if acc else s
                if len(cand) > 95:
                    break
                acc = cand
            if not acc:
                acc = body[:95]
            if len(acc) > 95:  # 兜底按逗号切
                cut = max((acc.rfind(c, 0, 93) for c in '，；、'), default=-1)
                acc = (acc[:cut] + '…') if cut > 20 else acc[:95] + '…'
            narratives.append((lead, acc))
mom_pct = ''
for r in mom_rows:
    if '月度新增总星数' in r[0]:
        mm3 = re.search(r'([+-][\d.]+%)', r[3] if len(r) > 3 else '')
        if mm3:
            mom_pct = mm3.group(1)

# ── 二、TOP10 ──
top10 = []
sec = find_h2('Top 20')
if sec >= 0:
    _, rows, _ = parse_table(sec + 1)
    for r in rows[:10]:
        if len(r) >= 7:
            top10.append({
                'rank': r[0], 'name': r[1].replace('**', ''),
                'new': r[2].replace('+', ''), 'total': r[3],
                'lang': r[4], 'days': r[5], 'best': r[6],
            })

# ── 三、三大王冠 ──
crowns = []
sec = find_h2('三大王冠')
if sec >= 0:
    end = sec + 1
    while end < len(lines) and not lines[end].startswith('## '):
        end += 1
    for title, row, _ in h3_blocks(sec, end):
        if not row:
            continue
        name = row[0].replace('**', '')
        if '持久' in title:
            key = f'全月 {row[1]} · 连续 {row[2]}'
            right, sub = row[3], row[4] if len(row) > 4 else ''
        elif '单日' in title or '爆发' in title:
            key = f'{row[2]} 单日 +{row[1]}'
            right, sub = '', row[3] if len(row) > 3 else ''
        elif '新秀' in title:
            key = f'{row[1]}★ · {row[2]}'
            right, sub = '', row[3] if len(row) > 3 else ''
        else:
            key, right, sub = ' · '.join(row[1:3]), '', row[3] if len(row) > 3 else ''
        tag = re.sub(r'^[^\w]*', '', title.split('—')[0]).strip()  # 去 emoji
        crowns.append((tag, name, key, right, sub))

# ── 四、关键指标环比（格局表）/ 回退「关键指标一览」──
grid_header, grid_rows = [], []
if mom_rows and mom_header:
    grid_header, grid_rows = mom_header, mom_rows
else:
    sec = find_h2('关键指标一览')
    if sec >= 0:
        h, rows, _ = parse_table(sec + 1)
        grid_header, grid_rows = h or ['指标', '数值'], rows

# ── 领域着色（口径 = 条形图 / 领域热度表）──
COLORS = {
    'agent-skills': '#2E8B57', 'ai-video-audio': '#E4572E',
    'code-visualization': '#4C72B0', 'web-infra': '#8172B2',
    'open-source-alt': '#DD8452', 'education': '#D9A404',
    'ai-quality': '#8C6E58', 'other': '#9AA0B5',
}
LABELS = {
    'agent-skills': 'Agent/Skills', 'ai-video-audio': 'AI 视频/音频',
    'code-visualization': '代码可视化', 'web-infra': 'Web 抓取',
    'open-source-alt': '开源替代', 'education': '教育/学习',
    'ai-quality': 'AI 质量', 'other': '其他',
}
# 描述缓存：正文 Top 表没有 description，直接查 DB
import sqlite3
db = sqlite3.connect(f'{REPO}/data/github_trending.db')
def domain(name):
    row = db.execute(
        "SELECT description FROM trending_daily WHERE repo_full_name=? AND date LIKE ?||'%' "
        "ORDER BY date DESC LIMIT 1", (name, month)).fetchone()
    cs = classify_category(name, row[0] if row else '')
    return cs[0] if cs else 'other'

# ══ HTML ══
C = {'blue': '#4C72B0', 'orange': '#E4572E', 'purple': '#8172B2'}
NCOL = [C['blue'], C['orange'], C['purple']]

sec_no = 0
def sec_title(txt):
    global sec_no
    sec_no += 1
    return f'<div class="sec"><span class="no">{"一二三四"[sec_no-1]}</span>{esc(txt)}</div>'

narr_html = ''
if narratives:
    for i, (lead, body) in enumerate(narratives[:3]):
        c = NCOL[i % 3]
        narr_html += f'''<div class="narr"><div class="spine" style="background:{c}"></div>
  <div class="body"><div class="ttl" style="background:{c}18;color:{c}">{esc(lead)}</div><p>{mdhtml(body)}</p></div>
</div>'''

top_html = ''
for i, r in enumerate(top10):
    d = domain(r['name'])
    c = COLORS[d]
    sub = [r['lang'], f"上榜 {r['days']}", f"最佳 #{r['best']}", f"总星 {r['total']}★"]
    sub_html = ' · '.join(s for s in sub if s)
    top_html += f'''<div class="row"><div class="idx">{i+1:02d}</div>
  <div class="main"><div class="l1"><span class="name">{esc(r['name'])}</span>
    <span class="tag" style="background:{c}">{LABELS[d]}</span></div>
    <div class="sub">{esc(sub_html)}</div></div>
  <div class="stars"><div class="wk" style="color:{c}">+{esc(r['new'])}<span style="font-size:15px">★</span></div></div>
</div>'''

crown_html = ''
for i, (tag, name, key, right, sub) in enumerate(crowns[:3]):
    c = NCOL[i % 3]
    right_s = f'<br><b style="color:{c}">{esc(right)}</b>' if right else ''
    crown_html += f'''<div class="knife"><span class="tag" style="background:{c}">{esc(tag)}</span>
  <h3>{esc(name)}</h3><p><b>{esc(key)}</b>{right_s}<br>{mdhtml(sub)}</p></div>'''

grid_html = ''
if grid_rows:
    gh = grid_header if len(grid_header) >= 4 else ['指标', '当月', '上月', '环比']
    head_cells = ''.join(f'<th>{esc(h)}</th>' for h in gh[:4])
    body_cells = ''
    for r in grid_rows:
        cells = (r + ['', '', '', ''])[:4]
        body_cells += '<tr>' + ''.join(f'<td>{mdhtml(c)}</td>' for c in cells) + '</tr>'
    grid_html = f'''<div class="gridwrap"><table class="kv">
<thead><tr>{head_cells}</tr></thead><tbody>{body_cells}</tbody></table></div>'''

meta_bits = [f'{p1} ~ {p2}', f'{n_projects} 个项目', f'{n_records} 条记录']
if mom_pct:
    meta_bits.append(f'环比 {mom_pct}')
meta = ' ｜ '.join(meta_bits)

toc = '本图结构 ｜ ' + ' · '.join(
    t for t, ok in [('本月格局', narratives), ('月度 TOP10', top10),
                    ('三大王冠', crowns), ('关键指标', grid_rows)] if ok)

HTML = f'''<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Noto Sans CJK SC','Noto Sans SC',sans-serif; background:#EEF0F4; width:1080px; }}
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
  .row .sub {{ font-size:14px; color:#9AA0B5; margin-top:2px; }}
  .row .stars {{ text-align:right; flex-shrink:0; padding-top:2px; }}
  .row .wk {{ font-size:22px; font-weight:900; }}
  .knives {{ display:flex; gap:20px; }}
  .knife {{ flex:1; background:#fff; border-radius:16px; padding:24px 24px 20px; box-shadow:0 2px 10px rgba(26,27,38,.05); }}
  .knife .tag {{ display:inline-block; font-size:14px; font-weight:700; color:#fff; padding:5px 16px; border-radius:20px; margin-bottom:14px; }}
  .knife h3 {{ font-size:19px; font-weight:700; color:#1A1B26; margin-bottom:10px; word-break:break-all; }}
  .knife p {{ font-size:15.5px; color:#4A4F66; line-height:1.6; }}
  .gridwrap {{ background:#fff; border-radius:16px; padding:10px 20px 16px; box-shadow:0 2px 10px rgba(26,27,38,.05); }}
  table.kv {{ width:100%; border-collapse:collapse; }}
  table.kv th {{ font-size:15px; color:#9AA0B5; font-weight:700; text-align:left; padding:14px 12px 10px; border-bottom:2px solid #E7E9EF; }}
  table.kv td {{ font-size:16px; color:#4A4F66; padding:11px 12px; border-bottom:1px solid #EFF1F5; }}
  table.kv tr:last-child td {{ border-bottom:none; }}
  table.kv td:first-child {{ color:#1A1B26; font-weight:500; }}
  .foot {{ background:#E7E9EF; padding:20px 0 22px; margin-top:36px; text-align:center; font-size:14px; color:#9AA0B5; }}
</style></head><body>
<div class="head">
  <div class="left"><h1>GitHub Trending 月报</h1><div class="bar"></div>
    <div class="meta">{esc(meta)}</div>
    <div class="toc">{esc(toc)}</div></div>
  <div class="right"><div class="num">{esc(total_stars)}★</div><div class="lbl">月度新增</div></div>
</div>
<div style="padding:0 36px;">
{sec_title('本月格局变了什么') if narratives else ''}{narr_html}
{sec_title(f'月度 TOP10（{mm_label} 按新增星排序）') if top_html else ''}{top_html}
{sec_title('三大王冠') if crown_html else ''}
{('<div class="knives">' + crown_html + '</div>') if crown_html else ''}
{sec_title('关键指标环比') if grid_html else ''}{grid_html}
</div>
<div class="foot">数据源：GitHub Trending ｜ 统计口径：月内日度新增 Star 累计 ｜ 完整榜单与项目链接见知识库原文</div>
</body></html>'''

wrap = f'/tmp/monthly_digest_{month}.html'
open(wrap, 'w', encoding='utf-8').write(HTML)
png = f'{REPO}/reports/monthly/monthly-{month}-digest.png'
subprocess.run(['chromium', '--headless=new', '--no-sandbox', '--disable-gpu',
                '--disable-dev-shm-usage', '--hide-scrollbars',
                '--force-device-scale-factor=2', '--window-size=1080,4400',
                f'--screenshot={png}.raw.png', wrap], check=True)
im = Image.open(f'{png}.raw.png')
a = np.asarray(im.convert('L'))
content_end = np.where((a < 235).any(axis=1))[0].max()
im.crop((0, 0, 2160, int(content_end) + 46)).save(png)
os.remove(f'{png}.raw.png')
print(f'saved: {png} | 2160x{int(content_end)+46}px')
print(f'narratives={len(narratives)} top10={len(top10)} crowns={len(crowns)} grid={len(grid_rows)} rows | {meta}')
