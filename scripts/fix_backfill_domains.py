#!/usr/bin/env python3
"""
用真实数据（GitHub API description + topics + language）替换 149 个回填 entity 里猜出来的领域。

做法：
  1. 领域判定 = topics（官方信号，权重最高）+ description 关键词 + language
  2. 只在有依据时写 domain；无依据留空并标 domain_verified: false
  3. 改写 entity frontmatter 的 tags 和正文的「所属领域」
"""
import glob
import json
import os
import re
import sqlite3
import sys

BASE = '/srv/www/github-trending-wiki'
ENT = f'{BASE}/entities'
CONC = f'{BASE}/concepts'

# --- 领域词典：topic -> domain（GitHub 官方 tag 映射，优先） ---
TOPIC_DOMAIN = {
    'ai-agent': 'ai-agent', 'agent': 'ai-agent', 'agentic': 'ai-agent',
    'ai-agents': 'ai-agent', 'llm-agent': 'ai-agent', 'multi-agent': 'ai-agent',
    'autonomous-agents': 'ai-agent', 'mcp': 'ai-agent', 'claude': 'ai-agent',
    'claude-code': 'ai-agent', 'claude-skills': 'ai-agent', 'skills': 'ai-agent',
    'gpt': 'ai-agent', 'llm': 'ai-agent', 'chatbot': 'ai-agent',
    'copilot': 'ai-agent', 'ai': 'ai-agent', 'machine-learning': 'ai-agent',
    'deep-learning': 'ai-agent', 'neural-network': 'ai-agent',
    'rag': 'ai-agent', 'langchain': 'ai-agent', 'langgraph': 'ai-agent',
    'agent-skills': 'ai-agent', 'ai-assistant': 'ai-agent',
    'cli': 'cli', 'terminal': 'cli', 'command-line': 'cli', 'shell': 'cli',
    'console': 'cli', 'zsh': 'cli', 'bash': 'cli',
    'web': 'web', 'browser': 'web', 'frontend': 'web', 'css': 'web',
    'html': 'web', 'chrome': 'web', 'website': 'web', 'http': 'web',
    'react': 'web', 'vue': 'web', 'nextjs': 'web',
    'data': 'data', 'analytics': 'data', 'etl': 'data', 'pipeline': 'data',
    'database': 'data', 'sql': 'data', 'metrics': 'data', 'data-analysis': 'data',
    'devops': 'devops', 'deploy': 'devops', 'infrastructure': 'devops',
    'monitoring': 'devops', 'observability': 'devops', 'ci-cd': 'devops',
    'kubernetes': 'devops', 'docker': 'devops', 'containers': 'devops',
    'security': 'security', 'privacy': 'security', 'encryption': 'security',
    'vpn': 'security', 'firewall': 'security', 'pentest': 'security',
    'education': 'education', 'tutorial': 'education', 'course': 'education',
    'learn': 'education', 'teaching': 'education', 'beginner': 'education',
    'erp': 'erp', 'business': 'erp', 'commerce': 'erp', 'invoice': 'erp',
    'shop': 'erp', 'inventory': 'erp',
    'image-gen': 'image-gen', 'diffusion': 'image-gen', 'stable-diffusion': 'image-gen',
    'image-generation': 'image-gen', 'text-to-image': 'image-gen',
    'audio': 'audio', 'tts': 'audio', 'speech': 'audio', 'voice': 'audio',
    'music': 'audio', 'whisper': 'audio',
    'science': 'science', 'scientific-computing': 'science',
    'bioinformatics': 'science', 'physics': 'science', 'chemistry': 'science',
    'quantum': 'science', 'research': 'science',
    'mobile': 'mobile', 'android': 'mobile', 'ios': 'mobile', 'swift': 'mobile',
    'kotlin': 'mobile', 'flutter': 'mobile', 'harmonyos': 'mobile',
    'game': 'game', 'gaming': 'game', 'vtuber': 'game', 'live2d': 'game',
    'finance': 'finance', 'trading': 'finance', 'quant': 'finance',
    'stock-market': 'finance', 'investment': 'finance',
    'video': 'video', 'ffmpeg': 'video', 'video-generation': 'video',
    'editor': 'video',
    # ML / 推理 / 系统底层（2026-10-04 按回填批次实测补）
    'machine-learning': 'ai-agent', 'ml': 'ai-agent', 'ml-engineer': 'ai-agent',
    'deep-learning': 'ai-agent', 'transformer': 'ai-agent', 'pytorch': 'ai-agent',
    'tensorflow': 'ai-agent', 'jax': 'ai-agent', 'cuda': 'ai-agent',
    'gpu': 'ai-agent', 'inference': 'ai-agent', 'llm-inference': 'ai-agent',
    'vllm': 'ai-agent', 'quantization': 'ai-agent', '1-bit-llm': 'ai-agent',
    'llama': 'ai-agent', 'qwen': 'ai-agent', 'deepseek': 'ai-agent',
    'fine-tuning': 'ai-agent', 'model-training': 'ai-agent',
    'graphrag': 'ai-agent', 'knowledge-graph': 'ai-agent',
    'nlp': 'ai-agent', 'natural-language-processing': 'ai-agent',
    'compiler': 'devops', 'compilers': 'devops', 'toolchain': 'devops',
    'build-tool': 'devops', 'transpiler': 'devops',
    'systemd': 'devops', 'linux': 'devops', 'init-system': 'devops',
    'service-manager': 'devops', 'embedded': 'devops', 'router': 'devops',
    'screenshot': 'tool', 'screen-recorder': 'tool', 'utility': 'tool',
    'desktop-app': 'tool', 'windows': 'tool', 'minecraft': 'game',
    'emulator': 'game', 'emulation': 'game', 'gaussian-splatting': 'image-gen',
    '3d': 'image-gen', '3d-reconstruction': 'image-gen', 'nerf': 'image-gen',
    'forensics': 'security', 'digital-forensics': 'security',
    'penetration-testing': 'security', 'hacking': 'security',
    'adblock': 'web', 'browser-extension': 'web',
}

