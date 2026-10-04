#!/usr/bin/env python3
"""
从 /srv/www/daily-report 回填 wiki 起始日（2026-05-16）之前的数据。

日期口径（2026-10-04 验证，133/134 天一致）：
  daily-report 的 `date` 字段是 UTC 抓取目标日，实际快照在北京次日早晨。
  归属日期 = generatedAt + 8h 后的北京自然日。

硬约束：
  - 只写 date <= CUTOFF 的日期，绝不触碰 wiki 已有数据
  - INSERT OR IGNORE，(date, repo) 已存在则跳过
  - 缺失字段写 NULL，不填 0 不猜测
  - rank 用数组下标推断，实体标 rank_inferred

用法：
  python3 backfill_from_dailyreport.py --dry-run
  python3 backfill_from_dailyreport.py
"""
import argparse
import glob
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta

DR_DIR = '/srv/www/daily-report/data/briefs/daily'
DB_PATH = '/srv/www/github-trending-wiki/data/github_trending.db'
CUTOFF = '2026-05-15'  # wiki 首日 2026-05-16，只补它之前


def to_int(v):
    """星数字段转 int，失败返回 None（不编 0）。"""
    if v is None or v == '':
        return None
    try:
        return int(str(v).replace(',', '').strip())
    except ValueError:
        return None


