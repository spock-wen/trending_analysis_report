#!/usr/bin/env python3
"""补采脚本：将旧格式的 raw JSON 导入 DB"""
import json, sqlite3, os, sys
from datetime import datetime

BASE = '/srv/www/github-trending-wiki'
DB_PATH = os.path.join(BASE, 'data', 'github_trending.db')
RAW_DIR = os.path.join(BASE, 'raw', 'trending')

def backfill_date(date_str):
    filepath = os.path.join(RAW_DIR, f'{date_str}.json')
    if not os.path.exists(filepath):
        print(f'❌ 文件不存在: {filepath}')
        return False

    with open(filepath) as f:
        raw = json.load(f)

    projects = raw.get('projects', [])
    if not projects:
        print(f'❌ {date_str}: 无项目数据')
        return False

    conn = sqlite3.connect(DB_PATH)
    count = 0

    # 标准化项目字段
    for p in projects:
        # 补全缺失字段
        p.setdefault('period', 'daily')
        p.setdefault('url', f"https://github.com/{p.get('repo', '')}")
        p.setdefault('stars_today', 0)
        p.setdefault('total_stars', 0)

        repo = p.get('repo', '')
        if not repo:
            continue

        try:
            conn.execute(
                "INSERT OR REPLACE INTO trending_daily "
                "(date, period, repo_full_name, rank, description, language, stars_today, total_stars, url) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (date_str, 'daily', repo, p.get('rank'), p.get('description', ''),
                 p.get('language', ''), p.get('stars_today', 0), p.get('total_stars', 0),
                 p.get('url', ''))
            )
            count += 1
        except Exception as e:
            print(f'  跳过 {repo}: {e}')

    conn.commit()
    print(f'✅ {date_str}: 导入 {count}/{len(projects)} 个项目到 trending_daily')

    # 更新 repo_stats
    for p in projects:
        repo = p.get('repo', '')
        if not repo:
            continue
        cursor = conn.execute(
            'SELECT date FROM trending_daily WHERE repo_full_name=? AND period=? ORDER BY date DESC',
            (repo, 'daily')
        )
        dates = [r[0] for r in cursor.fetchall()]
        if not dates:
            continue

        count_days = len(dates)
        first_seen = dates[-1]
        last_seen = dates[0]

        # 连续天数
        consecutive = 1
        from datetime import timedelta
        for i in range(1, len(dates)):
            prev = datetime.strptime(dates[i-1], '%Y-%m-%d')
            curr = datetime.strptime(dates[i], '%Y-%m-%d')
            if (prev - curr).days <= 1:
                consecutive += 1
            else:
                break

        cursor = conn.execute(
            'SELECT MIN(rank), MAX(stars_today) FROM trending_daily WHERE repo_full_name=? AND period=?',
            (repo, 'daily')
        )
        row = cursor.fetchone()
        peak_rank = row[0] or p.get('rank', 999)
        max_stars = row[1] or p.get('stars_today', 0)

        c2 = conn.execute('SELECT 1 FROM repo_stats WHERE repo_full_name=?', (repo,))
        exists = c2.fetchone()

        if exists:
            conn.execute('''
                UPDATE repo_stats SET
                    last_seen=?, trending_count_daily=?, consecutive_days=?,
                    max_consecutive_days=MAX(max_consecutive_days, ?),
                    peak_rank=?, max_stars_today=?, last_stars=?,
                    description=?, language=?
                WHERE repo_full_name=?
            ''', (last_seen, count_days, consecutive, consecutive,
                  peak_rank, max_stars, p.get('total_stars', 0),
                  p.get('description', ''), p.get('language', ''), repo))
        else:
            conn.execute('''
                INSERT INTO repo_stats
                (repo_full_name, description, language, first_seen, last_seen,
                 trending_count_daily, trending_count_weekly, trending_count_monthly,
                 consecutive_days, max_consecutive_days, peak_rank, max_stars_today, last_stars)
                VALUES (?,?,?,?,?,?,0,0,?,?,?,?,?)
            ''', (repo, p.get('description', ''), p.get('language', ''),
                  first_seen, last_seen, count_days, consecutive, consecutive,
                  peak_rank, max_stars, p.get('total_stars', 0)))

    conn.commit()
    conn.close()
    print(f'✅ {date_str}: repo_stats 更新完成')
    return True

if __name__ == '__main__':
    dates = sys.argv[1:] if len(sys.argv) > 1 else []
    if not dates:
        print('用法: python3 backfill.py YYYY-MM-DD [YYYY-MM-DD ...]')
        print('或: python3 backfill.py --all-missing   # 自动检测缺失日期')
        sys.exit(1)

    if dates[0] == '--all-missing':
        # 自动检测从 5/16 到今天的缺失日期
        from datetime import date, timedelta
        conn = sqlite3.connect(DB_PATH)
        in_db = set(r[0] for r in conn.execute(
            'SELECT DISTINCT date FROM trending_daily WHERE period="daily"').fetchall())
        conn.close()

        start = date(2026, 5, 16)
        end = date.today()
        missing = []
        for d in (start + timedelta(n) for n in range((end - start).days + 1)):
            ds = d.isoformat()
            if ds not in in_db:
                fp = os.path.join(RAW_DIR, f'{ds}.json')
                if os.path.exists(fp):
                    missing.append(ds)

        if not missing:
            print('✅ 没有可补采的缺失日期')
            sys.exit(0)
        print(f'检测到可补采的日期: {missing}')
        for ds in missing:
            backfill_date(ds)
    else:
        for ds in dates:
            backfill_date(ds)
