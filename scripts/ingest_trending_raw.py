#!/usr/bin/env python3
"""将 raw/trending{,-weekly,-monthly} JSON 幂等写入 github_trending.db。

权威仍是 raw；本脚本只派生 DB，失败不回滚/不修改 raw，exit≠0 时可单独重跑。
不阻断 scrape（独立进程）；不删无对应 raw 的更早日数据。

用法：
  python3 scripts/ingest_trending_raw.py --all
  python3 scripts/ingest_trending_raw.py --backfill          # 同 --all
  python3 scripts/ingest_trending_raw.py --daily 2026-10-26
  python3 scripts/ingest_trending_raw.py --weekly 2026-10-19
  python3 scripts/ingest_trending_raw.py --monthly 2026-10
  python3 scripts/ingest_trending_raw.py --all --db /tmp/t.db --raw-root /path/to/raw
  python3 scripts/ingest_trending_raw.py --all --no-repo-stats

日 → trending_daily（stars_today）；周 → weekly_trending（stars_this_period→weekly_stars）；
月 → monthly_trending（列名 stars_this_period）。默认先确保月表存在。
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def resolve_base() -> str:
    env_base = os.environ.get("GITHUB_TRENDING_WIKI_PATH")
    if env_base:
        return env_base
    srv = "/srv/www/github-trending-wiki"
    if os.path.isdir(os.path.join(srv, "raw", "trending")):
        return srv
    return REPO_ROOT


def default_db(base: str) -> str:
    return os.path.join(base, "data", "github_trending.db")


def default_raw_root(base: str) -> str:
    return os.path.join(base, "raw")


MONTHLY_DDL = """
CREATE TABLE IF NOT EXISTS monthly_trending (
    month TEXT NOT NULL,
    repo_full_name TEXT NOT NULL,
    rank INTEGER,
    stars_this_period INTEGER,
    description TEXT,
    language TEXT,
    total_stars INTEGER,
    url TEXT,
    PRIMARY KEY (month, repo_full_name)
)
"""

WEEKLY_DDL = """
CREATE TABLE IF NOT EXISTS weekly_trending (
    week_start TEXT NOT NULL,
    week_end TEXT NOT NULL,
    repo_full_name TEXT NOT NULL,
    rank INTEGER,
    weekly_stars INTEGER,
    description TEXT,
    language TEXT,
    PRIMARY KEY (week_start, repo_full_name)
)
"""

DAILY_DDL = """
CREATE TABLE IF NOT EXISTS trending_daily (
    date TEXT NOT NULL,
    period TEXT NOT NULL,
    repo_full_name TEXT NOT NULL,
    rank INTEGER,
    description TEXT,
    language TEXT,
    stars_today INTEGER,
    total_stars INTEGER,
    url TEXT,
    PRIMARY KEY (date, period, repo_full_name)
)
"""

REPO_STATS_DDL = """
CREATE TABLE IF NOT EXISTS repo_stats (
    repo_full_name TEXT PRIMARY KEY,
    description TEXT,
    language TEXT,
    first_seen TEXT,
    last_seen TEXT,
    trending_count_daily INTEGER DEFAULT 0,
    trending_count_weekly INTEGER DEFAULT 0,
    trending_count_monthly INTEGER DEFAULT 0,
    consecutive_days INTEGER DEFAULT 0,
    max_consecutive_days INTEGER DEFAULT 0,
    peak_rank INTEGER,
    max_stars_today INTEGER,
    last_stars INTEGER
)
"""


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(DAILY_DDL)
    conn.execute(WEEKLY_DDL)
    conn.execute(MONTHLY_DDL)
    conn.execute(REPO_STATS_DDL)
    conn.commit()


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def ingest_daily_file(conn: sqlite3.Connection, path: Path) -> int:
    data = load_json(path)
    date_str = data.get("date") or path.stem
    period = data.get("period") or "daily"
    projects = data.get("projects") or []
    # 有 raw 的日：该日 period 行集以 raw 为准（不碰无 raw 的更早日）
    conn.execute(
        "DELETE FROM trending_daily WHERE date = ? AND period = ?",
        (date_str, period),
    )
    n = 0
    for p in projects:
        repo = (p.get("repo") or "").strip()
        if not repo:
            continue
        url = p.get("url") or f"https://github.com/{repo}"
        conn.execute(
            "INSERT OR REPLACE INTO trending_daily "
            "(date, period, repo_full_name, rank, description, language, "
            "stars_today, total_stars, url) VALUES (?,?,?,?,?,?,?,?,?)",
            (
                date_str,
                period,
                repo,
                p.get("rank"),
                p.get("description") or "",
                p.get("language") or "",
                int(p.get("stars_today") or 0),
                int(p.get("total_stars") or 0),
                url,
            ),
        )
        n += 1
    return n


def ingest_weekly_file(conn: sqlite3.Connection, path: Path) -> int:
    data = load_json(path)
    week_start = data.get("week_start") or data.get("date") or path.stem
    week_end = data.get("week_end") or week_start
    projects = data.get("projects") or []
    conn.execute("DELETE FROM weekly_trending WHERE week_start = ?", (week_start,))
    n = 0
    for p in projects:
        repo = (p.get("repo") or "").strip()
        if not repo:
            continue
        weekly_stars = p.get("weekly_stars")
        if weekly_stars is None:
            weekly_stars = p.get("stars_this_period") or 0
        conn.execute(
            "INSERT OR REPLACE INTO weekly_trending "
            "(week_start, week_end, repo_full_name, rank, weekly_stars, "
            "description, language) VALUES (?,?,?,?,?,?,?)",
            (
                week_start,
                week_end,
                repo,
                p.get("rank"),
                int(weekly_stars),
                p.get("description") or "",
                p.get("language") or "",
            ),
        )
        n += 1
    return n


def ingest_monthly_file(conn: sqlite3.Connection, path: Path) -> int:
    data = load_json(path)
    month = data.get("month") or data.get("date") or path.stem
    if len(month) > 7:
        # 容忍误写成 YYYY-MM-DD
        month = month[:7]
    projects = data.get("projects") or []
    conn.execute("DELETE FROM monthly_trending WHERE month = ?", (month,))
    n = 0
    for p in projects:
        repo = (p.get("repo") or "").strip()
        if not repo:
            continue
        stars = p.get("stars_this_period")
        if stars is None:
            stars = p.get("monthly_stars") or 0
        url = p.get("url") or f"https://github.com/{repo}"
        conn.execute(
            "INSERT OR REPLACE INTO monthly_trending "
            "(month, repo_full_name, rank, stars_this_period, description, "
            "language, total_stars, url) VALUES (?,?,?,?,?,?,?,?)",
            (
                month,
                repo,
                p.get("rank"),
                int(stars),
                p.get("description") or "",
                p.get("language") or "",
                int(p.get("total_stars") or 0),
                url,
            ),
        )
        n += 1
    return n


def refresh_repo_stats_aggregates(conn: sqlite3.Connection) -> None:
    """可选：按月表重算 trending_count_monthly；按周表重算 weekly。不删历史日行。"""
    # 确保有列（老库应已有）
    cols = {r[1] for r in conn.execute("PRAGMA table_info(repo_stats)").fetchall()}
    if "trending_count_monthly" not in cols:
        return

    # 月：distinct month per repo
    monthly = {
        r[0]: r[1]
        for r in conn.execute(
            "SELECT repo_full_name, COUNT(DISTINCT month) FROM monthly_trending "
            "GROUP BY repo_full_name"
        )
    }
    weekly = {
        r[0]: r[1]
        for r in conn.execute(
            "SELECT repo_full_name, COUNT(DISTINCT week_start) FROM weekly_trending "
            "GROUP BY repo_full_name"
        )
    }
    # 只更新已存在的 repo_stats 行；月表新仓若无日榜 stats 则轻量插入
    for repo, cnt in monthly.items():
        row = conn.execute(
            "SELECT 1 FROM repo_stats WHERE repo_full_name=?", (repo,)
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE repo_stats SET trending_count_monthly=? WHERE repo_full_name=?",
                (cnt, repo),
            )
        else:
            # 轻量占位，不虚构日统计
            conn.execute(
                "INSERT INTO repo_stats "
                "(repo_full_name, description, language, first_seen, last_seen, "
                "trending_count_daily, trending_count_weekly, trending_count_monthly, "
                "consecutive_days, max_consecutive_days, peak_rank, max_stars_today, last_stars) "
                "VALUES (?,?,?,?,?,0,0,?,0,0,NULL,NULL,NULL)",
                (
                    repo,
                    "",
                    "",
                    None,
                    None,
                    cnt,
                ),
            )
            # fill description/language from monthly if present
            m = conn.execute(
                "SELECT description, language, total_stars FROM monthly_trending "
                "WHERE repo_full_name=? ORDER BY month DESC LIMIT 1",
                (repo,),
            ).fetchone()
            if m:
                conn.execute(
                    "UPDATE repo_stats SET description=?, language=?, last_stars=? "
                    "WHERE repo_full_name=?",
                    (m[0] or "", m[1] or "", m[2], repo),
                )

    for repo, cnt in weekly.items():
        row = conn.execute(
            "SELECT 1 FROM repo_stats WHERE repo_full_name=?", (repo,)
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE repo_stats SET trending_count_weekly=? WHERE repo_full_name=?",
                (cnt, repo),
            )


def list_json(dir_path: Path) -> list[Path]:
    if not dir_path.is_dir():
        return []
    return sorted(p for p in dir_path.glob("*.json") if p.is_file())


def run_ingest(
    db_path: str,
    raw_root: str,
    *,
    do_daily: bool,
    do_weekly: bool,
    do_monthly: bool,
    daily_keys: list[str] | None,
    weekly_keys: list[str] | None,
    monthly_keys: list[str] | None,
    update_repo_stats: bool,
) -> dict[str, Any]:
    raw = Path(raw_root)
    os.makedirs(os.path.dirname(os.path.abspath(db_path)) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    summary: dict[str, Any] = {
        "db": db_path,
        "raw_root": raw_root,
        "daily_files": 0,
        "daily_rows": 0,
        "weekly_files": 0,
        "weekly_rows": 0,
        "monthly_files": 0,
        "monthly_rows": 0,
        "errors": [],
    }
    try:
        ensure_schema(conn)
        if do_daily:
            ddir = raw / "trending"
            files = list_json(ddir)
            if daily_keys:
                want = set(daily_keys)
                files = [f for f in files if f.stem in want]
            for f in files:
                try:
                    n = ingest_daily_file(conn, f)
                    summary["daily_files"] += 1
                    summary["daily_rows"] += n
                except Exception as e:
                    summary["errors"].append(f"daily {f.name}: {e}")
        if do_weekly:
            wdir = raw / "trending-weekly"
            files = list_json(wdir)
            if weekly_keys:
                want = set(weekly_keys)
                files = [f for f in files if f.stem in want]
            for f in files:
                try:
                    n = ingest_weekly_file(conn, f)
                    summary["weekly_files"] += 1
                    summary["weekly_rows"] += n
                except Exception as e:
                    summary["errors"].append(f"weekly {f.name}: {e}")
        if do_monthly:
            mdir = raw / "trending-monthly"
            files = list_json(mdir)
            if monthly_keys:
                want = set(monthly_keys)
                files = [f for f in files if f.stem in want]
            for f in files:
                try:
                    n = ingest_monthly_file(conn, f)
                    summary["monthly_files"] += 1
                    summary["monthly_rows"] += n
                except Exception as e:
                    summary["errors"].append(f"monthly {f.name}: {e}")
        if update_repo_stats and not summary["errors"]:
            refresh_repo_stats_aggregates(conn)
        conn.commit()
        # row counts after
        summary["counts"] = {
            "trending_daily": conn.execute("SELECT COUNT(*) FROM trending_daily").fetchone()[0],
            "weekly_trending": conn.execute("SELECT COUNT(*) FROM weekly_trending").fetchone()[0],
            "monthly_trending": conn.execute("SELECT COUNT(*) FROM monthly_trending").fetchone()[0],
        }
    finally:
        conn.close()
    return summary


def main(argv: list[str] | None = None) -> int:
    base = resolve_base()
    p = argparse.ArgumentParser(
        description="Ingest raw trending JSON into github_trending.db (idempotent)"
    )
    p.add_argument("--db", default=default_db(base), help="Target sqlite (same filename convention)")
    p.add_argument("--raw-root", default=default_raw_root(base), help="Directory containing trending*/")
    p.add_argument("--all", "--backfill", dest="all", action="store_true",
                   help="Ingest all raw daily/weekly/monthly files")
    p.add_argument("--daily", nargs="*", metavar="YYYY-MM-DD",
                   help="Ingest daily; no args = all daily files")
    p.add_argument("--weekly", nargs="*", metavar="YYYY-MM-DD",
                   help="Ingest weekly; no args = all weekly files")
    p.add_argument("--monthly", nargs="*", metavar="YYYY-MM",
                   help="Ingest monthly; no args = all monthly files")
    p.add_argument("--no-repo-stats", action="store_true",
                   help="Skip optional repo_stats aggregate refresh")
    args = p.parse_args(argv)

    do_daily = do_weekly = do_monthly = False
    daily_keys = weekly_keys = monthly_keys = None

    if args.all:
        do_daily = do_weekly = do_monthly = True
    if args.daily is not None:
        do_daily = True
        daily_keys = args.daily or None
    if args.weekly is not None:
        do_weekly = True
        weekly_keys = args.weekly or None
    if args.monthly is not None:
        do_monthly = True
        monthly_keys = args.monthly or None

    if not (do_daily or do_weekly or do_monthly):
        p.print_help()
        print("\n至少指定 --all / --daily / --weekly / --monthly", file=sys.stderr)
        return 2

    summary = run_ingest(
        args.db,
        args.raw_root,
        do_daily=do_daily,
        do_weekly=do_weekly,
        do_monthly=do_monthly,
        daily_keys=daily_keys,
        weekly_keys=weekly_keys,
        monthly_keys=monthly_keys,
        update_repo_stats=not args.no_repo_stats,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary["errors"]:
        print(f"ingest 完成但有 {len(summary['errors'])} 个错误（raw 未改，可重跑）", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
