#!/usr/bin/env python3
"""
GitHub Trending 采集脚本 v2
走 sing-box 代理抓取 GitHub Trending 页面，解析项目列表，写入 SQLite + raw JSON。

用法：
  python3 github_trending_collector.py              # 正常采集
  python3 github_trending_collector.py --dry-run    # 只抓取解析，不写数据库/JSON

修复记录 (v2):
  - #1 重复运行去重：先检查今天是否已采集，已采集则跳过 repo_stats 递增
  - #2 curl 输出解析：strip 后再 split，防止换行干扰
  - #3 wiki_page/wiki_updated：采集脚本不写（由 cron agent 编译后写入）
  - #4 连续天数：查询最近上榜日期而非仅查昨天
  - #5 HTML 实体转义：处理 &amp; &lt; &gt; &quot; 等
  - #6 repo 路径校验：必须匹配 owner/repo 格式
  - #7 最小项目数检查：< 5 个项目则报警并保存 debug HTML
  - #8 注释清理
  - #9 dry-run 不写 JSON
  - #10 日志文件支持
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
    """从 .env 文件加载配置"""
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

# ========== 配置（从环境变量读取）==========
PROXY = os.environ.get("GITHUB_TRENDING_PROXY", "http://127.0.0.1:7890")
TRENDING_URL = os.environ.get("GITHUB_TRENDING_URL", "https://github.com/trending")
WIKI_PATH = os.environ.get("GITHUB_TRENDING_WIKI_PATH", "/srv/www/github-trending-wiki")
DB_PATH = os.path.join(WIKI_PATH, "data", "github_trending.db")
RAW_DIR = os.path.join(WIKI_PATH, "raw", "trending")
DEBUG_DIR = os.path.join(RAW_DIR, "debug")
LOG_DIR = os.path.join(WIKI_PATH, "logs")
MAX_RETRIES = int(os.environ.get("GITHUB_TRENDING_MAX_RETRIES", "3"))
RETRY_DELAY = int(os.environ.get("GITHUB_TRENDING_RETRY_DELAY", "5"))
TIMEOUT = int(os.environ.get("GITHUB_TRENDING_TIMEOUT", "30"))
MIN_PROJECTS = int(os.environ.get("GITHUB_TRENDING_MIN_PROJECTS", "5"))


# ========== 日志 ==========
def setup_logging():
    """配置日志：同时输出到 stdout 和文件"""
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, f"collector-{datetime.now().strftime('%Y-%m')}.log")

    logger = logging.getLogger("github_trending")
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")

    # stdout
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    # 文件（按月轮转）
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


log = setup_logging()


# ========== 重试 ==========
def retry(fn, max_attempts=MAX_RETRIES, delay=RETRY_DELAY):
    """重试包装器，指数退避"""
    def wrapper(*args, **kwargs):
        last_err = None
        for attempt in range(1, max_attempts + 1):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last_err = e
                if attempt < max_attempts:
                    wait = delay * (2 ** (attempt - 1))
                    log.warning(f"尝试 {attempt}/{max_attempts} 失败: {e}，{wait}s 后重试...")
                    time.sleep(wait)
        raise last_err
    return wrapper


# ========== 采集 ==========
def fetch_trending_html():
    """走代理抓取 GitHub Trending 页面"""
    log.info(f"抓取 {TRENDING_URL} (proxy={PROXY})")

    result = subprocess.run(
        ['curl', '-s', '--proxy', PROXY, '--connect-timeout', '15',
         '-o', '-', '-w', '\n%{http_code}', TRENDING_URL],
        capture_output=True, text=True, timeout=TIMEOUT
    )

    if result.returncode != 0:
        raise RuntimeError(f"curl 失败: returncode={result.returncode}, stderr={result.stderr}")

    # Fix #2: strip 后再 split，防止末尾换行干扰
    output = result.stdout.strip()
    parts = output.rsplit('\n', 1)
    if len(parts) < 2:
        raise RuntimeError("curl 输出格式异常，无法提取 HTTP 状态码")

    html_content = parts[0]
    http_code = parts[1].strip()

    if http_code != '200':
        raise RuntimeError(f"HTTP {http_code}，非 200 响应")

    if len(html_content) < 10000:
        raise RuntimeError(f"HTML 内容过短 ({len(html_content)} bytes)，可能被拦截")

    log.info(f"抓取成功，HTML 大小: {len(html_content)} bytes")
    return html_content


# ========== 解析 ==========
def unescape_html(text):
    """转义 HTML 实体（Fix #5）"""
    return html_lib.unescape(text)


def validate_repo_name(repo_name):
    """校验 repo 路径格式（Fix #6）：必须是 owner/repo"""
    if not repo_name:
        return False
    parts = repo_name.split('/')
    if len(parts) != 2:
        return False
    owner, name = parts
    # GitHub 用户名/仓库名规则：字母数字连字符，不能以连字符开头/结尾
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$'
    return bool(re.match(pattern, owner)) and bool(re.match(pattern, name))