# --- description 关键词（权重低于 topics） ---
DESC_KEYWORDS = {
    'ai-agent': ['agent', 'agentic', 'mcp', 'skill', 'claude', 'gpt', 'llm',
                 'copilot', 'autonomous', 'chatbot', 'rag', 'langchain'],
    'cli': ['cli', 'terminal', 'command-line', 'command line', 'console', 'shell'],
    'web': ['browser', 'web', 'frontend', 'http', 'css', 'html', 'chrome', 'react'],
    'data': ['data', 'analytics', 'etl', 'pipeline', 'database', 'sql', 'metric'],
    'devops': ['deploy', 'infra', 'monitor', 'observability', 'devops', 'ci/cd',
               'kubernetes', 'docker'],
    'security': ['security', 'privacy', 'encrypt', 'vpn', 'firewall', 'pentest'],
    'education': ['tutorial', 'beginner', 'course', 'learn', 'teach', '从零开始'],
    'image-gen': ['diffusion', 'image generation', 'text-to-image', 'stable diffusion'],
    'audio': ['tts', 'speech', 'voice', 'whisper', 'audio', 'music'],
    'science': ['scientific', 'bioinformatics', 'physics', 'chemistry', 'quantum',
                'genomics', 'proteomics'],
    'finance': ['trading', 'hedge fund', 'quant', 'stock', 'investment', 'backtest'],
    'video': ['video', 'ffmpeg', 'rendering', 'render'],
    'game': ['vtuber', 'live2d', 'game', 'gaming'],
    'mobile': ['android', 'ios', 'swift', 'kotlin', 'flutter', 'mobile'],
    'tool': ['tool', 'utility', 'toolkit', 'setup', 'screenshot', 'screen recorder'],
    'security': ['hacking tool', 'hacker', 'penetration', 'forensic', 'blocker'],
    'web': ['browser extension', 'chromium', 'firefox', 'ublock'],
    'devops': ['compiler', 'toolchain', 'transpiler', 'runtime', 'service manager',
               'smart contract', 'blockchain', 'init system'],
    'image-gen': ['3d reconstruction', 'gaussian splat', 'nerf', 'photogrammetry'],
    'game': ['vtuber', 'live2d', 'game', 'gaming', 'emulator', 'minecraft'],
}


def detect(repo, topics, desc, lang):
    """返回 (domains, evidence) —— evidence 记录判据，便于审计。"""
    doms = set()
    ev = []
    # 1) topics 优先
    for t in (topics or []):
        d = TOPIC_DOMAIN.get(t.lower())
        if d:
            doms.add(d)
            ev.append(f'topic:{t}')
    # 2) description 关键词
    dl = (desc or '').lower()
    for d, kws in DESC_KEYWORDS.items():
        if any(k in dl for k in kws):
            if d not in doms:
                doms.add(d)
                ev.append(f'desc:{d}')

    if doms:
        return sorted(doms), '; '.join(ev[:4])
    # 3) 无依据 —— 不猜
    return [], 'no-evidence'


