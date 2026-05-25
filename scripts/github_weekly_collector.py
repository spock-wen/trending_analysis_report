#!/usr/bin/env python3
"""
GitHub Trending 周榜采集脚本
每周日爬取 GitHub Trending ?since=weekly 页面，写入 weekly_trending 表。

用法：
  python3 github_weekly_collector.py              # 正常采集
  python3 github_weekly_collector.py --dry-run    # 只抓取解析，不写 DB
"""

import html as html_lib
import json
import logging
import os
import re
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta

# ========== 配置 ==========
def load_env():
    env_paths = [
        os.path.join(os.path.dirname(__file__), '..', '.env'),
        os.path.join(os.path.dirname(__file__), '.env'),
    ]
    for env_path in env_paths:
        env_path = os.path.abspath(env_path)
        if os.path.exists(env_path):
            with open(env_path, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, _, value = line.partition('=')
                        os.environ.setdefault(key.strip(), value.strip())
            break

load_env()

PROXY = os.environ.get("GITHUB_TRENDING_PROXY", "http://127.0.0.1:7890")
WEEKLY_URL = os.environ.get("GITHUB_WEEKLY_URL", "https://github.com/trending?since=weekly")
WIKI_PATH = os.environ.get("GITHUB_TRENDING_WIKI_PATH", "/srv/www/github-trending-wiki")
DB_PATH = os.path.join(WIKI_PATH, "data", "github_trending.db")
LOG_DIR = os.path.join(WIKI_PATH, "logs")
MAX_RETRIES = int(os.environ.get("GITHUB_TRENDING_MAX_RETRIES", "3"))
RETRY_DELAY = int(os.environ.get("GITHUB_TRENDING_RETRY_DELAY", "5"))
TIMEOUT = int(os.environ.get("GITHUB_TRENDING_TIMEOUT", "30"))
MIN_PROJECTS = int(os.environ.get("GITHUB_TRENDING_MIN_PROJECTS", "5"))

# ========== 日志 ==========
def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, f"weekly-collector-{datetime.now().strftime('%Y-%m')}.log")
    logger = logging.getLogger("github_weekly")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger

log = setup_logging()

# ========== 日期工具 ==========
def get_week_range():
    """返回本周一和本周日的日期字符串"""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")

# ========== 采集 ==========
def fetch_weekly_html():
    log.info(f"抓取周榜 {WEEKLY_URL} (proxy={PROXY})")
    result = subprocess.run(
        ['curl', '-s', '--proxy', PROXY, '--connect-timeout', '15',
         '-o', '-', '-w', '\n%{http_code}', WEEKLY_URL],
        capture_output=True, text=True, timeout=TIMEOUT
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl 失败: returncode={result.returncode}, stderr={result.stderr}")
    output = result.stdout.strip()
    parts = output.rsplit('\n', 1)
    if len(parts) < 2:
        raise RuntimeError("curl 输出格式异常")
    html_content = parts[0]
    http_code = parts[1].strip()
    if http_code != '200':
        raise RuntimeError(f"HTTP {http_code}")
    if len(html_content) < 10000:
        raise RuntimeError(f"HTML 过短 ({len(html_content)} bytes)")
    log.info(f"抓取成功，HTML 大小: {len(html_content)} bytes")
    return html_content

# ========== 解析 ==========
def unescape_html(text):
    return html_lib.unescape(text)

def validate_repo_name(repo_name):
    if not repo_name:
        return False
    parts = repo_name.split('/')
    if len(parts) != 2:
        return False
    owner, name = parts
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$'
    return bool(re.match(pattern, owner)) and bool(re.match(pattern, name))

def parse_weekly(html_content):
    projects = []
    articles = re.findall(
        r'<article class="Box-row">(.*?)</article>',
        html_content, re.DOTALL
    )
    for i, article in enumerate(articles, 1):
        try:
            project = parse_single_article(article, rank=i)
            if project:
                projects.append(project)
        except Exception as e:
            log.warning(f"解析第 {i} 个项目失败: {e}")
            continue
    log.info(f"解析到 {len(projects)} 个项目")
    return projects

def parse_single_article(article, rank):
    # repo full name
    repo_match = re.search(r'<h2[^>]*>.*?<a[^>]*href="/([^"]+)"', article, re.DOTALL)
    if not repo_match:
        return None
    repo_full_name = repo_match.group(1).strip()
    if not validate_repo_name(repo_full_name):
        log.warning(f"跳过无效 repo: {repo_full_name}")
        return None

    # 描述
    desc_match = re.search(r'<p class="col-9[^"]*"[^>]*>\s*(.*?)\s*</p>', article, re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else ""
    description = re.sub(r'<[^>]+>', '', description).strip()
    description = unescape_html(description)

    # 语言
    lang_match = re.search(r'itemprop="programmingLanguage"[^>]*>([^<]+)<', article)
    language = lang_match.group(1).strip() if lang_match else ""

    # 本周 star 数（GitHub 周榜显示 "X stars this week"）
    weekly_match = re.search(r'([\d,]+)\s+stars?\s+this\s+week', article)
    weekly_stars = 0
    if weekly_match:
        weekly_stars = int(weekly_match.group(1).replace(',', ''))

    return {
        "rank": rank,
        "repo": repo_full_name,
        "description": description,
        "language": language,
        "weekly_stars": weekly_stars,
        "url": f"https://github.com/{repo_full_name}"
    }

# ========== 写入 DB ==========
def write_to_db(projects, week_start, week_end):
    conn = sqlite3.connect(DB_PATH)
    # 幂等：先删除本周已有数据
    conn.execute("DELETE FROM weekly_trending WHERE week_start = ?", (week_start,))
    # 批量插入
    for p in projects:
        conn.execute(
            "INSERT OR REPLACE INTO weekly_trending "
            "(week_start, week_end, repo_full_name, rank, weekly_stars, description, language) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (week_start, week_end, p["repo"], p["rank"], p["weekly_stars"],
             p["description"], p["language"])
        )
    conn.commit()
    conn.close()
    log.info(f"写入 DB: {len(projects)} 个项目 (week: {week_start} ~ {week_end})")

# ========== 主流程 ==========
def main():
    dry_run = "--dry-run" in sys.argv

    week_start, week_end = get_week_range()
    log.info(f"周报周期: {week_start} ~ {week_end}")

    html = fetch_weekly_html()
    projects = parse_weekly(html)

    if len(projects) < MIN_PROJECTS:
        # 保存 debug HTML
        debug_dir = os.path.join(os.path.dirname(DB_PATH), "..", "raw", "debug")
        os.makedirs(debug_dir, exist_ok=True)
        debug_file = os.path.join(debug_dir, f"weekly-debug-{week_start}.html")
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(html)
        log.warning(f"项目数不足 {MIN_PROJECTS}，debug HTML 已保存到 {debug_file}")

    if dry_run:
        print("\n=== DRY RUN ===")
        print(json.dumps(projects, ensure_ascii=False, indent=2))
        print(f"\n共 {len(projects)} 个项目，未写入 DB")
        return

    write_to_db(projects, week_start, week_end)

    # 打印摘要
    total_stars = sum(p["weekly_stars"] for p in projects)
    print(f"\n周报采集完成: {len(projects)} 个项目, 总周 star: {total_stars:,}")
    for p in projects[:5]:
        print(f"  #{p['rank']} {p['repo']} - +{p['weekly_stars']:,} stars [{p['language']}]")

if __name__ == '__main__':
    main()
