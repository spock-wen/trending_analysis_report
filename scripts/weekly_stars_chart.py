#!/usr/bin/env python3
"""Weekly bar chart: weekly stars by repo, colored by category."""
import sqlite3, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patheffects as pe

week_end = sys.argv[1] if len(sys.argv) > 1 else '2026-09-20'
week_start = sys.argv[2] if len(sys.argv) > 2 else '2026-09-14'
total = int(sys.argv[3]) if len(sys.argv) > 3 else 74805
pct = sys.argv[4] if len(sys.argv) > 4 else '-29.5%'

db = sqlite3.connect('/srv/www/github-trending-wiki/data/github_trending.db')
rows = db.execute("SELECT repo_full_name, weekly_stars FROM weekly_trending WHERE week_end=? ORDER BY weekly_stars DESC", (week_end,)).fetchall()

def cat(name):
    big_vendors = {'alibaba/open-code-review','Tencent/WeKnora','anthropics/claude-code','anthropics/knowledge-work-plugins','openai/plugins','supabase/supabase'}
    if name in big_vendors:
        return '大厂官方/产品级开源'
    skills = {'affaan-m/ECC','ayghri/i-have-adhd','blader/humanizer','heygen-com/hyperframes','mksglu/context-mode','addyosmani/agent-skills','Panniantong/Agent-Reach','stablyai/orca','max-sixty/worktrunk','kunchenguid/firstmate','danny-avila/LibreChat','microsoft/markitdown'}
    if name in skills:
        return 'Skill/Agent 工作流'
    return '独立应用/其他'

colors = {'Skill/Agent 工作流': '#4C72B0', '大厂官方/产品级开源': '#E4572E', '独立应用/其他': '#2E8B57'}
names = [r[0] for r in rows][::-1]
stars = [r[1] for r in rows][::-1]
cats = [cat(r[0]) for r in rows][::-1]

fm.fontManager.addfont('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc')
plt.rcParams['font.family'] = 'WenQuanYi Micro Hei'

fig, ax = plt.subplots(figsize=(10.8, 12), dpi=200)
ax.barh(range(len(names)), stars, color=[colors[c] for c in cats], height=0.72)
ax.set_yticks(range(len(names)))
ax.set_yticklabels(names, fontsize=11)
for i, s in enumerate(stars):
    ax.text(s + 150, i, f'+{s:,}', va='center', fontsize=10,
            path_effects=[pe.withStroke(linewidth=2, foreground='white')])
ax.set_xlim(0, max(stars) * 1.15)
ax.set_xlabel('本周新增 Star', fontsize=11)
ax.set_title(f'GitHub Trending 周榜 · {week_start} ~ {week_end}\n{len(rows)} 个项目 · {total:,}★ · 环比 {pct}',
             fontsize=14, fontweight='bold', pad=14)
handles = [plt.Rectangle((0, 0), 1, 1, color=colors[k]) for k in colors]
ax.legend(handles, list(colors), fontsize=10, loc='lower right')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
out = '/srv/www/github-trending-wiki/reports/weekly/weekly-%s-stars.png' % week_end
plt.savefig(out, dpi=200, bbox_inches='tight')
print('saved', out)

from collections import defaultdict
agg, cnt = defaultdict(int), defaultdict(int)
for r in rows:
    agg[cat(r[0])] += r[1]; cnt[cat(r[0])] += 1
for k in agg:
    print(k, cnt[k], '项', agg[k], '★')
print('sum:', sum(agg.values()), 'expected:', total, 'match:', sum(agg.values()) == total)
