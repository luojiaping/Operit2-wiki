#!/usr/bin/env python3
"""基线前移收尾（第十二轮）：全部 .status.json 的 source_commit 改为 7fdb667，
edge-acceptance-v1 summary 里的基线表述同步，AGENTS.md / AI_USAGE.md /
SCHEMA.md / 首页基线同步更新。只改这些，不动 status /
approved_by / 水位线；各页 .md 正文本身的基线提及按惯例不动（由各页
修订员维护）。本轮事实总数 13609 → 13603（tools-peer-protocol-check
-5、core-node-runtime -1），里程碑 batch-03 2017→2016、batch-11
1806→1801，其余各批不变，首页 data-count 与里程碑按实测全改。"""
import glob
import json
import re

OLD = "c4d47c7"
NEW = "7fdb667"
TODAY = "2026-11-21"

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
     "源码基线：`AAswordman/Operit2 @ c4d47c7`（2026-11-20）",
     "源码基线：`AAswordman/Operit2 @ 7fdb667`（2026-11-21）"),
    ("wiki/AI_USAGE.md",
     "行号以源码钉住的 commit（`c4d47c7`）为准",
     "行号以源码钉住的 commit（`7fdb667`）为准"),
    ("SCHEMA.md",
     "钉住 `c4d47c7`（2026-11-20）",
     "钉住 `7fdb667`（2026-11-21）"),
]:
    s = open(f).read()
    assert old in s, f
    open(f, "w").write(s.replace(old, new, 1))
    print(f"baseline text fixed: {f}")

# 4. 首页：基线 hash 按钮；日期 2026-11-20 → 2026-11-21；事实总数
#    13609 → 13603；里程碑 batch-03 2017→2016、batch-11 1806→1801，
#    其余各批断言不变
f = "site/index.html"
s = open(f).read()
assert 'data-copy="c4d47c7"' in s and ">c4d47c7 ⧉<" in s
s = s.replace('data-copy="c4d47c7"', 'data-copy="7fdb667"', 1)
s = s.replace(">c4d47c7 ⧉<", ">7fdb667 ⧉<", 1)
assert "<span>2026-11-20</span>" in s
s = s.replace("<span>2026-11-20</span>", "<span>2026-11-21</span>", 1)
assert 'data-count="13609"' in s
s = s.replace('data-count="13609"', 'data-count="13603"', 1)
assert "13 页 · 2017 原子事实" in s
s = s.replace("13 页 · 2017 原子事实", "13 页 · 2016 原子事实", 1)
assert "18 页 · 1806 原子事实" in s
s = s.replace("18 页 · 1806 原子事实", "18 页 · 1801 原子事实", 1)
for want in ["10 页 · 878 原子事实", "10 页 · 1540 原子事实",
             "8 页 · 860 原子事实", "14 页 · 2209 原子事实",
             "11 页 · 1192 原子事实", "8 页 · 1053 原子事实",
             "4 页 · 382 原子事实", "3 页 · 274 原子事实",
             "16 页 · 1398 原子事实"]:
    assert want in s, want
open(f, "w").write(s)
print("index.html fixed: baseline hash c4d47c7 -> 7fdb667; date 2026-11-20 -> 2026-11-21; facts 13609 -> 13603; milestones batch-03 2016, batch-11 1801, others unchanged (asserted)")
