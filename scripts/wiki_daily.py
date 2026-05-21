#!/usr/bin/env python3
"""GitHub Trending Wiki 日报脚本 v2
- SQLite 作为唯一数据源，markdown entity 从 DB 生成（消除双写不一致）
- 自动关联：同语言/同领域项目生成 [[wikilinks]]
- Concept 自动生成：同领域≥3项目上榜时创建/更新 concept 页面
- 飞书推送 + Git commit
"""

import json, os, sys, subprocess, datetime, requests, sqlite3, re
from collections import defaultdict

BASE = '/srv/www/github-trending-wiki'
ENTITIES_DIR = f'{BASE}/entities'
CONCEPTS_DIR = f'{BASE}/concepts'
RAW_DIR = f'{BASE}/raw/trending'
DB_PATH = f'{BASE}/data/github_trending.db'
TODAY = datetime.date.today().isoformat()

# ============ 领域关键词映射 ============
DOMAIN_KEYWORDS = {
    'ai-agent': ['agent', 'agentic', 'skill', 'mcp', 'claude', 'gpt', 'llm', 'ai', 'copilot', 'autonomous'],
    'web': ['browser', 'web', 'http', 'frontend', 'css', 'html', 'chrome'],
    'cli': ['cli', 'terminal', 'command', 'shell', 'console'],
    'data': ['data', 'analytics', 'etl', 'pipeline', 'database', 'sql', 'metric'],
    'devops': ['deploy', 'infra', 'monitor', 'observability', 'devops', 'ci/cd'],
    'security': ['security', 'privacy', 'encrypt', 'cloak', 'vpn', 'firewall'],
    'education': ['tutorial', 'beginner', 'course', 'learn', 'teach'],
    'erp': ['erp', 'business', 'commerce', 'shop', 'invoice'],
    'image-gen': ['diffusion', 'image', 'generation', 'synthesis', 'sana', 'stable'],
    'audio': ['tts', 'speech', 'audio', 'voice', 'music', 'supertonic'],
    'science': ['research', 'scientific', 'academic', 'paper', 'arxiv'],
}

def detect_domains(repo, desc, language=''):
    """检测项目所属领域"""
    text = f"{repo} {desc} {language}".lower()
    domains = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            domains.append(domain)
    return domains if domains else ['uncategorized']

# ============ 第一步：采集 ============
def collect():
    print(f"[1/5] 采集 GitHub Trending 数据...")
    result = subprocess.run(
        ['python3', f'{BASE}/scripts/github_trending_collector.py'],
        capture_output=True, text=True, cwd=BASE, timeout=120
    )
    if result.returncode != 0:
        print(f"  采集失败: {result.stderr[-500:]}")
        return False
    today_file = f'{RAW_DIR}/{TODAY}.json'
    if not os.path.exists(today_file):
        print(f"  今日数据文件不存在: {today_file}")
        return False
    with open(today_file) as f:
        data = json.load(f)
    projects = data.get('projects', [])
    print(f"  采集完成: {len(projects)} 个项目")
    
    # 确保 DB repo_stats 与今日数据同步
    sync_db_stats(projects)
    return True

