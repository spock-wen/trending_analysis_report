# trending DB 查询样例

数据库默认路径：`data/github_trending.db`（现网 `/srv/www/github-trending-wiki/data/github_trending.db`）。  
权威数据仍是 `raw/trending*`；本库为派生表，可用 `scripts/ingest_trending_raw.py` 重建。

## 按仓近 7 日（日榜）

```sql
-- 替换 :repo
SELECT date, rank, stars_today, total_stars, language
FROM trending_daily
WHERE period = 'daily'
  AND repo_full_name = :repo
  AND date >= date('now', '-7 day')
ORDER BY date DESC;
```

CLI 示例：

```bash
sqlite3 data/github_trending.db \
  "SELECT date, rank, stars_today FROM trending_daily
   WHERE period='daily' AND repo_full_name='Nutlope/hallmark'
     AND date >= date('now','-7 day')
   ORDER BY date DESC;"
```

## 按语言某日

```sql
-- 替换 :day / :lang
SELECT rank, repo_full_name, stars_today, total_stars, description
FROM trending_daily
WHERE period = 'daily'
  AND date = :day
  AND language = :lang
ORDER BY rank;
```

```bash
sqlite3 data/github_trending.db \
  "SELECT rank, repo_full_name, stars_today FROM trending_daily
   WHERE period='daily' AND date='2026-10-26' AND language='TypeScript'
   ORDER BY rank;"
```

## 月榜（monthly_trending）

```sql
SELECT rank, repo_full_name, stars_this_period, language
FROM monthly_trending
WHERE month = '2026-10'
ORDER BY rank;
```

## 周榜（weekly_trending）

```sql
SELECT rank, repo_full_name, weekly_stars, language
FROM weekly_trending
WHERE week_start = '2026-10-19'
ORDER BY rank;
```

## 入库 / 对账

```bash
# 初始化月表（幂等）
python3 scripts/init_monthly_db.py --db data/github_trending.db

# 回填全部 raw → DB（失败不改 raw，可重跑）
python3 scripts/ingest_trending_raw.py --all \
  --db data/github_trending.db --raw-root raw

# 对账（近 14 日窗 + 周/月全量）
python3 scripts/reconcile_trending_db.py \
  --db data/github_trending.db --raw-root raw --window 14 \
  --out /tmp/reconcile-trending.json
```
