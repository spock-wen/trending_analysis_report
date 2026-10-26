#!/usr/bin/env python3
"""对账：github_trending.db 与 raw/trending* 行集（repo 集合 + 关键 stars）。

- 有 raw 的日/周/月：要求 DB ≡ raw（集合 + stars）
- DB-only 更早日（无对应 raw 文件）不视为失败，单独统计
- 近窗默认 14 日抽查可复现

用法：
  python3 scripts/reconcile_trending_db.py
  python3 scripts/reconcile_trending_db.py --window 14 --out /tmp/reconcile.json
  python3 scripts/reconcile_trending_db.py --db … --raw-root …
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
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


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def reconcile_daily(conn: sqlite3.Connection, raw_dir: Path, window: int | None) -> dict[str, Any]:
    files = sorted(raw_dir.glob("*.json")) if raw_dir.is_dir() else []
    raw_dates = {f.stem for f in files}
    db_dates = {
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT date FROM trending_daily WHERE period='daily'"
        )
    }
    only_db = sorted(db_dates - raw_dates)
    only_raw = sorted(raw_dates - db_dates)

    check_files = files
    if window is not None and window > 0:
        cutoff = (datetime.now() - timedelta(days=window - 1)).strftime("%Y-%m-%d")
        check_files = [f for f in files if f.stem >= cutoff]

    ok = partial = fail = 0
    mismatches: list[dict[str, Any]] = []
    for f in check_files:
        data = load_json(f)
        date_str = data.get("date") or f.stem
        period = data.get("period") or "daily"
        raw_map = {}
        for p in data.get("projects") or []:
            repo = (p.get("repo") or "").strip()
            if not repo:
                continue
            raw_map[repo] = int(p.get("stars_today") or 0)
        db_rows = conn.execute(
            "SELECT repo_full_name, stars_today FROM trending_daily "
            "WHERE date=? AND period=?",
            (date_str, period),
        ).fetchall()
        db_map = {r[0]: int(r[1] or 0) for r in db_rows}
        raw_set, db_set = set(raw_map), set(db_map)
        if raw_set == db_set and all(raw_map[k] == db_map[k] for k in raw_set):
            ok += 1
        elif raw_set & db_set:
            partial += 1
            mismatches.append(
                {
                    "date": date_str,
                    "only_raw": sorted(raw_set - db_set),
                    "only_db": sorted(db_set - raw_set),
                    "stars_diff": {
                        k: {"raw": raw_map[k], "db": db_map[k]}
                        for k in sorted(raw_set & db_set)
                        if raw_map[k] != db_map[k]
                    },
                }
            )
        else:
            fail += 1
            mismatches.append(
                {
                    "date": date_str,
                    "only_raw": sorted(raw_set - db_set),
                    "only_db": sorted(db_set - raw_set),
                    "stars_diff": {},
                }
            )

    return {
        "raw_files": len(files),
        "db_dates": len(db_dates),
        "only_db_dates": only_db,
        "only_db_count": len(only_db),
        "only_raw_dates": only_raw,
        "checked": len(check_files),
        "ok": ok,
        "partial": partial,
        "fail": fail,
        "mismatches": mismatches[:20],
    }


def reconcile_weekly(conn: sqlite3.Connection, raw_dir: Path) -> dict[str, Any]:
    files = sorted(raw_dir.glob("*.json")) if raw_dir.is_dir() else []
    ok = partial = fail = 0
    mismatches: list[dict[str, Any]] = []
    for f in files:
        data = load_json(f)
        week_start = data.get("week_start") or data.get("date") or f.stem
        raw_map = {}
        for p in data.get("projects") or []:
            repo = (p.get("repo") or "").strip()
            if not repo:
                continue
            stars = p.get("stars_this_period")
            if stars is None:
                stars = p.get("weekly_stars") or 0
            raw_map[repo] = int(stars)
        db_rows = conn.execute(
            "SELECT repo_full_name, weekly_stars FROM weekly_trending WHERE week_start=?",
            (week_start,),
        ).fetchall()
        db_map = {r[0]: int(r[1] or 0) for r in db_rows}
        raw_set, db_set = set(raw_map), set(db_map)
        if raw_set == db_set and all(raw_map[k] == db_map[k] for k in raw_set):
            ok += 1
        elif raw_set & db_set:
            partial += 1
            mismatches.append(
                {
                    "week_start": week_start,
                    "only_raw": sorted(raw_set - db_set),
                    "only_db": sorted(db_set - raw_set),
                    "stars_diff": {
                        k: {"raw": raw_map[k], "db": db_map[k]}
                        for k in sorted(raw_set & db_set)
                        if raw_map[k] != db_map[k]
                    },
                }
            )
        else:
            fail += 1
            mismatches.append(
                {
                    "week_start": week_start,
                    "only_raw": sorted(raw_set - db_set),
                    "only_db": sorted(db_set - raw_set),
                }
            )
    db_weeks = {
        r[0] for r in conn.execute("SELECT DISTINCT week_start FROM weekly_trending")
    }
    raw_weeks = {f.stem for f in files}
    return {
        "raw_files": len(files),
        "db_weeks": len(db_weeks),
        "only_db_weeks": sorted(db_weeks - raw_weeks),
        "checked": len(files),
        "ok": ok,
        "partial": partial,
        "fail": fail,
        "mismatches": mismatches,
    }


def reconcile_monthly(conn: sqlite3.Connection, raw_dir: Path) -> dict[str, Any]:
    files = sorted(raw_dir.glob("*.json")) if raw_dir.is_dir() else []
    ok = partial = fail = 0
    mismatches: list[dict[str, Any]] = []
    for f in files:
        data = load_json(f)
        month = data.get("month") or data.get("date") or f.stem
        if len(month) > 7:
            month = month[:7]
        raw_map = {}
        for p in data.get("projects") or []:
            repo = (p.get("repo") or "").strip()
            if not repo:
                continue
            raw_map[repo] = int(p.get("stars_this_period") or 0)
        # table may not exist yet
        try:
            db_rows = conn.execute(
                "SELECT repo_full_name, stars_this_period FROM monthly_trending WHERE month=?",
                (month,),
            ).fetchall()
        except sqlite3.OperationalError as e:
            return {
                "error": str(e),
                "raw_files": len(files),
                "ok": 0,
                "partial": 0,
                "fail": len(files),
            }
        db_map = {r[0]: int(r[1] or 0) for r in db_rows}
        raw_set, db_set = set(raw_map), set(db_map)
        if raw_set == db_set and all(raw_map[k] == db_map[k] for k in raw_set):
            ok += 1
        elif raw_set & db_set:
            partial += 1
            mismatches.append(
                {
                    "month": month,
                    "only_raw": sorted(raw_set - db_set),
                    "only_db": sorted(db_set - raw_set),
                    "stars_diff": {
                        k: {"raw": raw_map[k], "db": db_map[k]}
                        for k in sorted(raw_set & db_set)
                        if raw_map[k] != db_map[k]
                    },
                }
            )
        else:
            fail += 1
            mismatches.append(
                {
                    "month": month,
                    "only_raw": sorted(raw_set - db_set),
                    "only_db": sorted(db_set - raw_set),
                }
            )
    try:
        db_months = {
            r[0] for r in conn.execute("SELECT DISTINCT month FROM monthly_trending")
        }
    except sqlite3.OperationalError:
        db_months = set()
    raw_months = {(load_json(f).get("month") or f.stem)[:7] for f in files}
    return {
        "raw_files": len(files),
        "db_months": len(db_months),
        "only_db_months": sorted(db_months - raw_months),
        "checked": len(files),
        "ok": ok,
        "partial": partial,
        "fail": fail,
        "mismatches": mismatches,
    }


def row_counts(conn: sqlite3.Connection) -> dict[str, int]:
    out = {}
    for t in ("trending_daily", "weekly_trending", "monthly_trending", "repo_stats"):
        try:
            out[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except sqlite3.OperationalError:
            out[t] = -1
    return out


def main(argv: list[str] | None = None) -> int:
    base = resolve_base()
    p = argparse.ArgumentParser(description="Reconcile github_trending.db vs raw")
    p.add_argument("--db", default=os.path.join(base, "data", "github_trending.db"))
    p.add_argument("--raw-root", default=os.path.join(base, "raw"))
    p.add_argument("--window", type=int, default=14, help="Daily near-window days (0=all)")
    p.add_argument("--out", help="Write JSON report to path")
    args = p.parse_args(argv)

    if not os.path.exists(args.db):
        print(f"DB 不存在: {args.db}", file=sys.stderr)
        return 2

    raw = Path(args.raw_root)
    window = None if args.window == 0 else args.window
    conn = sqlite3.connect(args.db)
    try:
        report = {
            "db": args.db,
            "raw_root": args.raw_root,
            "window_days": window,
            "counts": row_counts(conn),
            "daily": reconcile_daily(conn, raw / "trending", window),
            "weekly": reconcile_weekly(conn, raw / "trending-weekly"),
            "monthly": reconcile_monthly(conn, raw / "trending-monthly"),
        }
    finally:
        conn.close()

    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)

    d, w, m = report["daily"], report["weekly"], report["monthly"]
    bad = (d["fail"] + d["partial"] + w["fail"] + w["partial"] + m.get("fail", 0) + m.get("partial", 0))
    # only_raw dates are failures for coverage
    if d.get("only_raw_dates"):
        bad += len(d["only_raw_dates"])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