def sync_db_stats(projects):
    """确保 DB repo_stats 与今日 trending 数据一致。
    采集脚本在重复运行时会跳过 repo_stats 递增，
    这里强制重新计算，保证 DB 是唯一数据源。
    """
    print(f"  同步 DB repo_stats...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for p in projects:
        repo = p['repo']
        # 查询该 repo 的所有上榜日期
        cursor.execute(
            'SELECT date FROM trending_daily WHERE repo_full_name=? AND period=? ORDER BY date DESC',
            (repo, 'daily')
        )
        dates = [row[0] for row in cursor.fetchall()]
        
        if not dates:
            continue
        
        count = len(dates)
        first_seen = dates[-1]
        last_seen = dates[0]
        
        # 计算连续天数
        consecutive = 1
        for i in range(1, len(dates)):
            prev = datetime.datetime.strptime(dates[i-1], '%Y-%m-%d')
            curr = datetime.datetime.strptime(dates[i], '%Y-%m-%d')
            if (prev - curr).days <= 1:
                consecutive += 1
            else:
                break
        
        # 查询最高排名和最大 star
        cursor.execute(
            'SELECT MIN(rank), MAX(stars_today) FROM trending_daily WHERE repo_full_name=? AND period=?',
            (repo, 'daily')
        )
        row = cursor.fetchone()
        peak_rank = row[0] or p.get('rank', 999)
        max_stars = row[1] or p.get('stars_today', 0)
        
        # 更新或插入
        cursor.execute('SELECT 1 FROM repo_stats WHERE repo_full_name=?', (repo,))
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute('''
                UPDATE repo_stats SET
                    last_seen=?, trending_count_daily=?, consecutive_days=?,
                    max_consecutive_days=MAX(max_consecutive_days, ?),
                    peak_rank=?, max_stars_today=?, last_stars=?,
                    description=?, language=?
                WHERE repo_full_name=?
            ''', (last_seen, count, consecutive, consecutive,
                  peak_rank, max_stars, p.get('total_stars', 0),
                  p.get('description', ''), p.get('language', ''), repo))
        else:
            cursor.execute('''
                INSERT INTO repo_stats
                (repo_full_name, description, language, first_seen, last_seen,
                 trending_count_daily, trending_count_weekly, trending_count_monthly,
                 consecutive_days, max_consecutive_days, peak_rank, max_stars_today, last_stars)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?, ?, ?, ?, ?)
            ''', (repo, p.get('description', ''), p.get('language', ''),
                  first_seen, last_seen, count, consecutive, consecutive,
                  peak_rank, max_stars, p.get('total_stars', 0)))
    
    conn.commit()
    conn.close()
    print(f"  DB 同步完成")

# ============ 第二步：从 DB 生成 entity 页面 ============
def generate_entities():
    print(f"[2/5] 从 DB 生成 entity 页面...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # 获取所有 repo_stats
    cursor = conn.execute('SELECT * FROM repo_stats ORDER BY last_seen DESC')
    all_repos = [dict(row) for row in cursor.fetchall()]
    
    # 获取每个 repo 的上榜历史
    cursor = conn.execute('SELECT repo_full_name, date, rank, stars_today FROM trending_daily ORDER BY date DESC')
    history = defaultdict(list)
    for row in cursor.fetchall():
        history[row[0]].append({'date': row[1], 'rank': row[2], 'stars': row[3]})
    
    # 按领域分组（用于自动关联）
    domain_map = defaultdict(list)  # domain -> [repo_full_name]
    repo_domains = {}  # repo_full_name -> [domains]
    for r in all_repos:
        domains = detect_domains(r['repo_full_name'], r.get('description', ''), r.get('language', ''))
        repo_domains[r['repo_full_name']] = domains
        for d in domains:
            domain_map[d].append(r['repo_full_name'])
    
    # 按语言分组
    lang_map = defaultdict(list)
    for r in all_repos:
        lang = r.get('language', '其他') or '其他'
        lang_map[lang].append(r['repo_full_name'])
    
    os.makedirs(ENTITIES_DIR, exist_ok=True)
    new_count = 0
    update_count = 0
    
    for r in all_repos:
        repo = r['repo_full_name']
        slug = repo.replace('/', '-').lower()
        entity_path = f'{ENTITIES_DIR}/{slug}.md'
        
        # 判断是否新建
        is_new = not os.path.exists(entity_path)
        
        # Confidence
        count = r.get('trending_count_daily', 1) or 1
        if count >= 3:
            confidence = 'high'
        elif count >= 2:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        # Tags
        tags = []
        lang = r.get('language', '') or ''
        lang_lower = lang.lower()
        lang_tag_map = {
            'python': 'python', 'rust': 'rust', 'typescript': 'typescript',
            'go': 'go', 'java': 'java', 'c++': 'cpp', 'shell': 'shell',
            'jupyter notebook': 'python', 'css': 'python',
        }
        if lang_lower in lang_tag_map:
            tags.append(lang_tag_map[lang_lower])
        for d in repo_domains.get(repo, []):
            tags.append(d)
        consec = r.get('consecutive_days', 0) or 0
        if consec >= 3:
            tags.append('rising')
        if not tags:
            tags.append('tool')
        # Deduplicate while preserving order
        seen = set()
        unique_tags = []
        for t in tags:
            if t not in seen:
                seen.add(t)
                unique_tags.append(t)
        tags = unique_tags
        
        # Type
        desc = (r.get('description', '') or '').lower()
        if any(w in desc for w in ['tutorial', 'beginner', 'course']):
            ptype = 'tutorial'
        elif any(w in desc for w in ['framework', 'sdk', 'engine']):
            ptype = 'framework'
        else:
            ptype = 'tool'
        
        # 上榜历史（最近5次）
        hist_lines = []
        for h in history.get(repo, [])[:5]:
            hist_lines.append(f"  - {h['date']}: #{h['rank']}, +{h['stars']}⭐")
        
        # 自动关联：同语言 + 同领域的其他项目
        related = set()
        # 同语言（最多3个）
        for other in lang_map.get(lang, [])[:4]:
            if other != repo:
                related.add(other)
        # 同领域（最多3个）
        for d in repo_domains.get(repo, []):
            for other in domain_map.get(d, [])[:4]:
                if other != repo:
                    related.add(other)
        related = list(related)[:5]
        related_links = [f'[[{r2.replace("/", "-").lower()}]]' for r2 in related]
        
        # Frontmatter
        fm = f"""---
title: "{repo}"
created: {r.get('first_seen', TODAY)}
updated: {r.get('last_seen', TODAY)}
type: {ptype}
tags: [{', '.join(tags)}]
sources: [raw/trending/{r.get('last_seen', TODAY)}.json]
confidence: {confidence}
trending_count_daily: {count}
trending_count_weekly: {r.get('trending_count_weekly', 0) or 0}
trending_count_monthly: {r.get('trending_count_monthly', 0) or 0}
consecutive_days: {consec}
first_trending: {r.get('first_seen', TODAY)}
last_trending: {r.get('last_seen', TODAY)}
peak_rank: {r.get('peak_rank', 0) or 0}
total_stars: {r.get('last_stars', '?') or '?'}
language: {lang or '?'}
---"""
        
        # Body
        body = f"""# {repo}

{r.get('description', '') or 'No description'}

- 语言: {lang or '?'}
- 上榜次数: {count} 次
- 连续上榜: {consec} 天
- 最高排名: #{r.get('peak_rank', '?') or '?'}
- 链接: [{repo}](https://github.com/{repo})

## 上榜历史

{chr(10).join(hist_lines) if hist_lines else '- 首次上榜'}

## 相关项目

{' '.join(related_links) if related_links else '- 暂无'}
"""
        
        with open(entity_path, 'w') as f:
            f.write(f"{fm}\n\n{body}\n")
        
        if is_new:
            new_count += 1
        else:
            update_count += 1
    
    conn.close()
    print(f"  新建: {new_count}, 更新: {update_count}, 总 entity: {len(all_repos)}")
    return all_repos, repo_domains, domain_map

# ============ 第三步：Concept 自动生成 ============
def generate_concepts(all_repos, repo_domains, domain_map):
    print(f"[3/5] 生成 Concept 页面...")
    os.makedirs(CONCEPTS_DIR, exist_ok=True)
    
    # 获取今日上榜的 repo
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        'SELECT repo_full_name FROM trending_daily WHERE date = ? AND period = ?',
        (TODAY, 'daily')
    )
    today_repos = {row[0] for row in cursor.fetchall()}
    conn.close()
    
    new_concepts = 0
    updated_concepts = 0
    
    for domain, repos in domain_map.items():
        if domain == 'uncategorized':
            continue
        
        # 今日上榜的同领域项目
        today_in_domain = [r for r in repos if r in today_repos]
        if len(today_in_domain) < 2:  # 至少2个才值得建 concept
            continue
        
        concept_path = f'{CONCEPTS_DIR}/{domain}.md'
        is_new = not os.path.exists(concept_path)
        
        # 生成 wikilinks
        links = [f'[[{r.replace("/", "-").lower()}]]' for r in today_in_domain]
        
        # 统计
        lang_dist = defaultdict(int)
        total_stars_today = 0
        for r in today_in_domain:
            # 从 repo_stats 获取语言
            repo_data = next((x for x in all_repos if x['repo_full_name'] == r), None)
            if repo_data:
                lang_dist[repo_data.get('language', '?') or '?'] += 1
        
        lang_str = ', '.join([f'{l} {c}个' for l, c in sorted(lang_dist.items(), key=lambda x: -x[1])])
        
        fm = f"""---
title: "{domain}"
created: {TODAY if is_new else 'unknown'}
updated: {TODAY}
type: concept
tags: [{domain}]
---"""
        
        body = f"""# {domain}

## 今日上榜项目（{len(today_in_domain)} 个）

{' '.join(links)}

## 语言分布

{lang_str}

## 趋势观察

{len(today_in_domain)} 个 {domain} 领域项目今日同时上榜，反映该领域持续活跃。
"""
        
        with open(concept_path, 'w') as f:
            f.write(f"{fm}\n\n{body}\n")
        
        if is_new:
            new_concepts += 1
        else:
            updated_concepts += 1
    
    print(f"  新建 concept: {new_concepts}, 更新: {updated_concepts}")

# ============ 更新 index.md 和 log.md ============
def update_index_and_log(all_repos):
    print(f"  更新 index.md 和 log.md...")
    
    entities = sorted([f for f in os.listdir(ENTITIES_DIR) if f.endswith('.md')])
    concepts = sorted([f for f in os.listdir(CONCEPTS_DIR) if f.endswith('.md')])
    total_pages = len(entities) + len(concepts)
    
    # Entity entries
    entity_entries = []
    for fname in entities:
        slug = fname.replace('.md', '')
        # 从 DB 获取信息
        repo_name = slug.replace('-', '/', 1)  # rough reverse
        # Read frontmatter for display
        fm = {}
        in_fm = False
        with open(f'{ENTITIES_DIR}/{fname}') as f:
            for line in f:
                if line.strip() == '---':
                    if in_fm:
                        break
                    in_fm = True
                    continue
                if in_fm and ':' in line:
                    k, v = line.strip().split(':', 1)
                    fm[k.strip()] = v.strip()
        
        title_fm = fm.get('title', slug)
        consecutive = int(fm.get('consecutive_days', '0') or '0')
        confidence = fm.get('confidence', 'low')
        
        # Short description from body
        body_lines = []
        in_body = False
        dash_count = 0
        with open(f'{ENTITIES_DIR}/{fname}') as f:
            for line in f:
                if line.strip() == '---':
                    dash_count += 1
                    if dash_count == 2:
                        in_body = True
                        continue
                if in_body and line.strip() and not line.startswith('#'):
                    body_lines.append(line.strip())
                    if len(body_lines) >= 1:
                        break
        short_desc = body_lines[0][:60] if body_lines else ''
        if len((body_lines[0] if body_lines else '')) > 60:
            short_desc += '...'
        
        badge = ''
        if consecutive >= 3:
            badge = ' 🔥'
        elif consecutive >= 2 or fm.get('created') == TODAY:
            badge = ' 🆕'
        
        display_name = title_fm.split('/')[-1] if '/' in title_fm else title_fm
        entity_entries.append(f'- [[{slug}|{display_name}]] — {short_desc}{badge}')
    
    # Concept entries
    concept_entries = []
    for fname in concepts:
        slug = fname.replace('.md', '')
        concept_entries.append(f'- [[{slug}]] — {slug} 领域趋势分析')
    
    index_content = f"""# GitHub Trending Wiki Index

> 内容目录。所有 wiki 页面按类型分组，每条一行：wikilink + 摘要。
> 最后更新：{TODAY} | 总页面：{total_pages}

## Entities

"""
    for entry in sorted(entity_entries):
        index_content += entry + '\n'
    
    if concept_entries:
        index_content += '\n## Concepts\n\n'
        for entry in sorted(concept_entries):
            index_content += entry + '\n'
    
    index_content += """
## Comparisons

<!-- 项目对比分析 -->

## Reports

- [[reports/2026-05-16]] — 首日日报，12 个项目，Agent Skills 生态爆发
- [[reports/2026-05-17]] — 第 2 日日报，12 个项目全部连续上榜
"""
    with open(f'{BASE}/index.md', 'w') as f:
        f.write(index_content)
    
    # Update log.md
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        'SELECT repo_full_name, rank, stars_today, language FROM trending_daily WHERE date = ? AND period = ?',
        (TODAY, 'daily')
    )
    today_projects = cursor.fetchall()
    
    # 语言分布
    lang_count = defaultdict(int)
    for p in today_projects:
        lang_count[p[3] or '其他'] += 1
    
    # 连续上榜
    cursor = conn.execute(
        'SELECT repo_full_name, consecutive_days FROM repo_stats WHERE consecutive_days >= 2 ORDER BY consecutive_days DESC'
    )
    consecutive_list = cursor.fetchall()
    
    # Star top3
    top3 = sorted(today_projects, key=lambda x: -int(x[2] or 0))[:3]
    top3_str = ', '.join([p[0] + ' +' + str(p[2]) + '⭐' for p in top3])
    
    # 新项目
    cursor = conn.execute(
        'SELECT repo_full_name FROM repo_stats WHERE first_seen = ?',
        (TODAY,)
    )
    new_repos = [r[0] for r in cursor.fetchall()]
    conn.close()
    
    new_names_str = ', '.join(new_repos[:5]) + ('...' if len(new_repos) > 5 else '')
    lang_str = ', '.join([f'{l} {c}个' for l, c in sorted(lang_count.items(), key=lambda x: -x[1])[:5]])
    
    log_entry = f"""
## [{TODAY}] update | GitHub Trending 日报
- 采集 {len(today_projects)} 个项目（raw/trending/{TODAY}.json）
- 新建 entity: {len(new_repos)} 个（{new_names_str}）
- 趋势: {lang_str}
"""
    for repo, days in consecutive_list:
        log_entry += f"- 连续 {days} 天上榜: {repo}\n"
    log_entry += f"- 当日 star 增长 Top 3: {top3_str}\n"
    
    with open(f'{BASE}/log.md', 'a') as f:
        f.write(log_entry)

