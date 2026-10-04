#!/usr/bin/env python3
"""
把缺失的 entity 补进 index.md / log.md。

不整篇重写索引（会丢掉现有序和标记），只：
  - 找出 entities/ 里有但 index.md 里没有的 slug
  - 按字母序插入到 Entities 段的正确位置
  - log.md 追加回填记录
"""
import os
import re
import sqlite3
import argparse

BASE = '/srv/www/github-trending-wiki'
ENT = f'{BASE}/entities'
INDEX = f'{BASE}/index.md'
LOG = f'{BASE}/log.md'
DB = f'{BASE}/data/github_trending.db'


def short_desc(desc, limit=90):
    d = (desc or 'No description').strip().replace('\n', ' ')
    d = re.sub(r'\s+', ' ', d)
    return d[:limit] + ('...' if len(d) > limit else '')


def main(dry_run):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    stats = {r['repo_full_name']: dict(r) for r in conn.execute('SELECT * FROM repo_stats')}
    conn.close()

    have = {f[:-3] for f in os.listdir(ENT) if f.endswith('.md')}
    idx = open(INDEX, encoding='utf-8').read()

    # 现有索引里的 slug
    in_index = set(re.findall(r'- \[\[([a-z0-9._-]+)\|', idx))
    missing = sorted(have - in_index)
    print(f"entity {len(have)} 个，索引已有 {len(in_index)}，缺失 {len(missing)} 个")

    if not missing:
        print("无缺失")
        return

    # 构造新行（沿用历史格式：[[slug|shortname"]] — desc）
    lines = []
    for slug in missing:
        # slug -> repo_full_name
        cand = [r for r in stats if r.replace('/', '-').lower() == slug]
        desc = stats[cand[0]]['description'] if cand else ''
        name = slug.split('-', 1)[1] if '-' in slug else slug
        lines.append(f'- [[{slug}|{name}"]] — {short_desc(desc)} 🆕')

    if dry_run:
        print(f"\n[DRY-RUN] 将插入 {len(lines)} 行，抽样 5 行：")
        for l in lines[:5]:
            print(' ', l)
        return

    # 插入到 Entities 段末尾（Concepts 段之前），保持简单可控
    m = re.search(r'\n## (Concepts|实体|索引)', idx)
    if m:
        pos = m.start()
        new_idx = idx[:pos] + '\n'.join(lines) + '\n' + idx[pos:]
    else:
        new_idx = idx.rstrip() + '\n' + '\n'.join(lines) + '\n'

    # 更新总数标注
    total = len(have)
    new_idx = re.sub(r'\| 总页面：\d+', f'| 总页面：{total}', new_idx)
    new_idx = re.sub(r'最后更新：\d{4}-\d{2}-\d{2}', '最后更新：2026-10-04', new_idx)

    open(INDEX, 'w', encoding='utf-8').write(new_idx)
    print(f"index.md 已更新，总页面 {total}")

    # log.md 追加
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(f"\n## 2026-10-04 回填 daily-report 历史数据 (2026-03-04 ~ 2026-05-15)\n\n")
        f.write(f"- 新增 trending_daily 626 行 / 66 天；repo_stats 636 → 788；entity 636 → 788\n")
        f.write(f"- 日期归属规则：generatedAt + 8h（daily-report date 为 UTC 目标日，快照在北京次日早晨）\n")
        f.write(f"- 删除伪造的 2026-05-17（5/16 逐字节复制），用 daily-report 真实 8 条补回\n")
        f.write(f"- 周榜未回填（回填期日均 8.8 项 vs wiki 12~17 项，口径不可比）\n")
        f.write(f"- rank 为数组下标推断，19 行 language 为 NULL，均已标注 rank_inferred\n")
    print("log.md 已追加")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    main(ap.parse_args().dry_run)
