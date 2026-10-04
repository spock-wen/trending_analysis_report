#!/usr/bin/env python3
"""
只为缺失的 repo 生成 entity 页面，绝不全量重写。

为什么不用 wiki_daily.py 的 generate_entities()：
  那个函数会遍历所有 repo_stats 并无条件覆写 entity 文件，会冲掉人工编辑
  （例如 juliusbrussee-caveman 的 first_language/language_shifted 字段）。

本脚本：
  - 只对 entities/ 下不存在的 repo 建档
  - 复用 wiki_daily 的 detect_domains / tag 逻辑，保持一致
  - 回填数据标 source_backfill: true + rank_inferred: true
  - 已有 entity 一律不动

用法： python3 generate_entities_for_new.py [--dry-run]
"""
import os
import sys
import sqlite3
import argparse
from collections import defaultdict

BASE = '/srv/www/github-trending-wiki'
ENTITIES_DIR = f'{BASE}/entities'
CONCEPTS_DIR = f'{BASE}/concepts'
DB_PATH = f'{BASE}/data/github_trending.db'

sys.path.insert(0, f'{BASE}/scripts')
from wiki_daily import detect_domains  # noqa: E402


def slug_of(repo):
    return repo.replace('/', '-').lower()


def main(dry_run):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    repos = [dict(r) for r in conn.execute('SELECT * FROM repo_stats ORDER BY last_seen DESC')]

    # 每个 repo 的上榜历史
    history = defaultdict(list)
    for row in conn.execute('SELECT repo_full_name, date, rank, stars_today FROM trending_daily ORDER BY date DESC'):
        history[row[0]].append({'date': row[1], 'rank': row[2], 'stars': row[3]})

    # 领域/语言分组（供自动关联）
    repo_domains = {}
    domain_map = defaultdict(list)
    lang_map = defaultdict(list)
    for r in repos:
        d = detect_domains(r['repo_full_name'], r.get('description') or '', r.get('language') or '')
        repo_domains[r['repo_full_name']] = d
        for x in d:
            domain_map[x].append(r['repo_full_name'])
        lang_map[r.get('language') or '其他'].append(r['repo_full_name'])

    missing = [r for r in repos if not os.path.exists(f"{ENTITIES_DIR}/{slug_of(r['repo_full_name'])}.md")]
    print(f"repo_stats 共 {len(repos)} 个，缺少 entity 的 {len(missing)} 个")

    os.makedirs(ENTITIES_DIR, exist_ok=True)
    created = 0
    for r in missing:
        repo = r['repo_full_name']
        slug = slug_of(repo)
        path = f'{ENTITIES_DIR}/{slug}.md'
        is_backfill = (r.get('first_seen') or '') < '2026-05-16'

        count = r.get('trending_count_daily', 1) or 1
        confidence = 'high' if count >= 3 else ('medium' if count >= 2 else 'low')

        lang = r.get('language') or ''
        lang_lower = lang.lower()
        lang_tag_map = {
            'python': 'python', 'rust': 'rust', 'typescript': 'typescript',
            'go': 'go', 'java': 'java', 'c++': 'cpp', 'shell': 'shell',
            'jupyter notebook': 'python',
        }
        tags = []
        if lang_lower in lang_tag_map:
            tags.append(lang_tag_map[lang_lower])
        tags.extend(repo_domains.get(repo, []))
        if (r.get('consecutive_days') or 0) >= 3:
            tags.append('rising')
        if not tags:
            tags.append('tool')
        seen, uniq = set(), []
        for t in tags:
            if t not in seen:
                seen.add(t)
                uniq.append(t)
        tags = uniq

        desc = (r.get('description') or '').lower()
        if any(w in desc for w in ['tutorial', 'beginner', 'course']):
            ptype = 'tutorial'
        elif any(w in desc for w in ['framework', 'sdk', 'engine']):
            ptype = 'framework'
        else:
            ptype = 'tool'

        hist_lines = []
        for h in history.get(repo, [])[:5]:
            hist_lines.append(f"  - {h['date']}: #{h['rank']}, +{h['stars']}⭐")

        related = set()
        for other in lang_map.get(lang or '其他', [])[:4]:
            if other != repo:
                related.add(other)
        for d in repo_domains.get(repo, []):
            for other in domain_map.get(d, [])[:4]:
                if other != repo:
                    related.add(other)
        related_links = [f'[[{slug_of(x)}]]' for x in list(related)[:5]]

        concept_links = []
        for d in repo_domains.get(repo, []):
            if os.path.exists(f'{CONCEPTS_DIR}/{d}.md'):
                concept_links.append(f'[[{d}]]')

        if related_links and concept_links:
            all_related = f"{' '.join(related_links)}\n\n**所属领域**: {' '.join(concept_links)}"
        elif concept_links:
            all_related = f"**所属领域**: {' '.join(concept_links)}"
        elif related_links:
            all_related = ' '.join(related_links)
        else:
            all_related = '- 暂无'

        # 回填来源标注：sources 指向不存在本地 raw 的历史日期，必须说明
        backfill_note = ''
        if is_backfill:
            backfill_note = (
                f"\nsource_backfill: true"
                f"\nrank_inferred: true"
                f"\nbackfill_source: daily-report"
            )

        fm = f"""---
title: "{repo}"
created: {r.get('first_seen', '')}
updated: {r.get('last_seen', '')}
last_active: {r.get('last_seen', '')}
type: {ptype}
tags: [{', '.join(tags)}]
sources: [raw/trending/{r.get('last_seen', '')}.json]
confidence: {confidence}
trending_count_daily: {count}
trending_count_weekly: {r.get('trending_count_weekly', 0) or 0}
trending_count_monthly: {r.get('trending_count_monthly', 0) or 0}
consecutive_days: {r.get('consecutive_days', 0) or 0}
first_trending: {r.get('first_seen', '')}
last_trending: {r.get('last_seen', '')}
peak_rank: {r.get('peak_rank', 0) or 0}
total_stars: {r.get('last_stars', 0) or 0}
language: "{lang}"{backfill_note}
---"""

        body = f"""# {repo}

{r.get('description') or 'No description'}

- 语言: {lang if lang else '未标注'}
- 上榜次数: {count} 次
- 连续上榜: {r.get('consecutive_days', 0) or 0} 天
- 最高排名: #{r.get('peak_rank', '?') or '?'}
- 链接: [{repo}](https://github.com/{repo})

## 上榜历史

{chr(10).join(hist_lines) if hist_lines else '- 首次上榜'}

## 相关项目

{all_related}
"""
        if dry_run:
            if created < 3:
                print(f"\n--- [DRY-RUN] {slug} ---\n{fm}\n")
        else:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"{fm}\n\n{body}")
        created += 1

    conn.close()
    verb = '将新建' if dry_run else '已新建'
    print(f"{verb} entity: {created} 个")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    main(a.dry_run)