# ============ 第四步：Git Commit ============
def git_commit():
    print(f"[3/5] Git commit...")
    env = os.environ.copy()
    env['GIT_SSH_COMMAND'] = 'ssh -o StrictHostKeyChecking=no -i /root/.ssh/id_ed25519'
    subprocess.run(['git', 'add', '-A'], cwd=BASE, capture_output=True, env=env)
    result = subprocess.run(
        ['git', 'commit', '-m', f'wiki: {TODAY} compilation'],
        cwd=BASE, capture_output=True, text=True, env=env
    )
    if result.returncode == 0:
        print(f"  Commit 成功")
    else:
        print(f"  Commit: {result.stdout.strip() or result.stderr.strip()[:200]}")

# ============ 第五步：飞书推送 ============
# ============ LLM 深度分析 + 描述翻译 ============
def llm_enrich():
    """调用 LLM 对今日数据进行深度分析 + 描述翻译，返回 (analysis_text, desc_zh_dict)"""
    print(f"[4/5] LLM 深度分析 + 描述翻译...")
    
    # 从 DB 读取今日和近期数据
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # 今日项目
    cursor = conn.execute('''
        SELECT td.repo_full_name, td.rank, td.stars_today, td.language, td.description,
               rs.consecutive_days, rs.trending_count_daily, rs.last_stars
        FROM trending_daily td
        LEFT JOIN repo_stats rs ON td.repo_full_name = rs.repo_full_name
        WHERE td.date = ? AND td.period = ?
        ORDER BY td.rank
    ''', (TODAY, 'daily'))
    today_projects = [dict(row) for row in cursor.fetchall()]
    
    # 近5天的每日项目数和语言分布（用于趋势对比）
    cursor = conn.execute('''
        SELECT date, COUNT(*) as count
        FROM trending_daily
        WHERE period = 'daily' AND date >= date(?, '-4 days')
        GROUP BY date
        ORDER BY date
    ''', (TODAY,))
    daily_counts = [dict(row) for row in cursor.fetchall()]
    
    # 近5天语言趋势
    cursor = conn.execute('''
        SELECT date, language, COUNT(*) as count
        FROM trending_daily
        WHERE period = 'daily' AND date >= date(?, '-4 days')
        GROUP BY date, language
        ORDER BY date, count DESC
    ''', (TODAY,))
    lang_trend = [dict(row) for row in cursor.fetchall()]
    
    # 连续上榜项目
    cursor = conn.execute('''
        SELECT repo_full_name, consecutive_days, trending_count_daily, last_stars
        FROM repo_stats
        WHERE consecutive_days >= 2
        ORDER BY consecutive_days DESC
    ''')
    consecutive = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    # 构建分析输入
    today_list = []
    for p in today_projects:
        repo = p['repo_full_name']
        rank = p.get('rank', '?')
        stars = p.get('stars_today', 0)
        lang = p.get('language', '?') or '?'
        desc = p.get('description', '') or ''
        cons = p.get('consecutive_days', 0) or 0
        count = p.get('trending_count_daily', 0) or 0
        today_list.append(f"#{rank} {repo} [{lang}] +{stars}⭐ 连续{cons}天/共{count}次 | {desc}")
    
    consec_list = []
    for c in consecutive:
        consec_list.append(f"{c['repo_full_name']}: 连续{c['consecutive_days']}天, 共{c['trending_count_daily']}次上榜, {c.get('last_stars', '?')} stars")
    
    # 语言趋势摘要
    lang_by_date = defaultdict(lambda: defaultdict(int))
    for lt in lang_trend:
        lang_by_date[lt['date']][lt['language'] or '其他'] = lt['count']
    
    trend_lines = []
    for d in sorted(lang_by_date.keys()):
        langs = lang_by_date[d]
        top3 = sorted(langs.items(), key=lambda x: -x[1])[:3]
        trend_lines.append(f"  {d}: {', '.join([f'{l}({c})' for l, c in top3])}")
    
    # 项目列表（用于翻译）
    repo_list = []
    for p in today_projects:
        repo = p['repo_full_name']
        desc = p.get('description', '') or ''
        repo_list.append(f"{repo}: {desc}")
    
    prompt = f"""你是技术趋势分析师。基于今日 GitHub Trending 数据，完成两个任务。

## 今日数据（{TODAY}）
{len(today_projects)} 个项目上榜：
{chr(10).join(today_list)}

## 连续上榜项目
{chr(10).join(consec_list) if consec_list else '无'}

## 近5天语言趋势
{chr(10).join(trend_lines)}

## 每日项目数
{chr(10).join([f"  {d['date']}: {d['count']}个" for d in daily_counts])}

## 任务一：深度分析（≤400字）

**🔍 趋势洞察**
（2-3句：今天和近期比，什么在变？哪些领域升温/降温？）

**💡 亮点解读**
（2-3个值得注意的项目，每个1句：为什么值得关注，不只是复读描述）

**📌 行动建议**
（1-2句：对全栈架构师来说，哪些值得深入看？）

## 任务二：项目描述翻译

将以下项目描述翻译成简洁的中文（保留技术术语英文，每个≤30字）：

{chr(10).join(repo_list)}

输出格式（严格遵循）：

---ANALYSIS---
（深度分析内容）
---DESCRIPTIONS---
（每行一个：repo: 中文描述）"""

    # 调用 LLM API
    try:
        import yaml
        with open('/root/.hermes/profiles/radar/config.yaml') as f:
            cfg = yaml.safe_load(f)
        
        xc = cfg.get('xunfei-coding', {})
        api_key = xc.get('api_key', '')
        base_url = xc.get('base_url', '')
        model = xc.get('model', 'astron-code-latest')
        
        if not api_key or not base_url:
            print(f"  LLM API 配置缺失，跳过分析")
            return "", {}
        
        resp = requests.post(
            f'{base_url}/chat/completions',
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "你是技术趋势分析师，输出简洁有洞察的中文分析。严格按指定格式输出。"},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1200,
                "temperature": 0.7,
            },
            timeout=60
        )
        
        if resp.status_code != 200:
            print(f"  LLM API 错误: {resp.status_code}")
            return "", {}
        
        result = resp.json()
        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        if not content:
            print(f"  LLM 返回空内容")
            return "", {}
        
        # 解析输出
        analysis = ""
        desc_zh = {}
        
        if '---ANALYSIS---' in content and '---DESCRIPTIONS---' in content:
            parts = content.split('---ANALYSIS---', 1)[1].split('---DESCRIPTIONS---', 1)
            analysis = parts[0].strip()
            desc_section = parts[1].strip()
            
            for line in desc_section.split('\n'):
                line = line.strip()
                if ':' in line and '/' in line:
                    # 格式: owner/repo: 中文描述
                    colon_idx = line.index(':')
                    repo = line[:colon_idx].strip()
                    zh_desc = line[colon_idx+1:].strip()
                    desc_zh[repo] = zh_desc
        else:
            # 降级：整个内容作为分析
            analysis = content.strip()
        
        print(f"  分析完成: {len(analysis)} 字, 翻译: {len(desc_zh)} 个项目")
        return analysis, desc_zh
            
    except Exception as e:
        print(f"  LLM 分析失败: {e}")
        return "", {}

