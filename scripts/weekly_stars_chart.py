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
    # 口径（2026-10-25 起，与周报速览/复盘表一致）：五赛道
    skill = {'morluto/rea','cloudflare/security-audit-skill','anthropics/claude-plugins-official',
             'anthropics/knowledge-work-plugins','cursor/plugins','android/skills',
             'mattpocock/skills','cathrynlavery/diagram-design','alirezarezvani/claude-skills',
             'addyosmani/agent-skills','pbakaus/impeccable','davila7/claude-code-templates',
             'affaan-m/ECC','Nutlope/hallmark','SnailSploit/Claude-Red','luongnv89/claude-howto'}
    if name in skill:
        return 'Skill/插件生态'
    orch = {'stablyai/orca','anomalyco/opencode','ruvnet/ruflo','HKUDS/CLI-Anything',
            'paperclipai/paperclip','vectorize-io/hindsight','dream-num/univer','superdesigndev/treg',
            'Panniantong/Agent-Reach','pingdotgg/t3code','mvschwarz/openrig',
            'msitarzewski/agency-agents','aws/agent-toolkit-for-aws'}
    if name in orch:
        return 'Agent 编排与运行时'
    ctx = {'Graphify-Labs/graphify','akitaonrails/ai-memory','ranxianglei/billion-context',
           'mksglu/context-mode','headroomlabs-ai/headroom'}
    if name in ctx:
        return '上下文与记忆'
    content = {'heygen-com/hyperframes','Comfy-Org/ComfyUI','storytold/artcraft',
               'debpalash/VoiceStudio','harry0703/MoneyPrinterTurbo','Kruk2/jasna','OpenBMB/VoxCPM'}
    if name in content:
        return 'AI 内容创作'
    infer = {'vllm-project/vllm','pytorch/pytorch','huggingface/transformers','tile-ai/tilelang'}
    if name in infer:
        return '推理基础设施'
    return '独立应用/硬件'

colors = {'Skill/插件生态': '#4C72B0', 'Agent 编排与运行时': '#E4572E', '上下文与记忆': '#2E8B57',
          'AI 内容创作': '#8172B2', '推理基础设施': '#C4A35A', '独立应用/硬件': '#8C8C8C'}
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
