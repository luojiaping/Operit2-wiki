#!/usr/bin/env python3
"""第23轮盲区疑点分类：用 git diff -U0 的 hunk 把旧行号映射到新行号。
A: 旧树 ref ±3 内有关键术语，且映射后新行 ±3 内也有 -> 可跟随改 ref
B: 旧树有、映射后新树无 -> 内容被改动/搬移，需人工核对
C: 旧树就无 -> 本轮前已错位，需人工核对
只输出分类与映射值，不改任何文件。"""
import json, re, subprocess
from pathlib import Path

WIKI = Path("/home/hatch/workspace/Operit2-wiki")
OLD = Path("/home/hatch/workspace/Operit2-62dacc0")
NEW = Path("/home/hatch/workspace/Operit2-f020fc4")
suspects = json.load(open(WIKI / "tracking/unbackticked-suspect-23.json"))
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?")

def key_terms(text):
    terms = set()
    for t in IDENT.findall(text):
        if len(t) >= 4 and t not in {"Result", "String", "Self", "impl", "pub", "async", "await"}:
            terms.add(t)
    for t in re.findall(r"\d+(?:\.\d+)+", text):
        terms.add(t)
    return terms

def read_lines(base, rel):
    p = base / rel
    return p.read_text(encoding="utf-8", errors="replace").splitlines() if p.is_file() else None

def has_terms(lines, lno, terms):
    if lines is None or lno < 1 or lno > len(lines):
        return False
    window = "\n".join(lines[max(0, lno - 4): lno + 3])
    return any(t in window for t in terms)

_hunk_cache = {}
def hunks(rel):
    if rel in _hunk_cache:
        return _hunk_cache[rel]
    out = subprocess.run(["git", "diff", "-U0", "62dacc0", "f020fc4", "--", rel],
                         capture_output=True, text=True, cwd="/home/hatch/workspace/Operit2-62dacc0")
    hs = []
    for line in out.stdout.splitlines():
        m = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
        if m:
            os_, oc = int(m.group(1)), int(m.group(2) or 1)
            ns_, nc = int(m.group(3)), int(m.group(4) or 1)
            hs.append((os_, oc, ns_, nc))
    _hunk_cache[rel] = hs
    return hs

def map_line(rel, old_lineno):
    """返回 (new_lineno|None, in_change: bool)。"""
    delta = 0
    for os_, oc, ns_, nc in hunks(rel):
        if old_lineno < os_:
            break
        if os_ <= old_lineno < os_ + oc:
            return None, True
        delta += nc - oc
    return old_lineno + delta, False

cats = {"A": [], "B": [], "C": []}
for s in suspects:
    fpath, lno = s["ref"].rsplit(":", 1)
    lno = int(lno)
    # 事实文本：从 facts.json 取原文（suspect 里只有截断 120 字）
    page = s["page"]
    facts = None
    for f in (WIKI / "review").glob(f"batch-*/{page}.facts.json"):
        facts = json.load(open(f))
        break
    text = ""
    if facts and 0 < s["idx"] <= len(facts):
        ft = facts[s["idx"] - 1]
        text = ft.get("text") or ft.get("fact") or ""
    terms = key_terms(text) or set(s.get("terms") or [])
    old_lines = read_lines(OLD, fpath)
    new_lines = read_lines(NEW, fpath)
    old_ok = has_terms(old_lines, lno, terms)
    mapped, in_change = map_line(fpath, lno)
    if not old_ok:
        cats["C"].append({**s, "mapped": mapped, "in_change": in_change})
    elif in_change or mapped is None:
        cats["B"].append({**s, "mapped": mapped, "in_change": in_change})
    elif has_terms(new_lines, mapped, terms):
        cats["A"].append({**s, "mapped": mapped})
    else:
        cats["B"].append({**s, "mapped": mapped, "in_change": in_change})

for k in "ABC":
    print(f"== {k}: {len(cats[k])}")
json.dump(cats, open(WIKI / "tracking/unbackticked-classify-23.json", "w"), ensure_ascii=False, indent=1)
for k in "ABC":
    for s in cats[k][:40]:
        print(f"  {k} {s['page']}#{s['idx']} {s['ref']} -> {s.get('mapped')} in_change={s.get('in_change')} :: {s['text'][:60]}")
