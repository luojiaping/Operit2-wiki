#!/usr/bin/env python3
"""基线前移收尾（第 28 轮）：全部 .status.json 的 source_commit 改为 e1aebc1，
edge-acceptance-v1 summary 里的基线表述同步，AGENTS.md / AI_USAGE.md /
SCHEMA.md / 首页基线同步更新。只改这些，不动 status /
approved_by / 水位线；各页 .md 正文本身的基线提及按惯例不动（由各页
修订员维护）。事实总数 13603 不变，各批里程碑数字不变，首页日期已是
2026-11-28，不动。"""
import glob
import json
import re

OLD = "3dd6149"
NEW = "e1aebc1"
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
     "源码基线：`AAswordman/Operit2 @ 3dd6149`（2026-11-28）",
     "源码基线：`AAswordman/Operit2 @ e1aebc1`（2026-11-28）"),
    ("wiki/AI_USAGE.md",
     "行号以源码钉住的 commit（`3dd6149`）为准",
     "行号以源码钉住的 commit（`e1aebc1`）为准"),
    ("SCHEMA.md",
     "钉住 `3dd6149`（2026-11-28）",
     "钉住 `e1aebc1`（2026-11-28）"),
]:
    s = open(f).read()
    if old not in s:
        assert new in s, f
        print(f"baseline text already new: {f}")
        continue
    open(f, "w").write(s.replace(old, new, 1))
    print(f"baseline text fixed: {f}")

# 4. 首页：只改基线 hash 按钮（事实数 13603 不变，日期已是 2026-11-28，各批里程碑数字与实测一致，不动）
f = "site/index.html"
s = open(f).read()
if 'data-copy="e1aebc1"' in s and ">e1aebc1 ⧉<" in s:
    print("index.html baseline hash already e1aebc1")
else:
    assert 'data-copy="3dd6149"' in s and ">3dd6149 ⧉<" in s
    s = s.replace('data-copy="3dd6149"', 'data-copy="e1aebc1"', 1)
    s = s.replace(">3dd6149 ⧉<", ">e1aebc1 ⧉<", 1)
    print("index.html fixed: baseline hash 3dd6149 -> e1aebc1 (facts 13603 unchanged)")
assert "<span>2026-11-28</span>" in s  # 日期已是今天，不动
assert 'data-count="13603"' in s
open(f, "w").write(s)
print("index.html done")
