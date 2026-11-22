#!/usr/bin/env python3
"""第 19 轮事故重建：core-command.facts.json 在协调员一次 `git checkout` 中被误还原
为旧基线版（34 处 ref + 2 处事实改写丢失；.md 完好）。
以 difflib 等值映射把旧 model.rs 行号重映射到新树，逐条校验新行内容与旧行内容一致；
#76/#77 事实改写按核验器结论用不加反引号的 @vfs-file 重写。
用法：python3 tracking/rebuild-core-command-facts.py [--check]
"""
import difflib, json, sys
from pathlib import Path

WIKI = Path("/home/hatch/workspace/Operit2-wiki")
OLD = Path("/home/hatch/workspace/Operit2-24ad6ff")
NEW = Path("/home/hatch/workspace/Operit2-8163f43")
REL = "core/crates/command/core/src/commands/model.rs"
FACTS = WIKI / "review/batch-03/core-command.facts.json"

old_lines = (OLD / REL).read_text().splitlines()
new_lines = (NEW / REL).read_text().splitlines()

# 等值块映射：old 行号(1-based) -> new 行号
mapping = {}
sm = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal":
        for k in range(i2 - i1):
            mapping[i1 + 1 + k] = j1 + 1 + k

def remap(old_no):
    if old_no in mapping:
        return mapping[old_no], "equal"
    # 非等值区：在新树中找内容相同的行，取与邻近等值映射最接近者
    content = old_lines[old_no - 1]
    cands = [i + 1 for i, l in enumerate(new_lines) if l == content]
    if not cands:
        return None, "no-identical-line"
    # 用最近的等值锚点估算
    below = [o for o in mapping if o < old_no]
    above = [o for o in mapping if o > old_no]
    est = None
    if below:
        est = mapping[max(below)] + (old_no - max(below))
    elif above:
        est = mapping[min(above)] - (min(above) - old_no)
    best = min(cands, key=lambda c: abs(c - est) if est else 0)
    return best, "content-match"

facts = json.loads(FACTS.read_text())
changed = []
problems = []
for idx, f in enumerate(facts):
    ref = f["ref"]
    path, _, lineno = ref.rpartition(":")
    if path != REL:
        continue
    old_no = int(lineno)
    new_no, how = remap(old_no)
    if new_no is None:
        problems.append(f"#{idx+1} {ref}: {how}")
        continue
    if new_lines[new_no - 1] != old_lines[old_no - 1]:
        problems.append(f"#{idx+1} {ref} -> {new_no}: content mismatch: old={old_lines[old_no-1]!r} new={new_lines[new_no-1]!r}")
        continue
    if new_no != old_no:
        changed.append((idx + 1, old_no, new_no, how))
        f["ref"] = f"{REL}:{new_no}"

# #76/#77 事实改写（@vfs-file 不加反引号：该字面只出现在用法字符串行，远离 ref 行）
for idx, old_text in (
    (75, "`parameters` 把 JSON 解析为 `Vec<ModelParameter<serde_json::Value>>` 后调 `updateParametersForModel` 更新。"),
    (76, "builtin-tools 把 JSON 解析为 `Vec<ModelBuiltinTool>` 后调 `updateBuiltinToolsForModel` 更新。"),
):
    cur = facts[idx]["fact"]
    assert cur == old_text, f"#{idx+1} fact text unexpected: {cur!r}"
    facts[idx]["fact"] = cur.replace("把 JSON 解析为", "把 JSON（字面量或 @vfs-file 文件内容）解析为")

if "--check" in sys.argv:
    print(f"would change {len(changed)} refs, problems: {len(problems)}")
    for c in changed:
        print(" ", c)
    for p in problems:
        print(" PROBLEM:", p)
    sys.exit(0)

if problems:
    print("REFUSE TO WRITE, problems:")
    for p in problems:
        print(" ", p)
    sys.exit(1)
FACTS.write_text(json.dumps(facts, ensure_ascii=False, indent=2) + "\n")
print(f"rewrote {len(changed)} refs")
for c in changed:
    print(" ", c)
