#!/usr/bin/env python3
"""
月报信号计算模块
从 DB 中计算月度聚合指标，输出 JSON 供 LLM 解读。

用法：
  python3 monthly_signals.py                           # 本月信号（默认）
  python3 monthly_signals.py --year 2026 --month 5     # 指定月份
"""

import json
import os
import sqlite3
import sys
from datetime import date, timedelta
from collections import defaultdict

BASE = '/srv/www/github-trending-wiki'
DB_PATH = os.path.join(BASE, 'data', 'github_trending.db')


def get_month_range(year=None, month=None):
    """返回 (month_start, month_end, prev_month_start, prev_month_end) 的 ISO 日期"""
    today = date.today()
    if year is None:
        year = today.year
    if month is None:
        month = today.month

    # 本月起止
    month_start = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(year, month + 1, 1) - timedelta(days=1)

    # 上月起止
    if month == 1:
        prev_month_start = date(year - 1, 12, 1)
    else:
        prev_month_start = date(year, month - 1, 1)
    prev_month_end = month_start - timedelta(days=1)

    return month_start.isoformat(), month_end.isoformat(), prev_month_start.isoformat(), prev_month_end.isoformat()


def calculate_signals(month_start, month_end, prev_month_start, prev_month_end):
    """计算月度聚合信号"""
    conn = sqlite3.connect(DB_PATH)

    signals = {
        'month': month_start[:7],
        'date_range': f'{month_start} ~ {month_end}',
        'overview': {},
        'retention': {},
        'weekly_domains': {},
        'top_repos': {},
        'month_over_month': {},
    }

    # ── 1. Overview ──
    total_repos = conn.execute('''
        SELECT COUNT(DISTINCT repo_full_name)
        FROM trending_daily
        WHERE date >= ? AND date <= ?
    ''', (month_start, month_end)).fetchone()[0]

    total_stars = conn.execute('''
        SELECT COALESCE(SUM(stars_today), 0)
        FROM trending_daily
        WHERE date >= ? AND date <= ?
    ''', (month_start, month_end)).fetchone()[0]

    daily_dates = conn.execute('''
        SELECT DISTINCT date FROM trending_daily
        WHERE date >= ? AND date <= ? AND period = 'daily'
        ORDER BY date
    ''', (month_start, month_end)).fetchall()
    days_with_data = len(daily_dates)

    signals['overview'] = {
        'total_repos': total_repos,
        'total_stars': total_stars,
        'days_with_data': days_with_data,
        'date_range': f'{month_start} ~ {month_end}',
        'avg_daily_repos': round(total_repos / max(days_with_data, 1), 1),
    }

    # ── 2. Retention distribution ──
    repo_days = conn.execute('''
        SELECT repo_full_name, COUNT(*) as days_on_chart
        FROM trending_daily
        WHERE date >= ? AND date <= ?
        GROUP BY repo_full_name
    ''', (month_start, month_end)).fetchall()

    buckets = {'1': 0, '2-3': 0, '4-7': 0, '8+': 0}
    for _, days in repo_days:
        if days >= 8:
            buckets['8+'] += 1
        elif days >= 4:
            buckets['4-7'] += 1
        elif days >= 2:
            buckets['2-3'] += 1
        else:
            buckets['1'] += 1

    signals['retention'] = {
        'bucket_1day': {'count': buckets['1'], 'ratio': round(buckets['1'] / max(total_repos, 1), 3)},
        'bucket_2_3days': {'count': buckets['2-3'], 'ratio': round(buckets['2-3'] / max(total_repos, 1), 3)},
        'bucket_4_7days': {'count': buckets['4-7'], 'ratio': round(buckets['4-7'] / max(total_repos, 1), 3)},
        'bucket_8plus': {'count': buckets['8+'], 'ratio': round(buckets['8+'] / max(total_repos, 1), 3)},
    }

    # ── 3. Weekly domain slices ──
    # 把月度数据按周分段（最多 5 周），统计每个领域每周的项目数
    month_start_d = date.fromisoformat(month_start)
    month_end_d = date.fromisoformat(month_end)

    # 从 daily_signals 的 category_heat 读取领域信息
    # 但 daily_signals 是按天存的，需要聚合
    # 直接按周从 daily repo domains 计算
    # 先获取 repo → domain 映射（从 entity 文件或 tags）
    repo_domains = defaultdict(set)
    for d in [month_start_d + timedelta(days=i) for i in range((month_end_d - month_start_d).days + 1)]:
        ds = d.isoformat()
        week_num = (d - month_start_d).days // 7 + 1
        week_label = f'week_{week_num}'

        rows = conn.execute('''
            SELECT repo_full_name, language
            FROM trending_daily
            WHERE date = ? AND period = 'daily'
        ''', (ds,)).fetchall()

        for repo, lang in rows:
            # 用语言作为粗粒度 domain 分类
            domain = lang if lang else 'unknown'
            repo_domains[(week_label, domain)].add(repo)

    # 整理为每周的 domain 分布
    weekly_domains = defaultdict(lambda: defaultdict(int))
    for (week_label, domain), repos in repo_domains.items():
        weekly_domains[week_label][domain] = len(repos)

    signals['weekly_domains'] = {
        week: dict(sorted(domains.items(), key=lambda x: -x[1])[:10])
        for week, domains in sorted(weekly_domains.items())
    }

    # ── 4. Four-dimensional ranking ──

    # 4a. 持久王 — 累计在榜天数最多的
    endurance = sorted(repo_days, key=lambda x: -x[1])[:10]
    # 补充每个 repo 的信息
    endurance_detail = []
    for repo, days in endurance:
        row = conn.execute('''
            SELECT language, SUM(stars_today), MIN(rank), MAX(stars_today)
            FROM trending_daily
            WHERE repo_full_name = ? AND date >= ? AND date <= ?
        ''', (repo, month_start, month_end)).fetchone()
        endurance_detail.append({
            'repo': repo,
            'days_on_chart': days,
            'language': row[0] or '?',
            'total_monthly_stars': row[1] or 0,
            'best_rank': row[2] or 99,
            'peak_daily_stars': row[3] or 0,
        })

    # 4b. 爆发王 — 单日峰值星数最高的
    explosiveness = conn.execute('''
        SELECT repo_full_name, MAX(stars_today) as peak_stars, date
        FROM trending_daily
        WHERE date >= ? AND date <= ?
        GROUP BY repo_full_name
        ORDER BY peak_stars DESC
        LIMIT 10
    ''', (month_start, month_end)).fetchall()
    explosiveness_detail = [
        {
            'repo': r[0],
            'peak_daily_stars': r[1],
            'peak_date': r[2],
            'language': conn.execute(
                'SELECT language FROM trending_daily WHERE repo_full_name = ? AND date = ?',
                (r[0], r[2])
            ).fetchone()[0] or '?'
        }
        for r in explosiveness
    ]

    # 4c. 本月新秀 — 本月首次出现且至少上榜 2 天
    newcomer = conn.execute('''
        SELECT r.repo_full_name,
               COUNT(*) as days_on_chart,
               MAX(r.stars_today) as peak_stars,
               MIN(r.rank) as best_rank,
               MIN(r.date) as first_appearance
        FROM trending_daily r
        WHERE r.date >= ? AND r.date <= ?
          AND r.repo_full_name NOT IN (
              SELECT DISTINCT repo_full_name FROM trending_daily
              WHERE date < ?
          )
        GROUP BY r.repo_full_name
        HAVING days_on_chart >= 2
        ORDER BY peak_stars DESC
        LIMIT 10
    ''', (month_start, month_end, month_start)).fetchall()
    newcomer_detail = [
        {
            'repo': r[0],
            'days_on_chart': r[1],
            'peak_daily_stars': r[2] or 0,
            'best_rank': r[3] or 99,
            'first_appearance': r[4],
            'language': conn.execute(
                'SELECT language FROM trending_daily WHERE repo_full_name = ? ORDER BY date DESC LIMIT 1',
                (r[0],)
            ).fetchone()[0] or '?'
        }
        for r in newcomer
    ]

    # 4d. 老兵不死 — 上个月也上榜过且本月仍在榜的
    # 检查 repo_stats 是否有跨月记录
    veteran = conn.execute('''
        SELECT DISTINCT r.repo_full_name
        FROM trending_daily r
        WHERE r.date >= ? AND r.date <= ?
          AND r.repo_full_name IN (
              SELECT DISTINCT repo_full_name FROM trending_daily
              WHERE date >= ? AND date <= ?
          )
    ''', (month_start, month_end, prev_month_start, prev_month_end)).fetchall()
    veteran_detail = []
    for (repo,) in veteran:
        stats = conn.execute('''
            SELECT trending_count_daily, max_consecutive_days, max_stars_today
            FROM repo_stats WHERE repo_full_name = ?
        ''', (repo,)).fetchone()
        # 本月表现
        this_month = conn.execute('''
            SELECT COUNT(*), SUM(stars_today), MAX(stars_today)
            FROM trending_daily
            WHERE repo_full_name = ? AND date >= ? AND date <= ?
        ''', (repo, month_start, month_end)).fetchone()
        veteran_detail.append({
            'repo': repo,
            'total_daily_count': stats[0] if stats else 0,
            'max_consecutive_days': stats[1] if stats else 0,
            'this_month_days': this_month[0],
            'this_month_stars': this_month[1] or 0,
            'peak_stars': max(this_month[2] or 0, (stats[2] if stats else 0) or 0),
        })
    veteran_detail.sort(key=lambda x: -x['this_month_days'])

    signals['top_repos'] = {
        'endurance': endurance_detail[:8],
        'explosiveness': explosiveness_detail[:8],
        'newcomer': newcomer_detail[:8],
        'veteran': veteran_detail[:8],
    }

    # ── 5. Month-over-month 对比 ──
    # 检查上个月有没有数据
    prev_total = conn.execute('''
        SELECT COUNT(DISTINCT repo_full_name)
        FROM trending_daily
        WHERE date >= ? AND date <= ?
    ''', (prev_month_start, prev_month_end)).fetchone()[0]

    prev_stars = conn.execute('''
        SELECT COALESCE(SUM(stars_today), 0)
        FROM trending_daily
        WHERE date >= ? AND date <= ?
    ''', (prev_month_start, prev_month_end)).fetchone()[0]

    prev_dates = conn.execute('''
        SELECT DISTINCT date FROM trending_daily
        WHERE date >= ? AND date <= ? AND period = 'daily'
        ORDER BY date
    ''', (prev_month_start, prev_month_end)).fetchall()

    signals['month_over_month'] = {
        'prev_month_days': len(prev_dates),
        'prev_month_repos': prev_total,
        'prev_month_stars': prev_stars,
        'repo_change': round(total_repos - prev_total, 0),
        'stars_change': round(total_stars - prev_stars, 0),
        'repo_change_pct': round((total_repos - prev_total) / max(prev_total, 1) * 100, 1) if prev_total > 0 else None,
        'stars_change_pct': round((total_stars - prev_stars) / max(prev_stars, 1) * 100, 1) if prev_stars > 0 else None,
    }

    conn.close()
    return signals


def main():
    year = None
    month = None
    for i, arg in enumerate(sys.argv[1:]):
        if arg == '--year' and i + 2 < len(sys.argv):
            year = int(sys.argv[i + 2])
        elif arg == '--month' and i + 2 < len(sys.argv):
            month = int(sys.argv[i + 2])

    month_start, month_end, prev_start, prev_end = get_month_range(year, month)

    print(f'📊 计算月度信号: {month_start} ~ {month_end}', file=sys.stderr)
    print(f'📊 对比上月: {prev_start} ~ {prev_end}', file=sys.stderr)

    signals = calculate_signals(month_start, month_end, prev_start, prev_end)

    # 输出 JSON
    out_path = os.path.join(BASE, 'raw', 'monthly_signals', f'{month_start}.json')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(signals, f, ensure_ascii=False, indent=2)

    print(f'✅ 信号已保存: {out_path}', file=sys.stderr)
    print(json.dumps(signals, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