def parse_trending(html_content):
    """解析 GitHub Trending HTML，提取项目列表"""
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
    """解析单个 article 元素"""
    # 提取 repo full name
    repo_match = re.search(r'<h2[^>]*>.*?<a[^>]*href="/([^"]+)"', article, re.DOTALL)
    if not repo_match:
        return None
    repo_full_name = repo_match.group(1).strip()

    # Fix #6: 校验 repo 路径格式
    if not validate_repo_name(repo_full_name):
        log.warning(f"跳过无效 repo 路径: {repo_full_name}")
        return None

    # 提取描述 + Fix #5: HTML 实体转义
    desc_match = re.search(r'<p class="col-9[^"]*"[^>]*>\s*(.*?)\s*</p>', article, re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else ""
    description = re.sub(r'<[^>]+>', '', description).strip()
    description = unescape_html(description)

    # 提取语言
    lang_match = re.search(r'itemprop="programmingLanguage"[^>]*>([^<]+)<', article)
    language = lang_match.group(1).strip() if lang_match else ""

    # 提取总 star 数
    star_match = re.search(
        r'<a[^>]*href="/' + re.escape(repo_full_name) + r'/stargazers"[^>]*>.*?([0-9,]+)\s*</a>',
        article, re.DOTALL
    )
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


# ========== 存储 ==========
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

    log.info(f"原始数据已保存: {filepath}")
    return filepath


def save_debug_html(html_content, date_str):
    """保存调试用 HTML"""
    os.makedirs(DEBUG_DIR, exist_ok=True)
    filepath = os.path.join(DEBUG_DIR, f"{date_str}.html")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    log.info(f"调试 HTML 已保存: {filepath}")


def save_to_db(projects, date_str, period='daily'):
    """写入 SQLite 数据库（Fix #1: 去重；Fix #4: 连续天数改进）"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()

    # Fix #1: 检查今天是否已采集过这些项目
    cursor.execute(
        "SELECT repo_full_name FROM trending_daily WHERE date=? AND period=?",
        (date_str, period)
    )
    already_scraped = {row[0] for row in cursor.fetchall()}
    is_first_run_today = len(already_scraped) == 0

    if already_scraped:
        log.warning(f"今天已采集过 {len(already_scraped)} 个项目，将跳过 repo_stats 递增")

    try:
        for p in projects:
            # trending_daily: INSERT OR REPLACE（始终更新为最新数据）
            cursor.execute("""
                INSERT OR REPLACE INTO trending_daily
                (date, period, repo_full_name, rank, description, language, stars_today, total_stars, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (date_str, period, p['repo'], p['rank'], p['description'],
                  p['language'], p['stars_today'], p['total_stars'], p['url']))

            # Fix #1: 只有首次运行时才递增 repo_stats
            if p['repo'] in already_scraped:
                # 已采集过，只更新描述和 star 数据，不递增 count
                cursor.execute("""
                    UPDATE repo_stats SET
                        description=?, language=?, last_stars=?
                    WHERE repo_full_name=?
                """, (p['description'], p['language'], p['total_stars'], p['repo']))
                continue

            # Fix #4: 查询最近一次上榜日期（而非仅查昨天）
            cursor.execute("""
                SELECT date FROM trending_daily
                WHERE repo_full_name=? AND period=? AND date != ?
                ORDER BY date DESC LIMIT 1
            """, (p['repo'], period, date_str))
            last_seen_row = cursor.fetchone()

            # 查询现有 stats
            cursor.execute(
                "SELECT consecutive_days, max_consecutive_days, peak_rank, max_stars_today FROM repo_stats WHERE repo_full_name=?",
                (p['repo'],)
            )
            existing = cursor.fetchone()

            if existing:
                # 判断是否连续：最近一次上榜是否在昨天或前天（允许1天间隔）
                if last_seen_row:
                    last_date = datetime.strptime(last_seen_row[0], "%Y-%m-%d")
                    today = datetime.strptime(date_str, "%Y-%m-%d")
                    gap = (today - last_date).days
                    consec = existing[0] + 1 if gap <= 1 else 1
                else:
                    consec = 1

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
                # 新项目
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
        log.info(f"数据库写入成功: {len(projects)} 条记录 (首次运行: {is_first_run_today})")

    except Exception as e:
        conn.rollback()
        log.error(f"数据库写入失败，已回滚: {e}")
        raise
    finally:
        conn.close()


# ========== 主函数 ==========
def main():
    dry_run = '--dry-run' in sys.argv
    date_str = datetime.now().strftime("%Y-%m-%d")

    log.info(f"=== GitHub Trending 采集开始 ({date_str}) ===")
    if dry_run:
        log.info(">>> DRY-RUN 模式，不写数据库/JSON <<<")

    # 1. 抓取 HTML（带重试）
    try:
        html_content = retry(fetch_trending_html)()
    except Exception as e:
        log.error(f"抓取失败，已重试 {MAX_RETRIES} 次: {e}")
        sys.exit(1)

    # 2. 解析项目
    projects = parse_trending(html_content)
    if not projects:
        log.error("未解析到任何项目")
        save_debug_html(html_content, date_str)
        sys.exit(1)

    # Fix #7: 最小项目数检查
    if len(projects) < MIN_PROJECTS:
        log.warning(f"⚠️ 项目数量异常：仅 {len(projects)} 个（预期 ≥{MIN_PROJECTS}），GitHub 页面可能改版")
        save_debug_html(html_content, date_str)

    # 3. 保存原始 JSON（Fix #9: dry-run 不写）
    if not dry_run:
        save_raw_json(projects, date_str)
    else:
        log.info("DRY-RUN: 跳过 JSON 保存")

    # 4. 写入数据库
    if not dry_run:
        save_to_db(projects, date_str)
    else:
        log.info("DRY-RUN: 跳过数据库写入")
        for p in projects[:5]:
            log.info(f"  #{p['rank']} {p['repo']} ⭐{p['total_stars']}(+{p['stars_today']}) [{p['language']}]")

    log.info(f"=== 采集完成: {len(projects)} 个项目 ===")


if __name__ == "__main__":
    main()
