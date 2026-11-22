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
    # 口径（2026-11-22 起，与周报速览/复盘表一致）：Agent 工具链 / Agent 应用与协议 / 非 Agent 项目
    toolchain = {'backnotprop/plannotator','google-labs-code/stitch-skills',
                 'GoogleChrome/modern-web-guidance-src','alibaba/open-code-review',
                 'mvanhorn/last30days-skill','ChromeDevTools/chrome-devtools-mcp',
                 'tradermonty/claude-trading-skills','kajisho5/ffmpeg-skill',
                 'anthropics/skills','Nutlope/hallmark','jakubkrehel/skills',
                 'mattpocock/skills','obra/superpowers','pbakaus/impeccable',
                 'cloudflare/security-audit-skill','AgriciDaniel/claude-seo',
                 'Leonxlnx/taste-skill','multica-ai/andrej-karpathy-skills',
                 'addyosmani/agent-skills','Donchitos/Claude-Code-Game-Studios',
                 'vercel-labs/agent-browser','google/elephant-goldfish-model',
                 'anthropics/claude-quickstarts'}
    if name in toolchain:
        return 'Agent 工具链'
    app = {'ag-ui-protocol/ag-ui','meta/astryx','dream-num/univer',
           'milind-soni/OpenMausBot','shiyu-coder/Kronos','TauricResearch/TradingAgents',
           'AstrBotDevs/AstrBot','YuJunZhiXue/dsh-purge','ZhuLinsen/daily_stock_analysis'}
    if name in app:
        return 'Agent 应用与协议'
    return '非 Agent 项目'

colors = {'Agent 工具链': '#4C72B0', 'Agent 应用与协议': '#E4572E', '非 Agent 项目': '#8C8C8C'}
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
