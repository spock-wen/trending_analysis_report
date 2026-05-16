import re, os

WIKI = "/srv/www/github-trending-wiki"
today = "2026-05-17"
yesterday = "2026-05-16"

data = [
    (1, "tinyhumansai/openhuman", "Rust", 1271, 9679, "tinyhumansai-openhuman"),
    (2, "obra/superpowers", "Shell", 1648, 193299, "obra-superpowers"),
    (3, "K-Dense-AI/scientific-agent-skills", "Python", 646, 22705, "K-Dense-AI-scientific-agent-skills"),
    (4, "supertone-inc/supertonic", "Swift", 719, 6294, "supertone-inc-supertonic"),
    (5, "ruvnet/RuView", "Rust", 1859, 57787, "ruvnet-RuView"),
    (6, "influxdata/telegraf", "Go", 212, 17479, "influxdata-telegraf"),
    (7, "anthropics/skills", "Python", 689, 135502, "anthropics-skills"),
    (8, "czlonkowski/n8n-mcp", "TypeScript", 68, 20971, "czlonkowski-n8n-mcp"),
    (9, "NVIDIA-AI-Blueprints/video-search-and-summarization", "Python", 308, 1261, "NVIDIA-AI-Blueprints-video-search-and-summarization"),
    (10, "oven-sh/bun", "Rust", 448, 90705, "oven-sh-bun"),
    (11, "mattpocock/skills", "Shell", 3132, 85724, "mattpocock-skills"),
    (12, "joeseesun/qiaomu-anything-to-notebooklm", "Python", 438, 2907, "joeseesun-qiaomu-anything-to-notebooklm"),
]

for rank, repo, lang, stars_today, total_stars, slug in data:
    fpath = os.path.join(WIKI, "entities", f"{slug}.md")
    if not os.path.exists(fpath):
        print(f"MISSING: {fpath}")
        continue

    with open(fpath, "r") as f:
        content = f.read()

    # Update frontmatter fields
    content = content.replace(f"updated: {yesterday}", f"updated: {today}")
    content = content.replace("trending_count_daily: 1", "trending_count_daily: 2")
    content = content.replace("consecutive_days: 1", f"consecutive_days: 2")
    content = content.replace(f"last_trending: {yesterday}", f"last_trending: {today}")
    content = content.replace("confidence: low", "confidence: medium")

    # Update peak_rank if better
    old_peak_match = re.search(r"peak_rank: (\d+)", content)
    if old_peak_match:
        old_peak = int(old_peak_match.group(1))
        new_peak = min(old_peak, rank)
        content = content.replace(f"peak_rank: {old_peak}", f"peak_rank: {new_peak}")

    # Update total_stars
    old_stars_match = re.search(r"total_stars: (\d+)", content)
    if old_stars_match:
        old_stars = int(old_stars_match.group(1))
        content = content.replace(f"total_stars: {old_stars}", f"total_stars: {total_stars}")

    # Add today's row after the last date row in the trending table
    lines = content.split("\n")
    last_date_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("| 2026-05-"):
            last_date_idx = i
    if last_date_idx >= 0:
        new_row = f"| {today} | {rank} | +{stars_today:,} | {total_stars:,} |"
        lines.insert(last_date_idx + 1, new_row)
    content = "\n".join(lines)

    with open(fpath, "w") as f:
        f.write(content)
    print(f"Updated: {slug} (rank {rank}, +{stars_today}, total {total_stars})")

print("Done!")
