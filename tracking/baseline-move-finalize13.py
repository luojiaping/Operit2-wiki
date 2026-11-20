#!/usr/bin/env python3
"""基线前移收尾（第十三轮）：全部 .status.json 的 source_commit 改为 2dafe6b，
edge-acceptance-v1 summary 里的基线表述同步，AGENTS.md / AI_USAGE.md /
SCHEMA.md / 首页基线同步更新。只改这些，不动 status /
approved_by / 水位线；各页 .md 正文本身的基线提及按惯例不动（由各页
修订员维护）。本轮事实总数 13603 → 13605（plugin-catalog-buildin +2，
docs_editor 目录自洽新增），里程碑 batch-06 1192→1194，其余各批不变，
首页 data-count 与里程碑按实测全改。"""
import glob
import json
import re

OLD = "7fdb667"
NEW = "2dafe6b"
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
     "源码基线：`AAswordman/Operit2 @ 7fdb667`（2026-11-21）",
     "源码基线：`AAswordman/Operit2 @ 2dafe6b`（2026-11-21）"),
    ("wiki/AI_USAGE.md",
     "行号以源码钉住的 commit（`7fdb667`）为准",
     "行号以源码钉住的 commit（`2dafe6b`）为准"),
    ("SCHEMA.md",
     "钉住 `7fdb667`（2026-11-21）",
     "钉住 `2dafe6b`（2026-11-21）"),
]:
    s = open(f).read()
    assert old in s, f
    open(f, "w").write(s.replace(old, new, 1))
    print(f"baseline text fixed: {f}")

# 4. 首页：基线 hash 按钮；日期已是 2026-11-21 不动；事实总数
#    13603 → 13605；里程碑 batch-06 1192→1194，其余各批断言不变
f = "site/index.html"
s = open(f).read()
assert 'data-copy="7fdb667"' in s and ">7fdb667 ⧉<" in s
s = s.replace('data-copy="7fdb667"', 'data-copy="2dafe6b"', 1)
s = s.replace(">7fdb667 ⧉<", ">2dafe6b ⧉<", 1)
assert "<span>2026-11-21</span>" in s
assert 'data-count="13603"' in s
s = s.replace('data-count="13603"', 'data-count="13605"', 1)
assert "11 页 · 1192 原子事实" in s
s = s.replace("11 页 · 1192 原子事实", "11 页 · 1194 原子事实", 1)
for want in ["10 页 · 878 原子事实", "10 页 · 1540 原子事实",
             "13 页 · 2016 原子事实", "8 页 · 860 原子事实",
             "14 页 · 2209 原子事实", "8 页 · 1053 原子事实",
             "4 页 · 382 原子事实", "3 页 · 274 原子事实",
             "16 页 · 1398 原子事实", "18 页 · 1801 原子事实"]:
    assert want in s, want
open(f, "w").write(s)
print("index.html fixed: baseline hash 7fdb667 -> 2dafe6b; date already 2026-11-21 unchanged; facts 13603 -> 13605; milestones batch-06 1194, others unchanged (asserted)")
