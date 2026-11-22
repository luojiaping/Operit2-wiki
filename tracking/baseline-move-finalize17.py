#!/usr/bin/env python3
"""基线前移收尾（第十七轮）：全部 .status.json 的 source_commit 改为 a7920ad，
edge-acceptance-v1 summary 里的基线表述同步，AGENTS.md / AI_USAGE.md /
SCHEMA.md / 首页基线同步更新。只改这些，不动 status /
approved_by / 水位线；各页 .md 正文本身的基线提及按惯例不动（由各页
修订员维护）。本轮事实总数 13604 不变（只修行号与 1 处错锚，无增删）；
各批里程碑全部不变，首页 data-count 与里程碑按实测断言。"""
import glob
import json
import re

OLD = "ab6508d"
NEW = "a7920ad"
TODAY = "2026-11-22"

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
     "源码基线：`AAswordman/Operit2 @ ab6508d`（2026-11-22）",
     "源码基线：`AAswordman/Operit2 @ a7920ad`（2026-11-22）"),
    ("wiki/AI_USAGE.md",
     "行号以源码钉住的 commit（`ab6508d`）为准",
     "行号以源码钉住的 commit（`a7920ad`）为准"),
    ("SCHEMA.md",
     "钉住 `ab6508d`（2026-11-22）",
     "钉住 `a7920ad`（2026-11-22）"),
]:
    s = open(f).read()
    assert old in s, f
    open(f, "w").write(s.replace(old, new, 1))
    print(f"baseline text fixed: {f}")

# 4. 首页：基线 hash 按钮；日期已是 2026-11-22 不变；事实总数 13604 不变；
#    各批里程碑全部不变，按实测断言
f = "site/index.html"
s = open(f).read()
assert 'data-copy="ab6508d"' in s and ">ab6508d ⧉<" in s
s = s.replace('data-copy="ab6508d"', 'data-copy="a7920ad"', 1)
s = s.replace(">ab6508d ⧉<", ">a7920ad ⧉<", 1)
assert 'data-count="13604"' in s
for want in ["10 页 · 878 原子事实", "10 页 · 1539 原子事实",
             "13 页 · 2016 原子事实", "8 页 · 860 原子事实",
             "14 页 · 2209 原子事实", "11 页 · 1194 原子事实",
             "8 页 · 1053 原子事实", "4 页 · 382 原子事实",
             "3 页 · 274 原子事实", "16 页 · 1398 原子事实",
             "18 页 · 1801 原子事实"]:
    assert want in s, want
open(f, "w").write(s)
print("index.html fixed: baseline hash ab6508d -> a7920ad; facts 13604 unchanged; all milestones unchanged (asserted)")
