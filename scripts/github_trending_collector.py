#!/usr/bin/env python3
"""
GitHub Trending 采集脚本
走 sing-box 代理抓取 GitHub Trending 页面，解析项目列表，写入 SQLite + raw JSON。

用法：
  python3 github_trending_collector.py              # 正常采集
  python3 github_trending_collector.py --dry-run    # 只抓取解析，不写数据库
"""

import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# ========== 配置 ==========
PROXY = "http://127.0.0.1:7890"
TRENDING_URL = "https://github.com/trending"
WIKI_PATH = "/root/wiki/github"
DB_PATH = os.path.join(WIKI_PATH, "data", "github_trending.db")
RAW_DIR = os.path.join(WIKI_PATH, "raw", "trending")
DEBUG_DIR = os.path.join(RAW_DIR, "debug")
MAX_RETRIES = 3
RETRY_DELAY = 5
TIMEOUT = 30


def log(level, msg):
    """结构化日志输出"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")


def retry(fn, max_attempts=MAX_RETRIES, delay=RETRY_DELAY):
    """重试装饰器，指数退避"""
    def wrapper(*args, **kwargs):
        last_err = None
        for attempt in range(1, max_attempts + 1):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last_err = e
                if attempt < max_attempts:
                    wait = delay * (2 ** (attempt - 1))
                    log("WARN", f"尝试 {attempt}/{max_attempts} 失败: {e}，{wait}s 后重试...")
                    time.sleep(wait)
        raise last_err
    return wrapper


def fetch_trending_html():
    """走代理抓取 GitHub Trending 页面"""
    log("INFO", f"抓取 {TRENDING_URL} (proxy={PROXY})")

    result = subprocess.run(
        ['curl', '-s', '--proxy', PROXY, '--connect-timeout', '15',
         '-o', '-', '-w', '\n%{http_code}', TRENDING_URL],
        capture_output=True, text=True, timeout=TIMEOUT
    )

    if result.returncode != 0:
        raise RuntimeError(f"curl 失败: returncode={result.returncode}, stderr={result.stderr}")

    lines = result.stdout.rsplit('\n', 1)
    if len(lines) < 2:
        raise RuntimeError("curl 输出格式异常，无法提取 HTTP 状态码")

    html = lines[0]
    http_code = lines[1].strip()

    if http_code != '200':
        raise RuntimeError(f"HTTP {http_code}，非 200 响应")

    if len(html) < 10000:
        raise RuntimeError(f"HTML 内容过短 ({len(html)} bytes)，可能被拦截")

    log("INFO", f"抓取成功，HTML 大小: {len(html)} bytes")
    return html


def parse_trending(html):
    """解析 GitHub Trending HTML，提取项目列表"""
    projects = []

    # 用正则解析，比 BeautifulSoup 更轻量且不需额外依赖
    # 每个项目在一个 <article class="Box-row"> 中
    articles = re.findall(
        r'<article class="Box-row">(.*?)</article>',
        html, re.DOTALL
    )

    for i, article in enumerate(articles, 1):
        try:
            project = parse_single_article(article, rank=i)
            if project:
                projects.append(project)
        except Exception as e:
            log("WARN", f"解析第 {i} 个项目失败: {e}")
            continue

    log("INFO", f"解析到 {len(projects)} 个项目")
    return projects


def parse_single_article(article, rank):
    """解析单个 article 元素"""
    # 提取 repo full name: <a href="/owner/repo">
    repo_match = re.search(r'<h2[^>]*>.*?<a[^>]*href="/([^"]+)"', article, re.DOTALL)
    if not repo_match:
        return None
    repo_full_name = repo_match.group(1).strip()

    # 提取描述
    desc_match = re.search(r'<p class="col-9[^"]*"[^>]*>\s*(.*?)\s*</p>', article, re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else ""
    # 清理 HTML 标签
    description = re.sub(r'<[^>]+>', '', description).strip()

    # 提取语言
    lang_match = re.search(r'itemprop="programmingLanguage"[^>]*>([^<]+)<', article)
    language = lang_match.group(1).strip() if lang_match else ""

    # 提取总 star 数
    star_match = re.search(r'<a[^>]*href="/' + re.escape(repo_full_name) + r'/stargazers"[^>]*>.*?([0-9,]+)\s*</a>', article, re.DOTALL)
    total_stars = 0
    if star_match:
        total_stars = int(star_match.group(1).replace(',', ''))

    # 提取今日 star 数
    today_match = re.search(r'([\d,]+)\s+stars?\s+today', article)
    stars_today = 0
    if today_match:
        stars_today = int(today_match.group(1).replace(',', ''))

    return {
        "rank": rank,
        "repo": repo_full_name,
        "description": description,
        "language": language,
        "stars_today": stars_today,
        "total_stars": total_stars,
        "url": f"https://github.com/{repo_full_name}"
    }


def save_raw_json(projects, date_str):
    """保存原始 JSON 到 raw/trending/YYYY-MM-DD.json"""
    os.makedirs(RAW_DIR, exist_ok=True)
    filepath = os.path.join(RAW_DIR, f"{date_str}.json")

    data = {
        "date": date_str,
        "scraped_at": datetime.now().isoformat(),
        "period": "daily",
        "count": len(projects),
        "projects": projects
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    log("INFO", f"原始数据已保存: {filepath}")
    return filepath


def save_debug_html(html, date_str):
    """保存调试用 HTML"""
    os.makedirs(DEBUG_DIR, exist_ok=True)
    filepath = os.path.join(DEBUG_DIR, f"{date_str}.html")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    log("INFO", f"调试 HTML 已保存: {filepath}")


def save_to_db(projects, date_str, period='daily'):
    """写入 SQLite 数据库"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()

    try:
        for p in projects:
            # 写入 trending_daily
            cursor.execute("""
                INSERT OR REPLACE INTO trending_daily
                (date, period, repo_full_name, rank, description, language, stars_today, total_stars, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (date_str, period, p['repo'], p['rank'], p['description'],
                  p['language'], p['stars_today'], p['total_stars'], p['url']))

            # 更新 repo_stats
            yesterday = (datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")

            # 查询昨天是否上榜
            cursor.execute("""
                SELECT 1 FROM trending_daily
                WHERE repo_full_name=? AND date=? AND period=?
            """, (p['repo'], yesterday, period))
            was_trending_yesterday = cursor.fetchone() is not None

            # 查询现有 stats
            cursor.execute("SELECT consecutive_days, max_consecutive_days, peak_rank, max_stars_today FROM repo_stats WHERE repo_full_name=?",
                          (p['repo'],))
            existing = cursor.fetchone()

            if existing:
                consec = existing[0] + 1 if was_trending_yesterday else 1
                max_consec = max(existing[1], consec)
                peak_rank = min(existing[2], p['rank']) if existing[2] else p['rank']
                max_stars = max(existing[3], p['stars_today']) if existing[3] else p['stars_today']

                cursor.execute("""
                    UPDATE repo_stats SET
                        description=?, language=?, last_seen=?,
                        trending_count_daily=trending_count_daily+1,
                        consecutive_days=?, max_consecutive_days=?,
                        peak_rank=?, max_stars_today=?, last_stars=?
                    WHERE repo_full_name=?
                """, (p['description'], p['language'], date_str,
                      consec, max_consec, peak_rank, max_stars,
                      p['total_stars'], p['repo']))
            else:
                cursor.execute("""
                    INSERT INTO repo_stats
                    (repo_full_name, description, language, first_seen, last_seen,
                     trending_count_daily, trending_count_weekly, trending_count_monthly,
                     consecutive_days, max_consecutive_days, peak_rank, max_stars_today, last_stars)
                    VALUES (?, ?, ?, ?, ?, 1, 0, 0, 1, 1, ?, ?, ?)
                """, (p['repo'], p['description'], p['language'],
                      date_str, date_str, p['rank'],
                      p['stars_today'], p['total_stars']))

        conn.commit()
        log("INFO", f"数据库写入成功: {len(projects)} 条记录")

    except Exception as e:
        conn.rollback()
        log("ERROR", f"数据库写入失败，已回滚: {e}")
        raise
    finally:
        conn.close()


def main():
    dry_run = '--dry-run' in sys.argv
    date_str = datetime.now().strftime("%Y-%m-%d")

    log("INFO", f"=== GitHub Trending 采集开始 ({date_str}) ===")
    if dry_run:
        log("INFO", ">>> DRY-RUN 模式，不写数据库 <<<")

    # 1. 抓取 HTML（带重试）
    try:
        html = retry(fetch_trending_html)()
    except Exception as e:
        log("ERROR", f"抓取失败，已重试 {MAX_RETRIES} 次: {e}")
        sys.exit(1)

    # 2. 解析项目
    projects = parse_trending(html)
    if not projects:
        log("ERROR", "未解析到任何项目")
        save_debug_html(html, date_str)
        sys.exit(1)

    # 3. 保存原始 JSON
    save_raw_json(projects, date_str)

    # 4. 写入数据库
    if not dry_run:
        save_to_db(projects, date_str)
    else:
        log("INFO", "DRY-RUN: 跳过数据库写入")
        # 打印前 5 个项目
        for p in projects[:5]:
            log("INFO", f"  #{p['rank']} {p['repo']} ⭐{p['total_stars']}(+{p['stars_today']}) [{p['language']}]")

    log("INFO", f"=== 采集完成: {len(projects)} 个项目 ===")


if __name__ == "__main__":
    main()
