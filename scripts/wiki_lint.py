#!/usr/bin/env python3
"""
GitHub Trending Wiki Lint / Health Check
检查 wiki 健康状态，输出报告。

用法：
  python3 wiki_lint.py              # 运行检查并输出报告
  python3 wiki_lint.py --fix        # 自动修复可修复的问题
"""

import os
import re
import sys
from datetime import datetime, timedelta

WIKI_PATH = "/srv/www/github-trending-wiki"
ENTITIES_DIR = os.path.join(WIKI_PATH, "entities")
CONCEPTS_DIR = os.path.join(WIKI_PATH, "concepts")
REPORTS_DIR = os.path.join(WIKI_PATH, "reports")

REQUIRED_FRONTMATTER = ['title', 'created', 'updated', 'type', 'tags', 'confidence']
VALID_TYPES = ['entity', 'concept', 'comparison', 'query', 'tool', 'framework', 'tutorial', 'library', 'app', 'model', 'dataset', 'benchmark', 'awesome-list']
VALID_CONFIDENCE = ['high', 'medium', 'low']

# Tag taxonomy (from SCHEMA.md)
VALID_TAGS = {
    'ai-agent', 'llm', 'web', 'cli', 'mobile', 'data', 'devops', 'security', 'game',
    'blockchain', 'iot', 'ar-vr', 'education', 'healthcare', 'finance',
    'rust', 'python', 'typescript', 'go', 'java', 'cpp', 'c', 'zig', 'ruby', 'php',
    'swift', 'kotlin', 'dart', 'shell',
    'framework', 'tool', 'library', 'app', 'model', 'dataset', 'benchmark', 'tutorial', 'awesome-list',
    'trending', 'rising', 'viral', 'new', 'returning', 'github'
}


def get_all_wiki_pages():
    """获取所有 wiki 页面路径"""
    pages = []
    for d in [ENTITIES_DIR, CONCEPTS_DIR]:
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith('.md') and not f.startswith('.'):
                    pages.append(os.path.join(d, f))
    return pages


def parse_frontmatter(content):
    """解析 YAML frontmatter"""
    if not content.startswith('---'):
        return None
    end = content.find('---', 3)
    if end == -1:
        return None
    fm_text = content[3:end].strip()
    fm = {}
    for line in fm_text.split('\n'):
        if ':' in line:
            key, _, value = line.partition(':')
            fm[key.strip()] = value.strip()
    return fm


def extract_wikilinks(content):
    """提取所有 [[wikilinks]]"""
    return re.findall(r'\[\[([^\]]+)\]\]', content)


