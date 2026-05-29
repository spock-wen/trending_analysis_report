#!/usr/bin/env python3
"""
GitHub Trending Wiki — 每日信号计算脚本

在 wiki_daily.py 采集完成后运行，读取 SQLite 数据库，
计算各类趋势信号指标，输出 JSON 供 LLM 日报生成使用。

输出：raw/signals/YYYY-MM-DD.json
"""

import json
import os
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "github_trending.db")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "raw", "signals")
DATE_FORMAT = "%Y-%m-%d"

# 领域分类关键词规则
CATEGORY_RULES = {
    "agent-skills": [
        "skill", "agent", "claude code", "codex", "cursor", "copilot",
        "gemini cli", "harness", "superpowers", "plugin",
    ],
    "ai-video-audio": [
        "video", "tts", "audio", "voice", "speech", "sound",
        "moneyprinter",
    ],
    "code-visualization": [
        "codegraph", "understand", "knowledge graph", "interactive",
        "knowledge", "graph",
    ],
    "web-infra": [
        "crawl", "scrape", "markitdown", "markdown", "domain",
    ],
    "open-source-alt": [
        "salesforce", "alternative", "twenty",
    ],
    "education": [
        "learn", "tutorial", "guide", "english", "build-your-own",
        "from scratch",
    ],
    "ai-quality": [
        "slop", "taste", "quality", "stop",
    ],
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_today_date():
    """获取最近的完整采集日数据（取最大日期）"""
    conn = get_db()
    row = conn.execute("SELECT MAX(date) as max_date FROM trending_daily").fetchone()
    conn.close()
    return row["max_date"] if row else None


def get_week_range(date_str):
    """获取 date_str 所在周的周一~周日"""
    d = datetime.strptime(date_str, DATE_FORMAT)
    monday = d - timedelta(days=d.weekday())
    return monday.strftime(DATE_FORMAT), (monday + timedelta(days=6)).strftime(DATE_FORMAT)


def calc_project_count(conn, today_str):
    """今日/昨日/上周同期项目数"""
    yesterday = (datetime.strptime(today_str, DATE_FORMAT) - timedelta(days=1)).strftime(DATE_FORMAT)
    last_week = (datetime.strptime(today_str, DATE_FORMAT) - timedelta(days=7)).strftime(DATE_FORMAT)

    today_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM trending_daily WHERE date=?", (today_str,)
    ).fetchone()["cnt"]

    yesterday_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM trending_daily WHERE date=?", (yesterday,)
    ).fetchone()["cnt"]

    last_week_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM trending_daily WHERE date=?", (last_week,)
    ).fetchone()["cnt"]

    return {
        "today": today_count,
        "yesterday": yesterday_count,
        "last_week_same": last_week_count,
    }


def calc_total_stars(conn, today_str):
    """今日总 star 增长"""
    row = conn.execute(
        "SELECT COALESCE(SUM(stars_today), 0) as total FROM trending_daily WHERE date=?", (today_str,)
    ).fetchone()

    yesterday = (datetime.strptime(today_str, DATE_FORMAT) - timedelta(days=1)).strftime(DATE_FORMAT)
    row_y = conn.execute(
        "SELECT COALESCE(SUM(stars_today), 0) as total FROM trending_daily WHERE date=?", (yesterday,)
    ).fetchone()

    last_week = (datetime.strptime(today_str, DATE_FORMAT) - timedelta(days=7)).strftime(DATE_FORMAT)
    row_lw = conn.execute(
        "SELECT COALESCE(SUM(stars_today), 0) as total FROM trending_daily WHERE date=?", (last_week,)
    ).fetchone()

    return {
        "today": row["total"],
        "yesterday": row_y["total"],
        "last_week_same": row_lw["total"],
    }


def calc_language_share(conn, today_str):
    """今日语言分布，并与上周同期对比"""
    rows = conn.execute(
        "SELECT language, COUNT(*) as cnt FROM trending_daily WHERE date=? GROUP BY language ORDER BY cnt DESC",
        (today_str,),
    ).fetchall()
    total = sum(r["cnt"] for r in rows)

    last_week = (datetime.strptime(today_str, DATE_FORMAT) - timedelta(days=7)).strftime(DATE_FORMAT)
    rows_lw = conn.execute(
        "SELECT language, COUNT(*) as cnt FROM trending_daily WHERE date=? GROUP BY language ORDER BY cnt DESC",
        (last_week,),
    ).fetchall()
    total_lw = sum(r["cnt"] for r in rows_lw)
    lw_map = {r["language"]: r["cnt"] for r in rows_lw}

    result = []
    for r in rows:
        lang = r["language"] if r["language"] else "未标注"
        share = round(r["cnt"] / total * 100) if total else 0
        lw_cnt = lw_map.get(r["language"], 0)
        lw_share = round(lw_cnt / total_lw * 100) if total_lw else 0
        if lw_share > 0:
            change = share - lw_share
            trend = "up" if change > 3 else ("down" if change < -3 else "flat")
        else:
            trend = "new"
        result.append({
            "lang": lang,
            "today": r["cnt"],
            "share": f"{share}%",
            "last_week_share": f"{lw_share}%",
            "trend": trend,
        })
    return result