def push_feishu():
    print(f"[5/5] 飞书推送...")
    
    result = subprocess.run(
        ['bash', '-c', 'source /root/.hermes/profiles/radar/.env && echo $FEISHU_APP_SECRET'],
        capture_output=True, text=True
    )
    APP_SECRET = result.stdout.strip()
    APP_ID = 'cli_a916e5b5a1b8dcd4'
    
    resp = requests.post(
        'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
        json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=10
    )
    tenant_token = resp.json().get('tenant_access_token', '')
    if not tenant_token:
        print(f"  Token 获取失败: {resp.json()}")
        return False
    
    # 从 DB 读取今日数据
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute('''
        SELECT td.repo_full_name, td.rank, td.stars_today, td.language, td.description,
               rs.consecutive_days, rs.trending_count_daily, rs.last_stars
        FROM trending_daily td
        LEFT JOIN repo_stats rs ON td.repo_full_name = rs.repo_full_name
        WHERE td.date = ? AND td.period = ?
        ORDER BY td.rank
    ''', (TODAY, 'daily'))
    projects = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # 语言分布
    lang_count = defaultdict(int)
    for p in projects:
        lang_count[p.get('language', '其他') or '其他'] += 1
    top_lang = sorted(lang_count.items(), key=lambda x: -x[1])[:5]
    lang_str = " | ".join([f"{l} {c}个" for l, c in top_lang])
    
    # 连续上榜
    consecutive = [(p['repo_full_name'], p.get('consecutive_days', 0) or 0, p.get('stars_today', 0))
                   for p in projects if (p.get('consecutive_days', 0) or 0) >= 2]
    consecutive.sort(key=lambda x: -x[1])
    
    # LLM 分析 + 描述翻译
    analysis, desc_zh = llm_enrich()
    
    # ===== 构建富文本 post =====
    rows = []
    
    # 标题
    rows.append([{"tag": "md", "text": f"📊 **GitHub Trending 日报** `{TODAY}`"}])
    rows.append([{"tag": "text", "text": " "}])
    
    # 概览
    rows.append([{"tag": "md", "text": f"**{len(projects)}** 个项目上榜 ｜ 语言：{lang_str}"}])
    rows.append([{"tag": "text", "text": " "}])
    
    # 深度分析区（如果有）
    if analysis:
        rows.append([{"tag": "md", "text": "🧠 **深度分析**"}])
        # 把分析文本按行拆分，每行一个 row
        for line in analysis.split('\n'):
            line = line.strip()
            if line:
                rows.append([{"tag": "md", "text": line}])
        rows.append([{"tag": "text", "text": " "}])
    
    # 连续上榜区
    if consecutive:
        rows.append([{"tag": "md", "text": "🔥 **连续上榜**"}])
        for repo, days, stars in consecutive:
            name = repo.split('/')[1]
            org = repo.split('/')[0]
            url = f"https://github.com/{repo}"
            rows.append([{"tag": "md", "text": f"  [{name}]({url}) `{org}` — 连续 **{days}** 天 ｜ +{stars}⭐"}])
        rows.append([{"tag": "text", "text": " "}])
    
    # 完整榜单
    rows.append([{"tag": "md", "text": "📋 **今日榜单**"}])
    for p in projects:
        rank = p.get('rank', '?')
        repo = p['repo_full_name']
        name = repo.split('/')[1]
        org = repo.split('/')[0]
        lang = p.get('language', '?') or '?'
        stars = p.get('stars_today', '?')
        url = f"https://github.com/{repo}"
        # 优先用 LLM 翻译的中文描述，降级用英文描述
        desc = desc_zh.get(repo, p.get('description', '') or '')
        if len(desc) > 60:
            desc = desc[:57] + '...'
        rows.append([{"tag": "md", "text": f"**{rank}.** [{name}]({url}) — {desc}"}])
        rows.append([{"tag": "md", "text": f"  `{lang}` `{org}` +{stars}⭐"}])

    # 发送飞书消息
    try:
        post_payload = json.dumps({"zh_cn": {"content": rows}}, ensure_ascii=False)
        headers = {"Authorization": f"Bearer {tenant_token}", "Content-Type": "application/json; charset=utf-8"}
        resp = requests.post(
            "https://open.feishu.cn/open-apis/im/v1/messages",
            params={"receive_id_type": "chat_id"},
            headers=headers,
            json={"receive_id": "oc_b269ff6fab6e321a35e344ea5984e985", "msg_type": "post", "content": post_payload},
            timeout=10
        )
        if resp.status_code == 200 and resp.json().get("code") == 0:
            print(f"  飞书推送成功")
        else:
            print(f"  飞书推送失败: {resp.status_code} {resp.json()}")
    except Exception as e:
        print(f"  飞书推送异常: {e}")

