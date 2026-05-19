#!/usr/bin/env python3
"""GitHub Trending Wiki 编译脚本 - 一键完成采集、编译、git commit、飞书推送"""

import json, os, sys, subprocess, datetime, requests

BASE = '/srv/www/github-trending-wiki'
ENTITIES_DIR = f'{BASE}/entities'
RAW_DIR = f'{BASE}/raw/trending'
TODAY = datetime.date.today().isoformat()

# ============ 第一步：采集 ============
def collect():
    print(f"[1/4] 采集 GitHub Trending 数据...")
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
    return True

# ============ 第二步：Wiki 编译 ============
def read_frontmatter(path):
    fm = {}
    in_fm = False
    with open(path) as f:
        for line in f:
            if line.strip() == '---':
                if in_fm:
                    break
                in_fm = True
                continue
            if in_fm and ':' in line:
                k, v = line.strip().split(':', 1)
                fm[k.strip()] = v.strip()
    return fm

def assign_tags(p):
    tags = []
    lang = (p.get('language', '') or '').lower()
    lang_map = {
        'python': 'python', 'rust': 'rust', 'typescript': 'typescript',
        'go': 'go', 'java': 'java', 'c++': 'cpp', 'shell': 'shell',
        'jupyter notebook': 'python', 'css': 'python',
    }
    if lang in lang_map:
        tags.append(lang_map[lang])
    desc = (p.get('description', '') or '').lower()
    repo = p.get('repo', '').lower()
    if any(w in desc or w in repo for w in ['agent', 'agentic', 'skill', 'mcp']):
        tags.append('ai-agent')
    if any(w in desc or w in repo for w in ['llm', 'gpt', 'claude', 'model']):
        tags.append('llm')
    if any(w in desc or w in repo for w in ['web', 'browser']):
        tags.append('web')
    if any(w in desc or w in repo for w in ['cli', 'terminal']):
        tags.append('cli')
    if any(w in desc or w in repo for w in ['framework', 'sdk']):
        tags.append('framework')
    if any(w in desc or w in repo for w in ['tool']):
        tags.append('tool')
    if any(w in desc or w in repo for w in ['tutorial', 'beginner', 'course']):
        tags.append('tutorial')
    if not tags:
        tags.append('tool')
    return tags

def assign_type(p):
    desc = (p.get('description', '') or '').lower()
    repo = p.get('repo', '').lower()
    if any(w in desc or w in repo for w in ['tutorial', 'beginner', 'course', 'awesome']):
        return 'tutorial'
    if any(w in desc or w in repo for w in ['framework', 'sdk', 'engine']):
        return 'framework'
    return 'tool'

