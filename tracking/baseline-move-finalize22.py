#!/usr/bin/env python3
"""基线前移收尾（第二十二轮）：全部 .status.json 的 source_commit 改为 62dacc0，
edge-acceptance-v1 summary 里的基线表述同步，AGENTS.md / AI_USAGE.md /
SCHEMA.md / 首页基线同步更新。只改这些，不动 status /
approved_by / 水位线；各页 .md 正文本身的基线提及按惯例不动（由各页
修订员维护）。本轮事实总数 13604 -> 13603（dev-contributing 删 1 条
DCO 事实）；batch-11 里程碑 1801 -> 1800，其余各批不变，首页
data-count 与里程碑按实测断言。"""
import glob
import json
import re

OLD = "805120c"
NEW = "62dacc0"
TODAY = "2026-11-25"

# 1. 116 个 .status.json
n = 0
for f in sorted(glob.glob("review/*/*.status.json")):
    d = json.load(open(f))
    assert d["source_commit"] == OLD, f
    assert d["status"] == "approved", f
    d["source_commit"] = NEW
    d["updated"] = TODAY
    if "summary" in d and OLD in d["summary"]:
        d["summary"] = d["summary"].replace(OLD, NEW)
        print(f"summary fixed: {f}")
    json.dump(d, open(f, "w"), ensure_ascii=False, indent=2)
    open(f, "a").write("\n")
    n += 1
print(f"status.json updated: {n}")

# 2. 条目 .md frontmatter date 必须全是 2026-11-11（本轮无人改过）
bad = []
for f in sorted(glob.glob("review/*/*.md")):
    if f.endswith(".critic.md"):
        continue
    m = re.search(r"^date: (.+)$", open(f).read(), re.M)
    if not m or m.group(1) != "2026-11-11":
        bad.append((f, m.group(1) if m else None))
assert not bad, bad
print("frontmatter dates: all 2026-11-11, nothing to fix")

# 3. 基线表述
for f, old, new in [
    ("AGENTS.md",
     "源码基线：`AAswordman/Operit2 @ 805120c`（2026-11-23）",
     "源码基线：`AAswordman/Operit2 @ 62dacc0`（2026-11-25）"),
    ("wiki/AI_USAGE.md",
     "行号以源码钉住的 commit（`805120c`）为准",
     "行号以源码钉住的 commit（`62dacc0`）为准"),
    ("SCHEMA.md",
     "钉住 `805120c`（2026-11-23）",
     "钉住 `62dacc0`（2026-11-25）"),
]:
    s = open(f).read()
    assert old in s, f
    open(f, "w").write(s.replace(old, new, 1))
    print(f"baseline text fixed: {f}")

# 4. 首页：基线 hash 按钮；日期 2026-11-23 -> 2026-11-25；
#    事实总数 13604 -> 13603；batch-11 里程碑 1801 -> 1800，其余不变
f = "site/index.html"
s = open(f).read()
assert 'data-copy="805120c"' in s and ">805120c ⧉<" in s
s = s.replace('data-copy="805120c"', 'data-copy="62dacc0"', 1)
s = s.replace(">805120c ⧉<", ">62dacc0 ⧉<", 1)
assert s.count("<span>2026-11-23</span>") == 1, s.count("<span>2026-11-23</span>")
s = s.replace("<span>2026-11-23</span>", "<span>2026-11-25</span>", 1)
assert 'data-count="13604"' in s
s = s.replace('data-count="13604"', 'data-count="13603"', 1)
assert "18 页 · 1801 原子事实" in s
s = s.replace("18 页 · 1801 原子事实", "18 页 · 1800 原子事实", 1)
for want in ["10 页 · 878 原子事实", "10 页 · 1539 原子事实",
             "13 页 · 2016 原子事实", "8 页 · 860 原子事实",
             "14 页 · 2209 原子事实", "11 页 · 1194 原子事实",
             "8 页 · 1053 原子事实", "4 页 · 382 原子事实",
             "3 页 · 274 原子事实", "16 页 · 1398 原子事实"]:
    assert want in s, want
open(f, "w").write(s)
print("index.html fixed: baseline hash 805120c -> 62dacc0, date 2026-11-23 -> 2026-11-25; facts 13604 -> 13603; batch-11 milestone 1801 -> 1800, others unchanged (asserted)")