def classify_category(repo_name, description):
    """根据仓库名和描述匹配领域分类"""
    text = f"{repo_name} {description or ''}".lower()
    matched = []
    for category, keywords in CATEGORY_RULES.items():
        for kw in keywords:
            if kw.lower() in text:
                matched.append(category)
                break
    return matched if matched else ["other"]


def calc_category_heat(conn, today_str):
    """领域聚类热度：今日 vs 过去7天日均"""
    today = datetime.strptime(today_str, DATE_FORMAT)
    seven_days_ago = (today - timedelta(days=6)).strftime(DATE_FORMAT)

    # 获取今日项目
    today_rows = conn.execute(
        "SELECT repo_full_name, description FROM trending_daily WHERE date=?", (today_str,)
    ).fetchall()

    # 获取过去7天项目
    week_rows = conn.execute(
        "SELECT date, repo_full_name, description FROM trending_daily WHERE date >= ? AND date <= ?",
        (seven_days_ago, today_str),
    ).fetchall()

    # 今日分类统计
    today_cats = defaultdict(int)
    for r in today_rows:
        cats = classify_category(r["repo_full_name"], r["description"])
        for c in cats:
            today_cats[c] += 1

    # 过去7天分类统计
    week_cats = defaultdict(list)
    for r in week_rows:
        cats = classify_category(r["repo_full_name"], r["description"])
        for c in cats:
            week_cats[c].append(r["date"])

    week_avg = {}
    for c, dates in week_cats.items():
        unique_dates = len(set(dates))
        week_avg[c] = round(len(dates) / max(unique_dates, 1), 1)

    # 计算趋势
    all_cats = set(list(today_cats.keys()) + list(week_cats.keys()))
    result = []
    for c in sorted(all_cats):
        today_val = today_cats.get(c, 0)
        avg_val = week_avg.get(c, 0)
        if avg_val > 0:
            change_pct = round((today_val - avg_val) / avg_val * 100)
            trend = "up" if change_pct > 20 else ("down" if change_pct < -20 else "flat")
        else:
            change_pct = 0
            trend = "new"
        result.append({
            "category": c,
            "today": today_val,
            "7d_avg": avg_val,
            "change_pct": change_pct,
            "trend": trend,
        })
    return result


def calc_newcomer_ratio(conn, today_str):
    """首次上榜项目占比"""
    all_today = conn.execute(
        "SELECT repo_full_name FROM trending_daily WHERE date=?", (today_str,)
    ).fetchall()

    first_timers = []
    for r in all_today:
        first_seen = conn.execute(
            "SELECT MIN(date) as first FROM trending_daily WHERE repo_full_name=?", (r["repo_full_name"],)
        ).fetchone()["first"]
        if first_seen == today_str:
            first_timers.append(r["repo_full_name"])

    # 过去7天新人占比均值
    today = datetime.strptime(today_str, DATE_FORMAT)
    seven_days_ago = (today - timedelta(days=6)).strftime(DATE_FORMAT)
    days = conn.execute(
        "SELECT DISTINCT date FROM trending_daily WHERE date >= ? AND date <= ? ORDER BY date",
        (seven_days_ago, today_str),
    ).fetchall()

    ratios = []
    for d in days:
        d_str = d["date"]
        all_d = conn.execute(
            "SELECT repo_full_name FROM trending_daily WHERE date=?", (d_str,)
        ).fetchall()
        first_d = 0
        for rd in all_d:
            fs = conn.execute(
                "SELECT MIN(date) as first FROM trending_daily WHERE repo_full_name=?",
                (rd["repo_full_name"],),
            ).fetchone()["first"]
            if fs == d_str:
                first_d += 1
        ratios.append(round(first_d / max(len(all_d), 1), 2))

    avg_ratio = round(sum(ratios) / max(len(ratios), 1), 2)

    return {
        "first_timers": len(first_timers),
        "total": len(all_today),
        "ratio": f"{round(len(first_timers) / max(len(all_today), 1) * 100)}%",
        "7d_avg_ratio": f"{round(avg_ratio * 100)}%",
        "first_timer_list": first_timers,
    }


