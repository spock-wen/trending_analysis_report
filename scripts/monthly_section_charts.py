#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""月报章节配图（3 张，均从 monthly-YYYY-MM.md 正文或 DB 读数）
用法：python3 monthly_section_charts.py 2026-09
输出：
  monthly-YYYY-MM-lang.png     语言分布：9月 vs 8月 新增星对比（锚「语言分布变化」末尾）
  monthly-YYYY-MM-domain.png   领域热度：9月 vs 8月 记录数对比（锚「领域热度趋势」末尾）
  monthly-YYYY-MM-rhythm.png   日度新增 Star 走势（锚月内节奏洞察末尾）
口径：lang/domain 直接解析正文表格（与已发布数字零偏差）；rhythm 从 trending_daily 聚合。
缺失的章节自动跳过（旧月份模板不同）。
"""
import re, sys, sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patheffects as pe

REPO = '/srv/www/github-trending-wiki'
month = sys.argv[1] if len(sys.argv) > 1 else '2026-09'
y, m = month.split('-')
lines = open(f'{REPO}/reports/monthly/monthly-{month}.md', encoding='utf-8').read().split('\n')

fm.fontManager.addfont('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc')
plt.rcParams['font.family'] = 'WenQuanYi Micro Hei'
plt.rcParams['axes.unicode_minus'] = False

def find_h2(key):
    for i, l in enumerate(lines):
        if l.startswith('## ') and key in l:
            return i
    return -1

def parse_table(start):
    i = start
    while i < len(lines) and not lines[i].strip():
        i += 1
    header, rows = None, []
    while i < len(lines) and lines[i].strip().startswith('|'):
        cells = [c.strip().replace('**', '') for c in lines[i].strip().strip('|').split('|')]
        if set(''.join(cells)) <= set('-: '):
            pass
        elif header is None:
            header = cells
        else:
            rows.append(cells)
        i += 1
    return header, rows

UP, DOWN = '#C2331F', '#2E8B57'   # 涨红跌绿（国内读图习惯）

# ── 图 1：语言分布 9月 vs 8月 新增星 ──
sec = find_h2('语言分布')
if sec >= 0:
    _, rows = parse_table(sec + 1)
    data = []  # (lang, s9, s8, change_text)
    for r in rows:
        if len(r) >= 7:
            data.append((r[0], int(r[4].replace(',', '')), int(r[5].replace(',', '')), r[6]))
    data.sort(key=lambda x: -x[1])
    langs = [d[0] for d in data]
    s9 = [d[1] for d in data]
    s8 = [d[2] for d in data]
    chg = [d[3] for d in data]

    fig, ax = plt.subplots(figsize=(10.8, 7.2), dpi=200)
    idx = range(len(langs))
    ax.barh([i + 0.19 for i in idx], s9, height=0.36, color='#4C72B0', label=f'{int(m)}月')
    ax.barh([i - 0.19 for i in idx], s8, height=0.36, color='#C3C8D4', label=f'{int(m)-1}月')
    for i, (a, b, c) in enumerate(zip(s9, s8, chg)):
        mx = max(a, b)
        col = UP if ('↑' in c or '+' in c) else (DOWN if '↓' in c else '#4A4F66')
        ax.text(mx * 1.02, i + 0.19, f'{a:,}', va='center', fontsize=9.5, color='#4C72B0',
                path_effects=[pe.withStroke(linewidth=2, foreground='white')])
        ax.text(mx * 1.02, i - 0.19, f'{b:,}', va='center', fontsize=9, color='#8A90A5',
                path_effects=[pe.withStroke(linewidth=2, foreground='white')])
        ax.text(mx * 1.30, i, c, va='center', fontsize=10.5, fontweight='bold', color=col)
    ax.set_yticks(list(idx))
    ax.set_yticklabels(langs, fontsize=12)
    ax.invert_yaxis()
    ax.set_xlim(0, max(max(s9), max(s8)) * 1.52)
    ax.set_xlabel('月度新增 Star', fontsize=11)
    ax.set_title(f'语言分布 9月 vs 8月 ｜ GitHub Trending 月报 Top {len(langs)}（右侧 = 星数环比）',
                 fontsize=13.5, fontweight='bold', pad=14)
    ax.legend(fontsize=10, loc='lower right')
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.grid(axis='x', alpha=.25)
    plt.tight_layout()
    out = f'{REPO}/reports/monthly/monthly-{month}-lang.png'
    plt.savefig(out, dpi=200, bbox_inches='tight'); plt.close()
    print('saved:', out, '| langs:', len(langs))
else:
    print('SKIP lang（正文无语言分布章节）')

# ── 图 2：领域热度 9月 vs 8月 记录数 ──
DC = [('Agent', '#2E8B57'), ('教育', '#D9A404'), ('AI 视频', '#E4572E'),
      ('代码可视化', '#4C72B0'), ('开源替代', '#DD8452'), ('AI 质量', '#8C6E58'),
      ('Web', '#8172B2'), ('其他', '#9AA0B5')]
def dcolor(name):
    for kw, c in DC:
        if kw in name:
            return c
    return '#9AA0B5'

sec = find_h2('领域热度')
if sec >= 0:
    _, rows = parse_table(sec + 1)
    data = []  # (领域, n9, n8, 趋势text)
    for r in rows:
        if len(r) >= 6:
            data.append((r[0], int(re.sub(r'\D', '', r[1])), int(re.sub(r'\D', '', r[3])), r[5]))
    data.sort(key=lambda x: -x[1])
    names = [d[0].replace(' / ', '/') for d in data]
    n9 = [d[1] for d in data]
    n8 = [d[2] for d in data]
    tr = [d[3] for d in data]

    fig, ax = plt.subplots(figsize=(10.8, 7.2), dpi=200)
    idx = range(len(names))
    for i, (a, b) in enumerate(zip(n9, n8)):
        c = dcolor(data[i][0])
        ax.barh(i + 0.19, a, height=0.36, color=c)
        ax.barh(i - 0.19, b, height=0.36, color='#C3C8D4')
        mx = max(a, b)
        ax.text(mx * 1.02, i + 0.19, str(a), va='center', fontsize=9.5, color=c,
                path_effects=[pe.withStroke(linewidth=2, foreground='white')])
        ax.text(mx * 1.02, i - 0.19, str(b), va='center', fontsize=9, color='#8A90A5',
                path_effects=[pe.withStroke(linewidth=2, foreground='white')])
        col = UP if tr[i].startswith('↑') else (DOWN if tr[i].startswith('↓') else '#4A4F66')
        ax.text(mx * 1.34, i, tr[i], va='center', fontsize=10, fontweight='bold', color=col)
    ax.set_yticks(list(idx))
    ax.set_yticklabels(names, fontsize=12)
    ax.invert_yaxis()
    ax.set_xlim(0, max(max(n9), max(n8)) * 1.75)
    ax.set_xlabel('当月上榜记录数（关键词可多重归类）', fontsize=11)
    ax.set_title(f'领域热度 9月 vs 8月 ｜ GitHub Trending 月报（右侧 = 记录数趋势）',
                 fontsize=13.5, fontweight='bold', pad=14)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color='#2E8B57'), Patch(color='#C3C8D4')],
              labels=[f'{int(m)}月（按领域着色）', f'{int(m)-1}月'], fontsize=10, loc='lower right')
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.grid(axis='x', alpha=.25)
    plt.tight_layout()
    out = f'{REPO}/reports/monthly/monthly-{month}-domain.png'
    plt.savefig(out, dpi=200, bbox_inches='tight'); plt.close()
    print('saved:', out, '| domains:', len(names))
else:
    print('SKIP domain（正文无领域热度章节）')

# ── 图 3：日度新增 Star 走势（DB 聚合）──
db = sqlite3.connect(f'{REPO}/data/github_trending.db')
daily = db.execute(
    "SELECT date, SUM(stars_today) FROM trending_daily WHERE date LIKE ?||'%' AND period='daily' "
    "GROUP BY date ORDER BY date", (month,)).fetchall()
if daily:
    ds = [d[0][5:] for d in daily]
    vs = [d[1] for d in daily]
    mean = sum(vs) / len(vs)
    imax, imin = vs.index(max(vs)), vs.index(min(vs))
    fig, ax = plt.subplots(figsize=(10.8, 5.4), dpi=200)
    ax.fill_between(range(len(vs)), vs, alpha=.18, color='#4C72B0')
    ax.plot(range(len(vs)), vs, color='#4C72B0', linewidth=2.4, marker='o', ms=4)
    ax.axhline(mean, color='#E4572E', linewidth=1.4, linestyle='--', alpha=.85)
    ax.text(len(vs) - 1, mean, f' 均值 {mean:,.0f}★/天', color='#E4572E',
            fontsize=10, va='bottom', ha='right', fontweight='bold')
    for i, lab in [(imax, f'峰值 {vs[imax]:,}★（{ds[imax]}）'), (imin, f'低谷 {vs[imin]:,}★（{ds[imin]}）')]:
        dy = 16 if i == imax else -22
        ax.annotate(lab, (i, vs[i]), textcoords='offset points', xytext=(0, dy),
                    ha='center', fontsize=10, fontweight='bold',
                    color=UP if i == imax else DOWN,
                    path_effects=[pe.withStroke(linewidth=2.5, foreground='white')])
    step = 2 if len(ds) <= 31 else 5
    ax.set_xticks(range(0, len(ds), step))
    ax.set_xticklabels([ds[i] for i in range(0, len(ds), step)], fontsize=10)
    ax.set_ylabel('每日新增 Star', fontsize=11)
    ax.set_title(f'{y}年{int(m)}月日度新增 Star 走势 ｜ 全月 {sum(vs):,}★ · {len(vs)} 天',
                 fontsize=13.5, fontweight='bold', pad=14)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=.25)
    plt.tight_layout()
    out = f'{REPO}/reports/monthly/monthly-{month}-rhythm.png'
    plt.savefig(out, dpi=200, bbox_inches='tight'); plt.close()
    print(f'saved: {out} | total={sum(vs):,} days={len(vs)} mean={mean:,.0f} max={vs[imax]:,}@{ds[imax]} min={vs[imin]:,}@{ds[imin]}')
else:
    print('SKIP rhythm（DB 无该月数据）')
