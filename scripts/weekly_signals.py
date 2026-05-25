#!/usr/bin/env python3
"""
周报信号计算模块
从 DB 中计算三轴信号指标（持续性轴、爆发力轴、交叉信号），输出 JSON。

用法：
  python3 weekly_signals.py                       # 本周信号（默认）
  python3 weekly_signals.py --date 2026-05-18     # 指定周的信号
  python3 weekly_signals.py --prev-week           # 上周信号（对比用）
"""

import json
import os
import sqlite3
import sys
from datetime import date, timedelta

BASE = '/srv/www/github-trending-wiki'
DB_PATH = os.path.join(BASE, 'data', 'github_trending.db')


def get_week_dates(base_date=None):
    """返回 (week_start, week_end) 包含 base_date 的那一周"""
    if base_date is None:
        base_date = date.today()
    elif isinstance(base_date, str):
        base_date = date.fromisoformat(base_date)
    monday = base_date - timedelta(days=base_date.weekday())
    sunday = monday + timedelta(days=6)
    return monday.isoformat(), sunday.isoformat()


def get_prev_week_dates(week_start):
    """返回上周的起止日期"""
    prev_monday = date.fromisoformat(week_start) - timedelta(days=7)
    prev_sunday = prev_monday + timedelta(days=6)
    return prev_monday.isoformat(), prev_sunday.isoformat()


def calculate_signals(week_start, week_end):
    """计算三轴信号"""
    conn = sqlite3.connect(DB_PATH)

    # ---- 1. 持续性轴：从每日榜计算 ----
    daily_rows = conn.execute('''
        SELECT repo_full_name,
               COUNT(*) as days_on_chart,
               MAX(stars_today) as peak_daily_stars,
               MIN(rank) as best_rank,
               MAX(rank) as worst_rank,
               SUM(stars_today) as total_daily_stars
        FROM trending_daily
        WHERE date >= ? AND date <= ? AND period = 'daily'
        GROUP BY repo_full_name
    ''', (week_start, week_end)).fetchall()

    # 构建每日榜项目集合
    daily_projects = {r[0]: {
        'days_on_chart': r[1],
        'peak_daily_stars': r[2] or 0,
        'best_rank': r[3],
        'worst_rank': r[4],
        'total_daily_stars': r[5] or 0,
    } for r in daily_rows}

    # ---- 2. 爆发力轴：从周榜表 ----
    weekly_rows = conn.execute('''
        SELECT repo_full_name, weekly_stars, rank, description, language
        FROM weekly_trending
        WHERE week_start = ?
        ORDER BY rank
    ''', (week_start,)).fetchall()

    if not weekly_rows:
        # 周榜还没采集时给个友好提示
        conn.close()
        return {
            'error': 'weekly_trending 表无本周数据，请先运行 github_weekly_collector.py',
            'week_start': week_start,
            'week_end': week_end,
        }

    weekly_map = {}
    for r in weekly_rows:
        weekly_map[r[0]] = {
            'weekly_stars': r[1] or 0,
            'weekly_rank': r[2],
            'description': r[3] or '',
            'language': r[4] or '',
        }

    # ---- 3. 计算上周活跃项目（判断"本周首次上榜"） ----
    prev_ws, prev_we = get_prev_week_dates(week_start)
    prev_active = set(r[0] for r in conn.execute(
        'SELECT DISTINCT repo_full_name FROM trending_daily WHERE date >= ? AND date <= ?',
        (prev_ws, prev_we)).fetchall())

    conn.close()

    # ---- 4. 组装所有项目信号 ----
    all_repos = set(list(daily_projects.keys()) + list(weekly_map.keys()))
    projects = []

    for repo in all_repos:
        daily = daily_projects.get(repo, {})
        weekly = weekly_map.get(repo, {})

        consec_days = daily.get('days_on_chart', 0)
        weekly_stars = weekly.get('weekly_stars', 0)
        weekly_rank = weekly.get('weekly_rank', 999)

        signals = {
            'repo': repo,
            'description': weekly.get('description', daily_projects.get(repo, {}).get('description', '')),
            'language': weekly.get('language', ''),
            'consecutive_days': consec_days,
            'peak_daily_stars': daily.get('peak_daily_stars', 0),
            'total_daily_stars': daily.get('total_daily_stars', 0),
            'best_rank': daily.get('best_rank'),
            'rank_volatility': (
                (daily.get('worst_rank', 0) - daily.get('best_rank', 0))
                if daily.get('best_rank') and daily.get('worst_rank')
                else None
            ),
            'weekly_stars': weekly_stars,
            'weekly_rank': weekly_rank,
            'has_weekly_data': repo in weekly_map,
            'is_new_this_week': repo not in prev_active and consec_days > 0,
        }

        # ---- 5. 交叉信号分类 ----
        if consec_days >= 4 and weekly_rank is not None and weekly_rank <= 10:
            signals['signal_type'] = 'persistent_leader'
        elif weekly_rank is not None and weekly_rank <= 5 and consec_days <= 2 and consec_days > 0:
            signals['signal_type'] = 'burst_star'
        elif repo in prev_active and consec_days >= 1:
            signals['signal_type'] = 'comeback'
        elif consec_days == 0 and weekly_stars > 0:
            signals['signal_type'] = 'weekly_only'
        else:
            signals['signal_type'] = 'normal'

        projects.append(signals)

    # ---- 6. 统计算法 ----
    total_weekly = sum(p['weekly_stars'] for p in projects)
    top_by_daily = sorted(projects, key=lambda p: p['total_daily_stars'], reverse=True)[:5]
    top_by_weekly = sorted([p for p in projects if p['has_weekly_data']],
                           key=lambda p: p['weekly_stars'], reverse=True)[:5]

    # 领域热度（按语言分组）
    lang_dist = {}
    for p in projects:
        lang = p['language'] or 'Unknown'
        lang_dist[lang] = lang_dist.get(lang, 0) + 1
    lang_dist_sorted = sorted(lang_dist.items(), key=lambda x: -x[1])

    return {
        'week_start': week_start,
        'week_end': week_end,
        'summary': {
            'total_projects': len(projects),
            'total_weekly_stars': total_weekly,
            'new_projects_this_week': sum(1 for p in projects if p['is_new_this_week']),
            'persistent_leaders': sum(1 for p in projects if p['signal_type'] == 'persistent_leader'),
            'burst_stars': sum(1 for p in projects if p['signal_type'] == 'burst_star'),
            'comebacks': sum(1 for p in projects if p['signal_type'] == 'comeback'),
            'language_distribution': lang_dist_sorted,
        },
        'top_by_daily_stars': top_by_daily,
        'top_by_weekly_stars': top_by_weekly,
        'projects': sorted(projects, key=lambda p: (
            -p['weekly_stars'] if p['has_weekly_data'] else -p['total_daily_stars']
        )),
    }


def main():
    ws = we = None
    if '--prev-week' in sys.argv:
        ws, we = get_prev_week_dates(get_week_dates()[0])
    elif any(a.startswith('--date=') for a in sys.argv):
        for a in sys.argv:
            if a.startswith('--date='):
                ws, we = get_week_dates(a.split('=', 1)[1])
    else:
        ws, we = get_week_dates()

    if not ws or not we:
        print('无法确定日期范围', file=sys.stderr)
        sys.exit(1)

    result = calculate_signals(ws, we)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
