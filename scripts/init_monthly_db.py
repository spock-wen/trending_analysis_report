#!/usr/bin/env python3
"""初始化 monthly_trending 表（幂等 CREATE TABLE IF NOT EXISTS）。

对齐 raw/trending-monthly/*.json；PK (month, repo_full_name)；月键 YYYY-MM。
字段用 stars_this_period（与周榜 weekly_stars 命名刻意区分，对齐 raw 契约）。

用法：
  python3 scripts/init_monthly_db.py
  python3 scripts/init_monthly_db.py --db /path/to/github_trending.db
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys

DDL = """
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


def default_db_path() -> str:
    env_base = os.environ.get("GITHUB_TRENDING_WIKI_PATH")
    if env_base:
        return os.path.join(env_base, "data", "github_trending.db")
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(repo, "data", "github_trending.db")


def init_monthly(db_path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(db_path)) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(DDL)
        conn.commit()
    finally:
        conn.close()
    print(f"monthly_trending table ready @ {db_path}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Init monthly_trending table")
    p.add_argument("--db", default=default_db_path(), help="Path to github_trending.db")
    args = p.parse_args(argv)
    init_monthly(args.db)
    return 0


if __name__ == "__main__":
    sys.exit(main())
