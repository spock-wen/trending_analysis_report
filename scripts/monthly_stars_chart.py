#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""月报 Top 15 横向条形图（条 = 本月增量，右侧 = 总星）
用法：python3 monthly_stars_chart.py 2026-09
输出：reports/monthly/monthly-2026-09-stars.png（dpi 200）
着色口径：daily_signals CATEGORY_RULES 关键词归类，与月报「领域热度趋势」表一致
"""
import sqlite3, sys, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patheffects as pe

REPO = '/srv/www/github-trending-wiki'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from daily_signals import classify_category

month = sys.argv[1] if len(sys.argv) > 1 else '2026-09'
y, m = month.split('-')

db = sqlite3.connect(f'{REPO}/data/github_trending.db')
rows = db.execute("""
    SELECT repo_full_name, language, description,
           SUM(stars_today) AS mstars,
           (SELECT total_stars FROM trending_daily d2
             WHERE d2.repo_full_name = d.repo_full_name
               AND d2.date LIKE ? || '%' AND d2.period = 'daily'
             ORDER BY d2.date DESC LIMIT 1) AS total_stars
    FROM trending_daily d
    WHERE date LIKE ? || '%' AND period = 'daily'
    GROUP BY repo_full_name
    ORDER BY mstars DESC
    LIMIT 15
""", (month, month)).fetchall()

# 月度全量核对（应与月报正文一致）
tot, n_proj, n_rec = db.execute(
    "SELECT SUM(stars_today), COUNT(DISTINCT repo_full_name), COUNT(*) "
    "FROM trending_daily WHERE date LIKE ? || '%'", (month,)).fetchone()
assert sum(r[3] for r in rows) <= tot, 'top15 sum > month total?!'

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

def cat_of(name, desc):
    cs = classify_category(name, desc)
    return cs[0] if cs else 'other'

items = []  # top-first
for name, lang, desc, mstars, total in rows:
    c = cat_of(name, desc)
    items.append((name, lang or '', mstars, total or 0, c))

names = [f'{it[0]} ({it[1]})' if it[1] else it[0] for it in items][::-1]
stars = [it[2] for it in items][::-1]
totals = [it[3] for it in items][::-1]
cats = [it[4] for it in items][::-1]

fm.fontManager.addfont('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc')
plt.rcParams['font.family'] = 'WenQuanYi Micro Hei'

fig, ax = plt.subplots(figsize=(10.8, 13.2), dpi=200)
ax.barh(range(len(names)), stars, color=[COLORS[c] for c in cats], height=0.72)
ax.set_yticks(range(len(names)))
ax.set_yticklabels(names, fontsize=11)
# names 已 [::-1]（榜首在末位），默认朝向即榜首在最上，勿再 invert

smax = max(stars)
for i, (s, t) in enumerate(zip(stars, totals)):
    if s > smax * 0.10:
        ax.text(s * 0.98, i, f'+{s:,}', va='center', ha='right',
                fontsize=10, fontweight='bold', color='white')
    else:
        ax.text(s + smax * 0.01, i, f'+{s:,}', va='center', ha='left', fontsize=10,
                path_effects=[pe.withStroke(linewidth=2, foreground='white')])
    if t:
        ax.text(s + smax * 0.035, i, f'{t:,}★', va='center', ha='left', fontsize=9.5,
                color='#4A4F66', path_effects=[pe.withStroke(linewidth=2, foreground='white')])

ax.set_xlim(0, smax * 1.28)
ax.set_xlabel('本月新增 Star', fontsize=11)
ax.set_title(f'GitHub Trending 月报 Top 15 | {y}年{int(m)}月（条 = 本月增量，右侧 = 总星）',
             fontsize=14, fontweight='bold', pad=14)

present = []
for c in cats:  # 保序去重（按出现频次靠前的排前）
    if c not in present:
        present.append(c)
present.sort(key=lambda c: -cats.count(c))
handles = [plt.Rectangle((0, 0), 1, 1, color=COLORS[c]) for c in present]
ax.legend(handles, [LABELS[c] for c in present], fontsize=10, loc='lower right')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()

out = f'{REPO}/reports/monthly/monthly-{month}-stars.png'
plt.savefig(out, dpi=200, bbox_inches='tight')
print(f'saved: {out}')
print(f'month check: total={tot:,} projects={n_proj} records={n_rec} | top15={sum(stars):,}')
for c in present:
    cs = sum(it[2] for it in items if it[4] == c)
    print(f'  {LABELS[c]}: {sum(1 for it in items if it[4] == c)} 项 {cs:,}★')
