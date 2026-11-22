#!/usr/bin/env python3
"""重建 host-android.facts.json：以 .md（保留修订员改动）为基准逐条匹配取 ref。
只输出改动报告，不写文件时加 --dry-run。"""
import json, re, sys
from pathlib import Path
from difflib import SequenceMatcher

WIKI = Path("/home/hatch/workspace/Operit2-wiki")
md_lines = open(WIKI / "review/batch-05/host-android.md").read().splitlines()
facts = json.load(open(WIKI / "review/batch-05/host-android.facts.json"))
REF_RE = re.compile(r"`([A-Za-z0-9_.\-/]+:(?:\d+))`")

def norm(s):
    s = s.replace("`", "").replace("\\", "")
    return re.sub(r"\s+", " ", s).strip()

md_norm = [(i, norm(l), REF_RE.findall(l)) for i, l in enumerate(md_lines)]

# 两处改写事实：旧特征词 -> .md 行号（1-based）
REWRITES = {
    "quietPeriod": (82, "PTY 命令执行以 `findLastAndroidPtyPromptMarker` 检出提示标记确认命令完成"),
    "COMMAND_CANCEL_SETTLE_TIMEOUT_MS": (84, "超时命令取消时先向 PTY 写 `b\"\\x03\"`，再以 3000 毫秒为限等提示标记确认 shell 就绪"),
    "waitForInitialAndroidPtyPrompt": (81, "新建 PTY 会话时 `waitForTerminalPrompt` 等待初始提示最长 10000 毫秒"),
}
# 排除误匹配：#186 与 .md:163 是另一条“注册”事实，不是同一事实
SKIP_IDX = {186}

changes = []
unmatched = []
for idx, f in enumerate(facts):
    text = f.get("fact") or f.get("text") or ""
    old_ref = f.get("ref")
    # 改写事实定向处理
    hit = None
    for key, (ln, newtext) in REWRITES.items():
        if key in text:
            hit = (ln, newtext)
            break
    if hit:
        ln, newtext = hit
        refs = REF_RE.findall(md_lines[ln - 1])
        new_ref = refs[0] if refs else None
        changes.append((idx + 1, text[:50], old_ref, new_ref, newtext, "REWRITE"))
        continue
    nt = norm(text)
    best, best_ratio = None, 0.0
    for i, nline, refs in md_norm:
        if not refs:
            continue
        r = SequenceMatcher(None, nt, nline).ratio()
        # 子串加分
        if nt and (nt in nline or nline in nt):
            r = max(r, 0.95)
        if r > best_ratio:
            best, best_ratio = (i, nline, refs), r
    if best is None or best_ratio < 0.55 or (idx + 1) in SKIP_IDX:
        if (idx + 1) in SKIP_IDX:
            continue
        unmatched.append((idx + 1, text[:60], old_ref, best_ratio))
        continue
    i, nline, refs = best
    # 选与旧 ref 同文件的 ref，缺省取第一个
    old_file = old_ref.rsplit(":", 1)[0] if old_ref else ""
    pick = None
    for r in refs:
        if r.rsplit(":", 1)[0] == old_file:
            pick = r
            break
    pick = pick or refs[0]
    if pick != old_ref:
        changes.append((idx + 1, text[:50], old_ref, pick, None, f"match-ratio={best_ratio:.2f} md:{i+1}"))

print(f"facts: {len(facts)}, changes: {len(changes)}, unmatched: {len(unmatched)}")
for c in changes:
    print(f"  #{c[0]} {c[1]} :: {c[2]} -> {c[3]} [{c[5]}]")
for u in unmatched:
    print(f"  UNMATCHED #{u[0]} {u[1]} :: {u[2]} ratio={u[3]:.2f}")

if "--dry-run" not in sys.argv:
    for idx, _, old_ref, new_ref, newtext, _ in changes:
        f = facts[idx - 1]
        f["ref"] = new_ref
        if newtext:
            f["fact"] = newtext
    raw = open(WIKI / "review/batch-05/host-android.facts.json").read()
    # 保持原文件格式：1 空格缩进
    out = json.dumps(facts, ensure_ascii=False, indent=1)
    open(WIKI / "review/batch-05/host-android.facts.json", "w").write(out + ("\n" if raw.endswith("\n") else ""))
    print("written")