def run_lint_and_alert():
    """编译后自动跑 lint，critical 问题飞书告警"""
    print(f"[Lint] 自动检查...")
    result = subprocess.run(
        ['python3', f'{BASE}/scripts/wiki_lint.py'],
        capture_output=True, text=True, cwd=BASE, timeout=30
    )
    lint_output = result.stdout
    
    # 检查是否有 critical 问题
    critical_count = 0
    for line in lint_output.split('\n'):
        if '🔴 Critical:' in line:
            try:
                critical_count = int(line.split(':')[1].strip())
            except:
                pass
    
    if critical_count > 0:
        # 飞书告警
        print(f"  ⚠️ 发现 {critical_count} 个 critical 问题，推送飞书告警...")
        try:
            sub_result = subprocess.run(
                ['bash', '-c', 'source /root/.hermes/profiles/radar/.env && echo $FEISHU_APP_SECRET'],
                capture_output=True, text=True
            )
            APP_SECRET = sub_result.stdout.strip()
            APP_ID = 'cli_a916e5b5a1b8dcd4'
            
            resp = requests.post(
                'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
                json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=10
            )
            tenant_token = resp.json().get('tenant_access_token', '')
            
            if tenant_token:
                # 提取 critical 问题列表
                critical_lines = []
                in_critical = False
                for line in lint_output.split('\n'):
                    if '## 🔴 Critical' in line:
                        in_critical = True
                        continue
                    if in_critical and line.startswith('## '):
                        break
                    if in_critical and line.strip().startswith('-'):
                        critical_lines.append(line.strip())
                
                rows = []
                rows.append([{"tag": "md", "text": f"⚠️ **Wiki Lint 告警 | {TODAY}**"}])
                rows.append([{"tag": "md", "text": f"发现 {critical_count} 个 critical 问题："}])
                for cl in critical_lines[:10]:
                    rows.append([{"tag": "md", "text": cl}])
                
                post_payload = json.dumps({"zh_cn": {"content": rows}}, ensure_ascii=False)
                headers = {"Authorization": f"Bearer {tenant_token}", "Content-Type": "application/json; charset=utf-8"}
                requests.post(
                    "https://open.feishu.cn/open-apis/im/v1/messages",
                    params={"receive_id_type": "chat_id"},
                    headers=headers,
                    json={"receive_id": "oc_b269ff6fab6e321a35e344ea5984e985", "msg_type": "post", "content": post_payload},
                    timeout=10
                )
                print(f"  告警推送完成")
        except Exception as e:
            print(f"  告警推送失败: {e}")
    else:
        print(f"  ✅ Lint 通过，无 critical 问题")

# ============ Main ============
if __name__ == '__main__':
    if not collect():
        print("[SILENT]")
        sys.exit(1)
    
    all_repos, repo_domains, domain_map = generate_entities()
    generate_concepts(all_repos, repo_domains, domain_map)
    update_index_and_log(all_repos)
    git_commit()
    run_lint_and_alert()
    push_feishu()
    print(f"\n✅ {TODAY} 日报完成")
