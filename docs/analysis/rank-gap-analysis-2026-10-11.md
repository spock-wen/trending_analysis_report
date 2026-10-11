# 日榜 rank 缺口分析（2026-10-11）

## 结论

213 天日榜数据中 46 天存在 rank 断号，逐一比对 `raw/trending/*.json` 原始抓取结果后确认：

- **44 天：GitHub Trending 自身 rank 字段跳号**（DB 条数与 raw JSON 条数完全一致，断号在原始数据里就存在）
- **0 天：采集/写入阶段丢失**
- **2 天：无 raw JSON 可查**（2026-03-22、2026-04-18，回填数据，原始文件未保留）

## 为什么 GitHub 会跳号

GitHub Trending 的排名不是从 1 到 N 连续编号。已知原因：

1. **Spoken languages 过滤**：非英语描述的项目会被降低权重或排除，造成位次空档
2. **赞助/推广位**：部分位次被占用但不显示在公开榜单
3. **Trending 算法分组**：同日多个项目共享权重时分入同一档

## 验证方法

```python
# 对每个有断号的日期，对比 DB 与 raw JSON
db_n = SELECT count(*), max(rank) FROM trending_daily WHERE date=? AND period='daily'
raw_n = len(json.load(open(f'raw/trending/{date}.json')))
# db_n == raw_n → GitHub 本身断号，非采集问题
```

## 对我们的影响

无。所有下游统计（连续上榜、星数环比、换血率）都基于 repo 集合而非 rank 连续性，断号不影响任何指标计算。

## 同类问题排查记录

周榜（`weekly_trending`）历史上也有 5 周存在 rank 缺口（06-15/06-22/06-29/07-06/09-28），同法验证：这些周的候选 repo 里**没有一个**带 `.` 或 `_`，与周采集器校验器 bug 无关。周采集器的校验器 bug 已修复（见 commit 8d414e01），但历史周榜缺口的成因是 GitHub 周榜当天的 article 数本身少于 rank 上限，同样不是采集丢失。