def compile_wiki():
    print(f"[2/4] Wiki 编译...")
    today_file = f'{RAW_DIR}/{TODAY}.json'
    with open(today_file) as f:
        data = json.load(f)
    projects = data.get('projects', [])
    
    existing = set(os.listdir(ENTITIES_DIR))
    new_count = 0
    update_count = 0
    
    for p in projects:
        repo = p['repo']
        slug = repo.replace('/', '-').lower()
        lang = p.get('language', '') or '?'
        stars_today = p.get('stars_today', 0)
        rank = p.get('rank', 0)
        desc = p.get('description', '') or ''
        url = p.get('url', f'https://github.com/{repo}')
        tags = assign_tags(p)
        ptype = assign_type(p)
        entity_path = f'{ENTITIES_DIR}/{slug}.md'
        
        if slug + '.md' in existing:
            # Update existing
            fm = read_frontmatter(entity_path)
            first_seen = fm.get('first_trending', fm.get('created', TODAY))
            old_count = int(fm.get('trending_count_daily', '0') or '0')
            old_consecutive = int(fm.get('consecutive_days', '0') or '0')
            old_peak = int(fm.get('peak_rank', '999') or '999')
            old_total_stars = fm.get('total_stars', '?')
            
            new_c = old_count + 1
            new_cons = old_consecutive + 1
            new_peak = min(old_peak, rank)
            confidence = 'high' if new_c >= 3 else ('medium' if new_c >= 2 else 'low')
            if new_cons >= 3 and 'rising' not in tags:
                tags.append('rising')
            
            with open(entity_path) as f:
                content = f.read()
            parts = content.split('---')
            body = '---'.join(parts[2:]).strip() if len(parts) >= 3 else desc
            
            new_fm = f"""---
title: "{repo}"
created: {fm.get('created', TODAY)}
updated: {TODAY}
type: {ptype}
tags: [{', '.join(tags)}]
sources: [raw/trending/{TODAY}.json]
confidence: {confidence}
trending_count_daily: {new_c}
trending_count_weekly: 0
trending_count_monthly: 0
consecutive_days: {new_cons}
first_trending: {first_seen}
last_trending: {TODAY}
peak_rank: {new_peak}
total_stars: {old_total_stars}
language: {lang}
---"""
            with open(entity_path, 'w') as f:
                f.write(f"{new_fm}\n\n{body}\n")
            update_count += 1
        else:
            # Create new
            new_fm = f"""---
title: "{repo}"
created: {TODAY}
updated: {TODAY}
type: {ptype}
tags: [{', '.join(tags)}]
sources: [raw/trending/{TODAY}.json]
confidence: low
trending_count_daily: 1
trending_count_weekly: 0
trending_count_monthly: 0
consecutive_days: 1
first_trending: {TODAY}
last_trending: {TODAY}
peak_rank: {rank}
total_stars: ?
language: {lang}
---"""
            body = f"""# {repo}

{desc}

- 语言: {lang}
- 今日排名: #{rank}
- 今日新增: +{stars_today}⭐
- 链接: [{repo}]({url})
"""
            with open(entity_path, 'w') as f:
                f.write(f"{new_fm}\n\n{body}\n")
            new_count += 1
    
    # Update index.md
    entities = sorted([f for f in os.listdir(ENTITIES_DIR) if f.endswith('.md')])
    total_pages = len(entities)
    
    entity_entries = []
    for fname in entities:
        slug = fname.replace('.md', '')
        fm = read_frontmatter(f'{ENTITIES_DIR}/{fname}')
        title_fm = fm.get('title', slug)
        consecutive = int(fm.get('consecutive_days', '0') or '0')
        
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
        if len(body_lines[0] if body_lines else '') > 60:
            short_desc += '...'
        
        badge = ''
        if consecutive >= 3:
            badge = ' 🔥'
        elif consecutive >= 2 or fm.get('created') == TODAY:
            badge = ' 🆕'
        
        display_name = title_fm.split('/')[-1] if '/' in title_fm else title_fm
        entity_entries.append(f'- [[{slug}|{display_name}]] — {short_desc}{badge}')
    
    index_content = f"""# GitHub Trending Wiki Index

> 内容目录。所有 wiki 页面按类型分组，每条一行：wikilink + 摘要。
> 最后更新：{TODAY} | 总页面：{total_pages}

## Entities

"""
    for entry in sorted(entity_entries):
        index_content += entry + '\n'
    
    index_content += """
## Concepts

- [[agent-skills-ecosystem]] — Agent Skills 生态趋势分析

## Comparisons

<!-- 项目对比分析 -->

## Reports

- [[reports/2026-05-16]] — 首日日报，12 个项目，Agent Skills 生态爆发
- [[reports/2026-05-17]] — 第 2 日日报，12 个项目全部连续上榜
"""
    with open(f'{BASE}/index.md', 'w') as f:
        f.write(index_content)
    
    # Update log.md
    # 统计连续上榜
    consecutive_list = []
    for fname in entities:
        fm = read_frontmatter(f'{ENTITIES_DIR}/{fname}')
        cons = int(fm.get('consecutive_days', '0') or '0')
        if cons >= 2:
            consecutive_list.append((fm.get('title', ''), cons))
    consecutive_list.sort(key=lambda x: -x[1])
    
    # 语言分布
    lang_count = {}
    for p in projects:
        lang = p.get('language', '其他') or '其他'
        lang_count[lang] = lang_count.get(lang, 0) + 1
    
    # star top3
    top3 = sorted(projects, key=lambda x: -int(x.get('stars_today', 0)))[:3]
    
    new_names = []
    for p in projects:
        slug = p['repo'].replace('/', '-').lower()
        if slug + '.md' not in existing:
            new_names.append(p['repo'])
    
    log_entry = f"""
## [{TODAY}] update | GitHub Trending 日报
- 采集 {len(projects)} 个项目（raw/trending/{TODAY}.json）
- 新建 entity: {new_count} 个（{', '.join(new_names[:5])}{'...' if len(new_names) > 5 else ''}）
- 更新 entity: {update_count} 个
- 趋势: {', '.join([f'{l} {c}个' for l, c in sorted(lang_count.items(), key=lambda x: -x[1])[:5]])}
"""
    for repo, days in consecutive_list:
        log_entry += f"- 连续 {days} 天上榜: {repo}\n"
    top3_str = ', '.join([p['repo'] + ' +' + str(p.get('stars_today', 0)) + '⭐' for p in top3])
    log_entry += f"- 当日 star 增长 Top 3: {top3_str}\n"
    
    with open(f'{BASE}/log.md', 'a') as f:
        f.write(log_entry)
    
    print(f"  新建: {new_count}, 更新: {update_count}, 总 entity: {total_pages}")
    return True

