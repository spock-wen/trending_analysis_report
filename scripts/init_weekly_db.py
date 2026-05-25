#!/usr/bin/env python3
"""初始化 weekly_trending 表"""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'github_trending.db')

conn = sqlite3.connect(DB_PATH)
conn.execute('''
    CREATE TABLE IF NOT EXISTS weekly_trending (
        week_start TEXT NOT NULL,
        week_end TEXT NOT NULL,
        repo_full_name TEXT NOT NULL,
        rank INTEGER,
        weekly_stars INTEGER,
        description TEXT,
        language TEXT,
        PRIMARY KEY (week_start, repo_full_name)
    )
''')
conn.commit()
conn.close()
print("weekly_trending table ready")
