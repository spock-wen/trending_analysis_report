#!/usr/bin/env python3
"""
GitHub Trending 月榜采集脚本
抓取 github.com/trending?since=monthly，落 raw/trending-monthly/YYYY-MM.json。

仅落 raw（供 report 同源读榜）；不改 wiki 现有月叙事聚合（wiki_daily --month-report）。

用法：
  python3 github_monthly_collector.py              # 正常采集写 raw
  python3 github_monthly_collector.py --dry-run    # 只抓取解析，不写 raw
"""

import html as html_lib
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime

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
MONTHLY_URL = os.environ.get("GITHUB_MONTHLY_URL", "https://github.com/trending?since=monthly")
WIKI_PATH = os.environ.get("GITHUB_TRENDING_WIKI_PATH", "/srv/www/github-trending-wiki")
RAW_DIR = os.path.join(WIKI_PATH, "raw", "trending-monthly")
LOG_DIR = os.path.join(WIKI_PATH, "logs")
MAX_RETRIES = int(os.environ.get("GITHUB_TRENDING_MAX_RETRIES", "3"))
RETRY_DELAY = int(os.environ.get("GITHUB_TRENDING_RETRY_DELAY", "5"))
TIMEOUT = int(os.environ.get("GITHUB_TRENDING_TIMEOUT", "30"))
MIN_PROJECTS = int(os.environ.get("GITHUB_TRENDING_MIN_PROJECTS", "5"))

# ========== 日志 ==========
def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, f"monthly-collector-{datetime.now().strftime('%Y-%m')}.log")
    logger = logging.getLogger("github_monthly")
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

# ========== 日期 ==========
def get_month_key(now=None):
    """文件名与顶层 date：YYYY-MM（采集当时日历月）"""
    now = now or datetime.now()
    return now.strftime("%Y-%m")

# ========== 采集 ==========
def fetch_monthly_html():
    log.info(f"抓取月榜 {MONTHLY_URL} (proxy={PROXY})")
    result = subprocess.run(
        ['curl', '-s', '--proxy', PROXY, '--connect-timeout', '15',
         '-o', '-', '-w', '\n%{http_code}', MONTHLY_URL],
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
    """与日/周采集同一套 owner/repo 规则"""
    if not repo_name:
        return False
    parts = repo_name.split('/')
    if len(parts) != 2:
        return False
    owner, name = parts
    owner_pat = r'^[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\Z'
    name_pat = r'^[a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9._])?\Z'
    if bool(re.match(owner_pat, owner)) is False:
        return False
    if bool(re.match(name_pat, name)) is False:
        return False
    if '--' in owner:
        return False
    if name.endswith('.git'):
        return False
    if name in ('.', '..'):
        return False
    return True

def parse_monthly(html_content):
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
    repo_match = re.search(r'<h2[^>]*>.*?<a[^>]*href="/([^"]+)"', article, re.DOTALL)
    if not repo_match:
        return None
    repo_full_name = repo_match.group(1).strip()
    if not validate_repo_name(repo_full_name):
        log.warning(f"跳过无效 repo: {repo_full_name}")
        return None

    desc_match = re.search(r'<p class="col-9[^"]*"[^>]*>\s*(.*?)\s*</p>', article, re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else ""
    description = re.sub(r'<[^>]+>', '', description).strip()
    description = unescape_html(description)

    lang_match = re.search(r'itemprop="programmingLanguage"[^>]*>([^<]+)<', article)
    language = lang_match.group(1).strip() if lang_match else ""

    star_match = re.search(
        r'<a[^>]*href="/' + re.escape(repo_full_name) + r'/stargazers"[^>]*>.*?([0-9,]+)\s*</a>',
        article, re.DOTALL
    )
    total_stars = 0
    if star_match:
        total_stars = int(star_match.group(1).replace(',', ''))

    # 本月 star（GitHub 月榜 "X stars this month"）
    monthly_match = re.search(r'([\d,]+)\s+stars?\s+this\s+month', article)
    stars_this_period = 0
    if monthly_match:
        stars_this_period = int(monthly_match.group(1).replace(',', ''))

    return {
        "rank": rank,
        "repo": repo_full_name,
        "description": description,
        "language": language,
        "stars_this_period": stars_this_period,
        "total_stars": total_stars,
        "url": f"https://github.com/{repo_full_name}",
    }

# ========== 写入 raw ==========
def save_raw_json(projects, month_key):
    """落 raw/trending-monthly/YYYY-MM.json；命名锁定日历月 YYYY-MM"""
    os.makedirs(RAW_DIR, exist_ok=True)
    filepath = os.path.join(RAW_DIR, f"{month_key}.json")
    data = {
        "date": month_key,
        "month": month_key,
        "scraped_at": datetime.now().isoformat(),
        "period": "monthly",
        "count": len(projects),
        "projects": projects,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log.info(f"原始月榜已保存: {filepath}")
    return filepath

# ========== 主流程 ==========
def main():
    dry_run = "--dry-run" in sys.argv
    month_key = get_month_key()
    log.info(f"月榜期次: {month_key}")

    html = fetch_monthly_html()
    projects = parse_monthly(html)

    if len(projects) < MIN_PROJECTS:
        debug_dir = os.path.join(WIKI_PATH, "raw", "debug")
        os.makedirs(debug_dir, exist_ok=True)
        debug_file = os.path.join(debug_dir, f"monthly-debug-{month_key}.html")
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(html)
        log.warning(f"项目数不足 {MIN_PROJECTS}，debug HTML 已保存到 {debug_file}")

    if dry_run:
        print("\n=== DRY RUN ===")
        print(json.dumps(projects, ensure_ascii=False, indent=2))
        print(f"\n共 {len(projects)} 个项目，未写入 raw")
        return

    save_raw_json(projects, month_key)

    period_stars = sum(p["stars_this_period"] for p in projects)
    print(f"\n月榜采集完成: {len(projects)} 个项目, 总月 star: {period_stars:,}")
    for p in projects[:5]:
        print(f"  #{p['rank']} {p['repo']} - +{p['stars_this_period']:,} stars [{p['language']}]")

if __name__ == '__main__':
    main()