def main():
    # 真实数据源
    api = json.load(open('/tmp/api_topics.json'))
    dr = {}
    for f in sorted(glob.glob('/srv/www/daily-report/data/briefs/daily/data-*.json')):
        j = json.load(open(f))
        for p in j.get('projects', []):
            r = p.get('repo')
            if not r:
                continue
            t = p.get('topics') or []
            if r not in dr or len(t) > len(dr[r].get('topics') or []):
                dr[r] = {'topics': t, 'desc': p.get('desc') or p.get('descZh'),
                         'language': p.get('language')}

    conn = sqlite3.connect(f'{BASE}/data/github_trending.db')
    conn.row_factory = sqlite3.Row

    # 找到带 source_backfill 标记的 entity
    targets = []
    for f in os.listdir(ENT):
        if not f.endswith('.md'):
            continue
        txt = open(f'{ENT}/{f}', encoding='utf-8').read()
        if 'source_backfill: true' in txt:
            targets.append(f)
    print(f"待处理 entity: {len(targets)}")

    stats = {'topics': 0, 'desc': 0, 'none': 0, 'api_used': 0}
    changed = 0
    for f in targets:
        path = f'{ENT}/{f}'
        txt = open(path, encoding='utf-8').read()
        repo = txt.split('"')[1]

        # 优先 API 真实数据，其次 daily-report 快照
        src_api = api.get(repo, {})
        if src_api.get('found') and (src_api.get('topics') or src_api.get('description')):
            topics = src_api.get('topics')
            desc = src_api.get('description')
            lang = src_api.get('language')
            src = 'github-api'
            stats['api_used'] += 1
        else:
            d = dr.get(repo, {})
            topics = d.get('topics')
            desc = d.get('desc')
            lang = d.get('language')
            src = 'daily-report'

        doms, ev = detect(repo, topics, desc, lang)
        # ev 是分号拼接字符串；只有以 topic: 开头才算官方 tag 依据
        first_ev = ev.split(';')[0].strip() if ev else ''
        if first_ev.startswith('topic:'):
            stats['topics'] += 1
        elif doms:
            stats['desc'] += 1
        else:
            stats['none'] += 1

        # 写回 frontmatter tags（语言 tag 保留，领域 tag 用真实判定）
        lang_tag = {'python': 'python', 'rust': 'rust', 'typescript': 'typescript',
                    'go': 'go', 'java': 'java', 'c++': 'cpp', 'shell': 'shell',
                    'zig': 'zig', 'kotlin': 'kotlin', 'swift': 'swift',
                    'c': 'c', 'javascript': 'javascript'}.get((lang or '').lower())
        tags = ([lang_tag] if lang_tag else []) + doms
        if not tags:
            tags = ['tool']

        # domain_verified：证据含 topic 即 true（ev 是分号拼接的字符串，不能逐字符遍历）
        verified = ('topic:' in ev.split(';')[0]) if ev else False

        # 替换 tags 行
        txt = re.sub(r'^tags: \[.*\]$', f'tags: [{", ".join(tags)}]',
                     txt, count=1, flags=re.M)
        # 在 frontmatter 末尾（第二个 --- 之前）插入 domain 元数据
        meta = (f'domain_verified: {str(verified).lower()}\n'
                f'domain_evidence: "{ev}"\n'
                f'domain_source: {src}\n')
        if 'domain_verified:' not in txt:
            # 文件形如 "---\n<frontmatter>\n---\n\n<body>"，只需切出 frontmatter 结束处
            head, sep, rest = txt.partition('\n---\n')
            if sep and head.startswith('---\n'):
                txt = head + '\n' + meta + '---\n' + rest

        # 正文「所属领域」段（替换原 wikilink 形式；不存在则追加）
        dom_str = '、'.join(doms) if doms else '（无可靠依据，未判定）'
        line = f'**所属领域**: {dom_str}'
        txt = re.sub(r'\*\*所属领域\*\*: .*', line, txt, count=1)
        if '所属领域' not in txt:
            txt = txt.rstrip() + f'\n\n{line}\n'

        open(path, 'w', encoding='utf-8').write(txt)
        changed += 1

    print(f"改写 {changed} 个 entity")
    print(f"  判据来源: topics {stats['topics']} | 仅 desc {stats['desc']} | 无依据 {stats['none']}")
    print(f"  用了 GitHub API 实时数据: {stats['api_used']}")


if __name__ == '__main__':
    main()
