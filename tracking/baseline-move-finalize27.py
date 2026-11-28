#!/usr/bin/env python3
"""基线前移收尾（第 27 轮）：全部 .status.json 的 source_commit 改为 3dd6149，
edge-acceptance-v1 summary 里的基线表述同步，AGENTS.md / AI_USAGE.md /
SCHEMA.md / 首页基线同步更新。只改这些，不动 status /
approved_by / 水位线；各页 .md 正文本身的基线提及按惯例不动（由各页
修订员维护）。事实总数 13603 不变，各批里程碑数字不变，首页日期已是
2026-11-28，不动。"""
import glob
import json
import re

OLD = "b3b897c"
NEW = "3dd6149"
TODAY = "2026-11-28"

# 1. 116 个 .status.json
n = 0
for f in sorted(glob.glob("review/*/*.status.json")):
    d = json.load(open(f))
    assert d["source_commit"] in (OLD, NEW), f
    if d["source_commit"] == NEW and d["updated"] == TODAY:
        n += 1
        continue
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
     "源码基线：`AAswordman/Operit2 @ b3b897c`（2026-11-27）",
     "源码基线：`AAswordman/Operit2 @ 3dd6149`（2026-11-28）"),
    ("wiki/AI_USAGE.md",
     "行号以源码钉住的 commit（`b3b897c`）为准",
     "行号以源码钉住的 commit（`3dd6149`）为准"),
    ("SCHEMA.md",
     "钉住 `b3b897c`（2026-11-27）",
     "钉住 `3dd6149`（2026-11-28）"),
]:
    s = open(f).read()
    assert old in s, f
    open(f, "w").write(s.replace(old, new, 1))
    print(f"baseline text fixed: {f}")

# 4. 首页：只改基线 hash 按钮（事实数 13603 不变，日期已是 2026-11-28，各批里程碑数字与实测一致，不动）
f = "site/index.html"
s = open(f).read()
assert 'data-copy="b3b897c"' in s and ">b3b897c ⧉<" in s
s = s.replace('data-copy="b3b897c"', 'data-copy="3dd6149"', 1)
s = s.replace(">b3b897c ⧉<", ">3dd6149 ⧉<", 1)
assert "<span>2026-11-27</span>" in s
s = s.replace("<span>2026-11-27</span>", "<span>2026-11-28</span>", 1)
assert 'data-count="13603"' in s
open(f, "w").write(s)
print("index.html fixed: baseline hash b3b897c -> 3dd6149 (facts 13603 unchanged)")