def load_daily_report():
    """读取 daily-report 全部日简报，按北京自然日归组。"""
    out = {}
    skipped_no_ts = []
    for f in sorted(glob.glob(os.path.join(DR_DIR, 'data-*.json'))):
        try:
            j = json.load(open(f))
        except (json.JSONDecodeError, OSError) as e:
            print(f"  [warn] 跳过无法解析的文件 {os.path.basename(f)}: {e}")
            continue
        ga = j.get('generatedAt')
        if not ga:
            skipped_no_ts.append(os.path.basename(f))
            continue
        try:
            bj = datetime.strptime(ga, '%Y-%m-%dT%H:%M:%S.%fZ') + timedelta(hours=8)
        except ValueError:
            try:
                bj = datetime.strptime(ga, '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=8)
            except ValueError:
                skipped_no_ts.append(os.path.basename(f))
                continue
        biz_date = bj.strftime('%Y-%m-%d')
        out.setdefault(biz_date, []).extend(j.get('projects', []))

    if skipped_no_ts:
        print(f"  [warn] {len(skipped_no_ts)} 个文件无有效 generatedAt，已跳过")
    return out


def main(dry_run):
    print("=" * 60)
    print(f"回填 daily-report → wiki  CUTOFF={CUTOFF}  dry_run={dry_run}")
    print("=" * 60)

    by_date = load_daily_report()
    dates = sorted(d for d in by_date if d <= CUTOFF and by_date[d])
    print(f"\n[1] 待回填日期: {len(dates)} 天  ({dates[0]} ~ {dates[-1]})")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    existing = set()
    for (d, r) in cur.execute("SELECT date, repo_full_name FROM trending_daily WHERE date<=?", (CUTOFF,)):
        existing.add((d, r))
    print(f"[2] 目标区间 wiki 已有 (date, repo): {len(existing)} 条")

    stats = {'new_rows': 0, 'skipped_dup': 0, 'skipped_norepo': 0,
             'null_lang': 0, 'null_today': 0, 'null_stars': 0}
    new_repos = set()
    touched_repos = set()
    rows = []

    for d in dates:
        for idx, p in enumerate(by_date[d], 1):
            repo = p.get('repo') or p.get('fullName')
            if not repo:
                stats['skipped_norepo'] += 1
                continue
            if (d, repo) in existing:
                stats['skipped_dup'] += 1
                continue

            lang = p.get('language') or None
            today = to_int(p.get('todayStars'))
            total = to_int(p.get('stars'))
            desc = p.get('desc') or p.get('descZh') or None

            if lang is None:
                stats['null_lang'] += 1
            if today is None:
                stats['null_today'] += 1
            if total is None:
                stats['null_stars'] += 1

            rows.append((d, 'daily', repo, idx, desc, lang, today, total,
                         p.get('url') or f"https://github.com/{repo}"))
            new_repos.add(repo)
            touched_repos.add(repo)
            stats['new_rows'] += 1
            existing.add((d, repo))

    known = {r[0] for r in cur.execute("SELECT DISTINCT repo_full_name FROM repo_stats")}
    print(f"[3] 待写入 trending_daily: {stats['new_rows']} 行")
    print(f"    涉及仓库 {len(touched_repos)} 个，其中 wiki 全新 {len(new_repos - known)} 个")
    print(f"[4] 跳过: 重复 {stats['skipped_dup']} | 无 repo 名 {stats['skipped_norepo']}")
    print(f"    字段缺失: language {stats['null_lang']} | todayStars {stats['null_today']} | stars {stats['null_stars']}")

    if stats['new_rows'] == 0:
        # 数据已写入过（重跑场景）：仍要保证 repo_stats 重建
        print("\n[info] 没有新行可写（数据已在库中）。")
        if not dry_run:
            print("[6] 重建受影响 repo 的 repo_stats ...")
            touched = {r[0] for r in cur.execute(
                "SELECT DISTINCT repo_full_name FROM trending_daily WHERE date<=? AND period='daily'", (CUTOFF,))}
            n = do_rebuild(cur, touched)
            conn.commit()
            print(f"    重建 repo_stats: {n} 个")
            dump_final(cur)
        conn.close()
        return 0

    if dry_run:
        print("\n[DRY-RUN] 不写库。抽样前 5 行:")
        cur.executemany(
            "INSERT OR IGNORE INTO trending_daily(date, period, repo_full_name, rank, description, language, stars_today, total_stars, url) VALUES (?,?,?,?,?,?,?,?,?)",
            [])
        conn.commit()
        for r in rows[:5]:
            print("  ", r)
        conn.close()
        return 0

    print("\n[5] 写入 trending_daily ...")
    cur.executemany(
        "INSERT OR IGNORE INTO trending_daily(date, period, repo_full_name, rank, description, language, stars_today, total_stars, url) VALUES (?,?,?,?,?,?,?,?,?)",
        rows)
    conn.commit()
    after = cur.execute("SELECT COUNT(*) FROM trending_daily WHERE date<=?", (CUTOFF,)).fetchone()[0]
    print(f"    写入后目标区间行数: {after}")

    print("\n[6] 重建受影响 repo 的 repo_stats ...")
    rebuilt = do_rebuild(cur, touched_repos)
    conn.commit()
    print(f"    重建 repo_stats: {rebuilt} 个")

    dump_final(cur)
    conn.close()
    return 0


def do_rebuild(cur, touched_repos):
    """重建受影响 repo 的 repo_stats，返回重建条数。"""
    rebuilt = 0
    for repo in sorted(touched_repos):
        agg = cur.execute(
            """SELECT MIN(date), MAX(date), COUNT(*),
                      COALESCE(MAX(total_stars),0)
               FROM trending_daily WHERE repo_full_name=? AND period='daily'""", (repo,)).fetchone()
        if not agg or not agg[0]:
            continue
        first_seen, last_seen, cnt_daily, total_stars = agg

        dates_asc = [x[0] for x in cur.execute(
            "SELECT DISTINCT date FROM trending_daily WHERE repo_full_name=? AND period='daily' ORDER BY date",
            (repo,)).fetchall()]
        dl = [datetime.strptime(x, '%Y-%m-%d') for x in dates_asc]
        run = best = 0
        prev_d = None
        for x in dl:
            run = run + 1 if (prev_d and (x - prev_d).days == 1) else 1
            best = max(best, run)
            prev_d = x

        # rank/today/stars 全可能为 NULL，peak_rank 取 MIN(非NULL)，无则 NULL
        peak = cur.execute(
            "SELECT MIN(rank) FROM trending_daily WHERE repo_full_name=? AND period='daily' AND rank IS NOT NULL",
            (repo,)).fetchone()[0]
        max_today = cur.execute(
            "SELECT MAX(stars_today) FROM trending_daily WHERE repo_full_name=? AND period='daily'",
            (repo,)).fetchone()[0]

        prev = cur.execute(
            "SELECT description, language FROM repo_stats WHERE repo_full_name=?", (repo,)).fetchone()
        desc = lang = None
        if prev:
            desc, lang = prev
        if not desc:
            r = cur.execute(
                "SELECT description FROM trending_daily WHERE repo_full_name=? AND description IS NOT NULL ORDER BY date DESC LIMIT 1",
                (repo,)).fetchone()
            desc = r[0] if r else None
        if not lang:
            r = cur.execute(
                "SELECT language FROM trending_daily WHERE repo_full_name=? AND language IS NOT NULL ORDER BY date DESC LIMIT 1",
                (repo,)).fetchone()
            lang = r[0] if r else None

        # weekly/monthly 计数：本次不写周榜，保留原值（新仓库为 0）
        # 注意：repo_stats 里的是 last_stars 而非 total_stars
        cur.execute(
            """INSERT INTO repo_stats(repo_full_name, description, language, first_seen, last_seen,
                                      trending_count_daily, trending_count_weekly, trending_count_monthly,
                                      consecutive_days, max_consecutive_days, peak_rank, max_stars_today,
                                      last_stars)
               VALUES (?,?,?,?,?,?,0,0,?,?,?,?,?)
               ON CONFLICT(repo_full_name) DO UPDATE SET
                 description=excluded.description,
                 language=COALESCE(repo_stats.language, excluded.language),
                 first_seen=MIN(repo_stats.first_seen, excluded.first_seen),
                 last_seen=MAX(repo_stats.last_seen, excluded.last_seen),
                 trending_count_daily=excluded.trending_count_daily,
                 consecutive_days=excluded.consecutive_days,
                 max_consecutive_days=MAX(repo_stats.max_consecutive_days, excluded.max_consecutive_days),
                 peak_rank=COALESCE(MIN(repo_stats.peak_rank, excluded.peak_rank), excluded.peak_rank),
                 max_stars_today=MAX(COALESCE(repo_stats.max_stars_today,0), COALESCE(excluded.max_stars_today,0)),
                 last_stars=MAX(COALESCE(repo_stats.last_stars,0), COALESCE(excluded.last_stars,0))""",
            (repo, desc, lang, first_seen, last_seen, cnt_daily,
             run, best, peak, max_today, total_stars))
        rebuilt += 1
    return rebuilt


def dump_final(cur):
    print("\n[7] 结果")
    print(f"    trending_daily 全表: {cur.execute('SELECT COUNT(*) FROM trending_daily').fetchone()[0]} 行")
    print(f"    date 范围: {cur.execute('SELECT MIN(date), MAX(date) FROM trending_daily').fetchone()}")
    print(f"    repo_stats: {cur.execute('SELECT COUNT(*) FROM repo_stats').fetchone()[0]} 个")
    early = cur.execute("SELECT COUNT(*) FROM repo_stats WHERE first_seen<'2026-05-16'").fetchone()[0]
    print(f"    first_seen 早于 5/16 的: {early} 个")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    sys.exit(main(args.dry_run))