def lint_pages():
    """运行所有 lint 检查"""
    issues = {'critical': [], 'warning': [], 'info': []}
    pages = get_all_wiki_pages()
    page_slugs = {os.path.splitext(os.path.basename(p))[0]: p for p in pages}

    # 收集所有 wikilinks
    all_links = {}  # slug -> [linking_slugs]
    for page_path in pages:
        slug = os.path.splitext(os.path.basename(page_path))[0]
        content = open(page_path, encoding='utf-8').read()
        links = extract_wikilinks(content)
        all_links[slug] = links

    # 1. 孤立页面检查
    linked_slugs = set()
    for links in all_links.values():
        linked_slugs.update(links)
    for slug in page_slugs:
        if slug not in linked_slugs and slug != 'index':
            inbound = sum(1 for links in all_links.values() if slug in links)
            if inbound == 0:
                issues['warning'].append(f"孤立页面: {slug} — 没有其他页面引用")

    # 2. 断裂链接检查
    for source_slug, links in all_links.items():
        for link in links:
            if link not in page_slugs:
                issues['critical'].append(f"断裂链接: {source_slug} → [[{link}]] 目标不存在")

    # 3. 索引完整性
    index_path = os.path.join(WIKI_PATH, "index.md")
    if os.path.exists(index_path):
        index_content = open(index_path, encoding='utf-8').read()
        for slug in page_slugs:
            if slug not in index_content:
                issues['warning'].append(f"索引缺失: {slug} 未出现在 index.md 中")

    # 4. Frontmatter 验证
    for page_path in pages:
        fname = os.path.basename(page_path)
        content = open(page_path, encoding='utf-8').read()
        fm = parse_frontmatter(content)

        if fm is None:
            issues['critical'].append(f"缺少 frontmatter: {fname}")
            continue

        for field in REQUIRED_FRONTMATTER:
            if field not in fm:
                issues['warning'].append(f"缺少字段 {field}: {fname}")

        if fm.get('type') not in VALID_TYPES:
            issues['warning'].append(f"无效 type '{fm.get('type')}': {fname}")

        if fm.get('confidence') not in VALID_CONFIDENCE:
            issues['warning'].append(f"无效 confidence '{fm.get('confidence')}': {fname}")

        # 检查 tags
        tags_str = fm.get('tags', '')
        if tags_str:
            tags = [t.strip() for t in tags_str.strip('[]').split(',')]
            for tag in tags:
                if tag and tag not in VALID_TAGS:
                    issues['info'].append(f"未注册 tag '{tag}': {fname}")

    # 5. 过期内容检查
    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    for page_path in pages:
        fname = os.path.basename(page_path)
        content = open(page_path, encoding='utf-8').read()
        fm = parse_frontmatter(content)
        if fm and fm.get('updated', '9999') < cutoff:
            issues['info'].append(f"过期内容 (>30天): {fname} (updated: {fm.get('updated')})")

    # 6. 矛盾页面检查
    for page_path in pages:
        fname = os.path.basename(page_path)
        content = open(page_path, encoding='utf-8').read()
        fm = parse_frontmatter(content)
        if fm and fm.get('contested') == 'true':
            issues['warning'].append(f"矛盾页面需审查: {fname}")

    # 7. 页面大小检查
    for page_path in pages:
        fname = os.path.basename(page_path)
        line_count = len(open(page_path, encoding='utf-8').readlines())
        if line_count > 200:
            issues['info'].append(f"页面过大 ({line_count} 行): {fname} — 考虑拆分")

    # 8. 来源标注检查
    for page_path in pages:
        fname = os.path.basename(page_path)
        content = open(page_path, encoding='utf-8').read()
        if content.count('## ') >= 5 and '^[' not in content:
            issues['info'].append(f"缺少来源标注: {fname} — 多章节页面建议添加 provenance markers")

    # 9. 矛盾页面超期检查（contested > 30 天未解决 → critical）
    contested_cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    for page_path in pages:
        fname = os.path.basename(page_path)
        content = open(page_path, encoding='utf-8').read()
        fm = parse_frontmatter(content)
        if fm and fm.get('contested') == 'true':
            updated = fm.get('updated', '9999')
            if updated < contested_cutoff:
                issues['critical'].append(f"矛盾页面超期 (>30天未解决): {fname} (updated: {updated}) — 需要人工审查并解决")

    # 10. DB vs Markdown 一致性检查
    try:
        import sqlite3
        db_path = os.path.join(WIKI_PATH, "data", "github_trending.db")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.execute('SELECT repo_full_name, consecutive_days, trending_count_daily, last_seen FROM repo_stats')
            db_data = {row[0]: {'consecutive_days': row[1], 'count': row[2], 'last_seen': row[3]} for row in cursor.fetchall()}
            conn.close()
            
            for page_path in pages:
                fname = os.path.basename(page_path)
                if not fname.endswith('.md') or not os.path.dirname(page_path).endswith('entities'):
                    continue
                content = open(page_path, encoding='utf-8').read()
                fm = parse_frontmatter(content)
                if not fm or 'title' not in fm:
                    continue
                title = fm.get('title', '').strip('"')
                if title not in db_data:
                    continue
                db = db_data[title]
                md_cons = int(fm.get('consecutive_days', '0') or '0')
                md_count = int(fm.get('trending_count_daily', '0') or '0')
                md_last = fm.get('last_trending', '')
                if db['consecutive_days'] != md_cons or db['count'] != md_count or db['last_seen'] != md_last:
                    issues['critical'].append(
                        f"DB/MD不一致: {fname} — DB(cons={db['consecutive_days']},count={db['count']},last={db['last_seen']}) "
                        f"vs MD(cons={md_cons},count={md_count},last={md_last})"
                    )
    except Exception as e:
        issues['warning'].append(f"DB一致性检查失败: {e}")

    return issues


def generate_report(issues):
    """生成 lint 报告"""
    total = sum(len(v) for v in issues.values())
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# Wiki Lint Report | {now}",
        "",
        f"**总问题数：** {total}",
        f"- 🔴 Critical: {len(issues['critical'])}",
        f"- 🟡 Warning: {len(issues['warning'])}",
        f"- 🔵 Info: {len(issues['info'])}",
        ""
    ]

    if issues['critical']:
        lines.append("## 🔴 Critical")
        for item in issues['critical']:
            lines.append(f"- {item}")
        lines.append("")

    if issues['warning']:
        lines.append("## 🟡 Warning")
        for item in issues['warning']:
            lines.append(f"- {item}")
        lines.append("")

    if issues['info']:
        lines.append("## 🔵 Info")
        for item in issues['info']:
            lines.append(f"- {item}")
        lines.append("")

    if total == 0:
        lines.append("✅ 所有检查通过，无问题。")

    return '\n'.join(lines)


def main():
    fix_mode = '--fix' in sys.argv

    print("=== GitHub Trending Wiki Lint ===")
    issues = lint_pages()
    report = generate_report(issues)

    # 输出到终端
    print(report)

    # 保存报告
    os.makedirs(REPORTS_DIR, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    report_path = os.path.join(REPORTS_DIR, f"lint-{date_str}.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n报告已保存: {report_path}")

    total = sum(len(v) for v in issues.values())
    if total > 0:
        print(f"\n⚠️ 发现 {total} 个问题，请检查并修复。")
        sys.exit(1)
    else:
        print("\n✅ 无问题。")
        sys.exit(0)


if __name__ == "__main__":
    main()