# ============ 第三步：Git Commit ============
def git_commit():
    print(f"[3/4] Git commit...")
    env = os.environ.copy()
    env['GIT_SSH_COMMAND'] = 'ssh -o StrictHostKeyChecking=no -i /root/.ssh/id_ed25519'
    result = subprocess.run(
        ['git', 'add', '-A'], cwd=BASE, capture_output=True, text=True, env=env
    )
    result = subprocess.run(
        ['git', 'commit', '-m', f'wiki: {TODAY} compilation'],
        cwd=BASE, capture_output=True, text=True, env=env
    )
    if result.returncode == 0:
        print(f"  Commit 成功")
    else:
        print(f"  Commit 结果: {result.stdout.strip() or result.stderr.strip()[:200]}")
    return True

# ============ 第四步：飞书推送 ============
def push_feishu():
    print(f"[4/4] 飞书推送...")
    
    # 获取 token
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
    
    # 读取数据
    today_file = f'{RAW_DIR}/{TODAY}.json'
    with open(today_file) as f:
        data = json.load(f)
    projects = data.get('projects', [])
    
    # 语言分布
    lang_count = {}
    for p in projects:
        lang = p.get('language', '其他') or '其他'
        lang_count[lang] = lang_count.get(lang, 0) + 1
    top_lang = sorted(lang_count.items(), key=lambda x: -x[1])[:5]
    lang_str = " | ".join([f"{l} {c}个" for l, c in top_lang])
    
    # 连续上榜
    consecutive_info = []
    for p in projects:
        slug = p['repo'].replace('/', '-').lower()
        fm = read_frontmatter(f'{ENTITIES_DIR}/{slug}.md')
        cons = int(fm.get('consecutive_days', '0') or '0')
        if cons >= 2:
            consecutive_info.append((p['repo'], cons, f"+{p.get('stars_today',0)}⭐"))
    consecutive_info.sort(key=lambda x: -x[1])
    
    rows = []
    rows.append([{"tag": "md", "text": f"📊 **GitHub Trending 日报 | {TODAY}**"}])
    rows.append([{"tag": "text", "text": " "}])
    rows.append([{"tag": "md", "text": f"**今日概览**：{len(projects)} 个项目上榜 | 语言分布：{lang_str}"}])
    rows.append([{"tag": "text", "text": " "}])
    
    if consecutive_info:
        rows.append([{"tag": "md", "text": "**🔥 连续上榜**"}])
        for repo, days, stars in consecutive_info:
            name = repo.split('/')[1]
            url = f"https://github.com/{repo}"
            rows.append([{"tag": "md", "text": f"- [{name}]({url}) — 连续 {days} 天 | {stars}"}])
        rows.append([{"tag": "text", "text": " "}])
    
    rows.append([{"tag": "md", "text": f"**📋 完整榜单（{len(projects)} 个项目）**"}])
    for p in projects:
        rank = p.get('rank', '?')
        repo = p['repo']
        name = repo.split('/')[1]
        lang = p.get('language', '?') or '?'
        stars = p.get('stars_today', '?')
        url = p.get('url', f"https://github.com/{repo}")
        rows.append([{"tag": "md", "text": f"#{rank} [{name}]({url}) — {lang} | +{stars}⭐"}])
    
    post_payload = json.dumps({"zh_cn": {"content": rows}}, ensure_ascii=False)
    headers = {"Authorization": f"Bearer {tenant_token}", "Content-Type": "application/json; charset=utf-8"}
    resp = requests.post(
        "https://open.feishu.cn/open-apis/im/v1/messages",
        params={"receive_id_type": "chat_id"},
        headers=headers,
        json={"receive_id": "oc_b269ff6fab6e321a35e344ea5984e985", "msg_type": "post", "content": post_payload},
        timeout=10
    )
    result = resp.json()
    if result.get('code') == 0:
        print(f"  推送成功")
        return True
    else:
        print(f"  推送失败: {result}")
        return False

# ============ Main ============
if __name__ == '__main__':
    if not collect():
        print("[SILENT]")
        sys.exit(1)
    if not compile_wiki():
        sys.exit(1)
    git_commit()
    push_feishu()
    print(f"\n✅ {TODAY} 日报完成")