def calc_accelerating(conn, today_str):
    """加速项目：连续3天+且最近一天星数 >= 过去3天均值*0.7"""
    rows = conn.execute(
        "SELECT repo_full_name, consecutive_days, max_stars_today FROM repo_stats "
        "WHERE consecutive_days >= 3 ORDER BY consecutive_days DESC"
    ).fetchall()

    result = []
    for r in rows:
        # 获取最近3天的星星数据
        recent = conn.execute(
            "SELECT date, stars_today FROM trending_daily "
            "WHERE repo_full_name=? ORDER BY date DESC LIMIT 3",
            (r["repo_full_name"],),
        ).fetchall()
        if len(recent) < 2:
            continue
        latest = recent[0]["stars_today"]
        prev_avg = sum(x["stars_today"] for x in recent[1:]) / max(len(recent) - 1, 1)

        if latest >= prev_avg * 0.7:
            trend = "up" if latest > prev_avg * 1.1 else "stable"
            result.append({
                "repo": r["repo_full_name"],
                "days": r["consecutive_days"],
                "latest_stars": latest,
                "prev_avg": round(prev_avg),
                "trend": trend,
            })
    return result


def calc_decelerating(conn, today_str):
    """减速项目：连续3天+且最新星数显著下降"""
    rows = conn.execute(
        "SELECT repo_full_name, consecutive_days FROM repo_stats "
        "WHERE consecutive_days >= 3 ORDER BY consecutive_days DESC"
    ).fetchall()

    result = []
    for r in rows:
        recent = conn.execute(
            "SELECT date, stars_today FROM trending_daily "
            "WHERE repo_full_name=? ORDER BY date DESC LIMIT 3",
            (r["repo_full_name"],),
        ).fetchall()
        if len(recent) < 2:
            continue
        latest = recent[0]["stars_today"]
        prev_avg = sum(x["stars_today"] for x in recent[1:]) / max(len(recent) - 1, 1)

        if latest < prev_avg * 0.4:
            # 找峰值
            peak = conn.execute(
                "SELECT MAX(stars_today) as peak FROM trending_daily WHERE repo_full_name=?",
                (r["repo_full_name"],),
            ).fetchone()["peak"]
            result.append({
                "repo": r["repo_full_name"],
                "days": r["consecutive_days"],
                "latest_stars": latest,
                "peak_stars": peak,
                "drop_pct": round((1 - latest / max(peak, 1)) * 100),
            })
    return result


def calc_dark_horse(conn, today_str):
    """黑马：今日新上榜且单日星数 >= 1000"""
    all_today = conn.execute(
        "SELECT repo_full_name, stars_today FROM trending_daily WHERE date=? ORDER BY stars_today DESC",
        (today_str,),
    ).fetchall()

    result = []
    for r in all_today:
        first_seen = conn.execute(
            "SELECT MIN(date) as first FROM trending_daily WHERE repo_full_name=?",
            (r["repo_full_name"],),
        ).fetchone()["first"]
        if first_seen == today_str and r["stars_today"] >= 500:
            result.append({
                "repo": r["repo_full_name"],
                "stars": r["stars_today"],
            })
    return result


def calc_consecutive_trend(conn, today_str):
    """连续上榜项目的整体趋势：总数变化"""
    conn_rs = conn.execute(
        "SELECT COUNT(*) as cnt FROM repo_stats WHERE consecutive_days >= 2"
    ).fetchone()["cnt"]

    yesterday = (datetime.strptime(today_str, DATE_FORMAT) - timedelta(days=1)).strftime(DATE_FORMAT)
    # 昨日的连续上榜数据不是直接可查的，用 trending_daily 反推
    # 简单方式：查昨天还在榜且 repo_stats 中连续>=2的项目
    yesterday_sustained = conn.execute(
        "SELECT COUNT(*) as cnt FROM trending_daily td "
        "JOIN repo_stats rs ON td.repo_full_name = rs.repo_full_name "
        "WHERE td.date=? AND rs.consecutive_days >= 2",
        (yesterday,),
    ).fetchone()["cnt"]

    return {
        "total_sustained": conn_rs,
        "yesterday_sustained": yesterday_sustained,
    }


def main():
    today_str = get_today_date()
    if not today_str:
        print(json.dumps({"error": "No data found in database"}, ensure_ascii=False))
        return

    conn = get_db()

    signals = {
        "date": today_str,
        "project_count": calc_project_count(conn, today_str),
        "total_stars": calc_total_stars(conn, today_str),
        "language_share": calc_language_share(conn, today_str),
        "category_heat": calc_category_heat(conn, today_str),
        "newcomer_ratio": calc_newcomer_ratio(conn, today_str),
        "accelerating": calc_accelerating(conn, today_str),
        "decelerating": calc_decelerating(conn, today_str),
        "dark_horse": calc_dark_horse(conn, today_str),
        "consecutive_trend": calc_consecutive_trend(conn, today_str),
    }

    conn.close()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"{today_str}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(signals, f, ensure_ascii=False, indent=2)

    print(json.dumps(signals, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
