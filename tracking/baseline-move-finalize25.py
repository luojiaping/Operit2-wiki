#!/usr/bin/env python3
"""基线前移收尾（第二十五轮）：全部 .status.json 的 source_commit 改为 7a79245，
edge-acceptance-v1 summary 里的基线表述同步，AGENTS.md / AI_USAGE.md /
SCHEMA.md / 首页基线同步更新。只改这些，不动 status /
approved_by / 水位线；各页 .md 正文本身的基线提及按惯例不动（由各页
修订员维护）。本轮事实总数 13603 不变（无增删事实）；各批里程碑不变，
首页 data-count 与里程碑按实测断言；首页同步日期 2026-11-25 -> 2026-11-27。"""
import glob
import json
import re

OLD = "d0f7619"
NEW = "7a79245"
TODAY = "2026-11-27"

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
     "源码基线：`AAswordman/Operit2 @ d0f7619`（2026-11-25）",
     "源码基线：`AAswordman/Operit2 @ 7a79245`（2026-11-27）"),
    ("wiki/AI_USAGE.md",
     "行号以源码钉住的 commit（`d0f7619`）为准",
     "行号以源码钉住的 commit（`7a79245`）为准"),
    ("SCHEMA.md",
     "钉住 `d0f7619`（2026-11-25）",
     "钉住 `7a79245`（2026-11-27）"),
]:
    s = open(f).read()
    assert old in s, f
    open(f, "w").write(s.replace(old, new, 1))
    print(f"baseline text fixed: {f}")

# 4. 首页：基线 hash 按钮 d0f7619 -> 7a79245；同步日期 2026-11-25 -> 2026-11-27；
#    事实总数 13603 不变；各批里程碑不变（按实测断言）
f = "site/index.html"
s = open(f).read()
assert 'data-copy="d0f7619"' in s and ">d0f7619 ⧉<" in s
s = s.replace('data-copy="d0f7619"', 'data-copy="7a79245"', 1)
s = s.replace(">d0f7619 ⧉<", ">7a79245 ⧉<", 1)
assert s.count("<span>2026-11-25</span>") == 1, s.count("<span>2026-11-25</span>")
s = s.replace("<span>2026-11-25</span>", "<span>2026-11-27</span>", 1)
assert 'data-count="13603"' in s
for want in ["10 页 · 878 原子事实", "10 页 · 1539 原子事实",
             "13 页 · 2016 原子事实", "8 页 · 860 原子事实",
             "14 页 · 2209 原子事实", "11 页 · 1194 原子事实",
             "8 页 · 1053 原子事实", "4 页 · 382 原子事实",
             "3 页 · 274 原子事实", "16 页 · 1398 原子事实",
             "18 页 · 1800 原子事实"]:
    assert want in s, want
open(f, "w").write(s)
print("index.html fixed: baseline hash d0f7619 -> 7a79245, date 2026-11-25 -> 2026-11-27; facts 13603 unchanged; all milestones unchanged (asserted)")
