#!/usr/bin/env python3
"""
GitHub Trending Wiki 查询工具
从 SQLite 数据库和 wiki 页面中查询项目。

用法：
  python3 wiki_query.py --lang rust                    # 按语言查询
  python3 wiki_query.py --tag ai-agent                 # 按标签查询
  python3 wiki_query.py --keyword trading               # 按关键词搜索
  python3 wiki_query.py --rising                        # 查询连续上榜项目
  python3 wiki_query.py --top 10 --sort stars           # 按 star 排序 Top N
  python3 wiki_query.py --stats                         # 输出整体统计
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime

WIKI_PATH = os.environ.get("GITHUB_TRENDING_WIKI_PATH", "/srv/www/github-trending-wiki")
DB_PATH = os.path.join(WIKI_PATH, "data", "github_trending.db")
ENTITIES_DIR = os.path.join(WIKI_PATH, "entities")


def get_db():
    if not os.path.exists(DB_PATH):
        print(f"数据库不存在: {DB_PATH}", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query_by_language(lang, sort='stars', limit=20):
    """按语言查询项目"""
    conn = get_db()
    order = "last_stars DESC" if sort == 'stars' else "trending_count_daily DESC"
    rows = conn.execute(f"""
        SELECT repo_full_name, description, language, last_stars,
               trending_count_daily, consecutive_days, first_seen, last_seen
        FROM repo_stats
        WHERE language LIKE ?
        ORDER BY {order}
        LIMIT ?
    """, (f"%{lang}%", limit)).fetchall()
    conn.close()
    return rows


def query_by_tag(tag, limit=20):
    """按标签查询（扫描 entity 页面的 frontmatter）"""
    results = []
    if not os.path.isdir(ENTITIES_DIR):
        return results
    for fname in os.listdir(ENTITIES_DIR):
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(ENTITIES_DIR, fname)
        content = open(fpath, encoding='utf-8').read()
        if not content.startswith('---'):
            continue
        end = content.find('---', 3)
        if end == -1:
            continue
        fm_text = content[3:end]
        if f"'{tag}'" in fm_text or f'"{tag}"' in fm_text or f" {tag}" in fm_text:
            # 提取基本信息
            title_match = re.search(r'title:\s*(.+)', fm_text)
            stars_match = re.search(r'total_stars:\s*(\d+)', fm_text)
            lang_match = re.search(r'language:\s*(.+)', fm_text)
            results.append({
                'file': fname,
                'title': title_match.group(1).strip().strip('"') if title_match else fname,
                'stars': int(stars_match.group(1)) if stars_match else 0,
                'language': lang_match.group(1).strip() if lang_match else ''
            })
    results.sort(key=lambda x: x['stars'], reverse=True)
    return results[:limit]


def query_by_keyword(keyword, limit=20):
    """按关键词搜索 description"""
    conn = get_db()
    rows = conn.execute("""
        SELECT repo_full_name, description, language, last_stars,
               trending_count_daily, consecutive_days
        FROM repo_stats
        WHERE description LIKE ? OR repo_full_name LIKE ?
        ORDER BY last_stars DESC
        LIMIT ?
    """, (f"%{keyword}%", f"%{keyword}%", limit)).fetchall()
    conn.close()
    return rows


def query_rising(min_days=3, limit=20):
    """查询连续上榜 >= N 天的项目"""
    conn = get_db()
    rows = conn.execute("""
        SELECT repo_full_name, description, language, last_stars,
               trending_count_daily, consecutive_days, max_consecutive_days
        FROM repo_stats
        WHERE consecutive_days >= ?
        ORDER BY consecutive_days DESC, last_stars DESC
        LIMIT ?
    """, (min_days, limit)).fetchall()
    conn.close()
    return rows


def query_top(sort='stars', limit=10):
    """查询 Top N 项目"""
    conn = get_db()
    order = "last_stars DESC" if sort == 'stars' else "trending_count_daily DESC"
    rows = conn.execute(f"""
        SELECT repo_full_name, description, language, last_stars,
               trending_count_daily, consecutive_days, max_consecutive_days
        FROM repo_stats
        ORDER BY {order}
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows


def query_stats():
    """输出整体统计"""
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM repo_stats").fetchone()[0]
    by_lang = conn.execute("""
        SELECT language, COUNT(*) as cnt, SUM(last_stars) as total_stars
        FROM repo_stats WHERE language != ''
        GROUP BY language ORDER BY cnt DESC LIMIT 10
    """).fetchall()
    recent = conn.execute("""
        SELECT COUNT(DISTINCT repo_full_name) FROM trending_daily
        WHERE date >= date('now', '-7 days')
    """).fetchone()[0]
    conn.close()
    return {'total': total, 'by_lang': by_lang, 'recent_7d': recent}


def format_rows(rows):
    """格式化查询结果"""
    if not rows:
        return "无结果"
    lines = []
    for i, row in enumerate(rows, 1):
        if hasattr(row, 'keys'):
            # sqlite3.Row
            repo = row['repo_full_name']
            desc = (row['description'] or '')[:60]
            lang = row['language'] or ''
            stars = row['last_stars'] or 0
            count = row['trending_count_daily'] or 0
            consec = row['consecutive_days'] or 0
            lines.append(f"{i}. {repo} ⭐{stars:,} | {lang} | 上榜{count}次 连续{consec}天")
            if desc:
                lines.append(f"   {desc}")
        elif isinstance(row, dict):
            # from tag query
            lines.append(f"{i}. {row['title']} ⭐{row['stars']:,} | {row['language']}")
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='GitHub Trending Wiki 查询')
    parser.add_argument('--lang', help='按语言查询')
    parser.add_argument('--tag', help='按标签查询')
    parser.add_argument('--keyword', help='按关键词搜索')
    parser.add_argument('--rising', action='store_true', help='查询连续上榜项目')
    parser.add_argument('--min-days', type=int, default=3, help='连续上榜最小天数')
    parser.add_argument('--top', type=int, help='查询 Top N')
    parser.add_argument('--sort', choices=['stars', 'count'], default='stars', help='排序方式')
    parser.add_argument('--limit', type=int, default=20, help='最大结果数')
    parser.add_argument('--stats', action='store_true', help='输出整体统计')
    parser.add_argument('--json', action='store_true', help='JSON 格式输出')

    args = parser.parse_args()

    if args.stats:
        stats = query_stats()
        print(f"📊 总计 {stats['total']} 个项目，近 7 天 {stats['recent_7d']} 个")
        print("\n按语言分布：")
        for lang in stats['by_lang']:
            print(f"  {lang['language']}: {lang['cnt']} 个项目, {lang['total_stars']:,} stars")
        return

    if args.lang:
        rows = query_by_language(args.lang, args.sort, args.limit)
        print(f"🔍 语言: {args.lang} ({len(rows)} 个结果)")
        print(format_rows(rows))
    elif args.tag:
        rows = query_by_tag(args.tag, args.limit)
        print(f"🔍 标签: {args.tag} ({len(rows)} 个结果)")
        print(format_rows(rows))
    elif args.keyword:
        rows = query_by_keyword(args.keyword, args.limit)
        print(f"🔍 关键词: {args.keyword} ({len(rows)} 个结果)")
        print(format_rows(rows))
    elif args.rising:
        rows = query_rising(args.min_days, args.limit)
        print(f"🔍 连续上榜 >= {args.min_days} 天 ({len(rows)} 个结果)")
        print(format_rows(rows))
    elif args.top:
        rows = query_top(args.sort, args.top)
        print(f"🔍 Top {args.top} (按{args.sort})")
        print(format_rows(rows))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
