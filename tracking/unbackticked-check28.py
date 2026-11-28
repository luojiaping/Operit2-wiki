#!/usr/bin/env python3
"""盲区复核 v2（第25轮）：对每条无反引号事实，取其文本中的关键标识
（CamelCase / snake_case / 数字版本 / 中文关键词片段），检查新树 ref 行 ±3 行内是否出现。
不出现的列出，供人工核对。只核 ref 文件在本轮 diff 中的事实。
输出：tracking/unbackticked-suspect-28.json"""
import json, glob, re
from pathlib import Path

NEW = Path("/home/hatch/workspace/Operit2-e1aebc1")
WIKI = Path("/home/hatch/workspace/Operit2-wiki")
changed = set((WIKI / "tracking/diff-3dd6149-e1aebc1.txt").read_text().split())

IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?")

def key_terms(text):
    terms = set()
    for t in IDENT.findall(text):
        if len(t) >= 4 and t not in {"Result", "String", "Self", "impl", "pub", "async", "await"}:
            terms.add(t)
    # 数字版本号如 0.2.7 / preview.41 / 120 秒
    for t in re.findall(r"\d+(?:\.\d+)+", text):
        terms.add(t)
    return terms

def lines(rel):
    p = NEW / rel
    return p.read_text(encoding="utf-8", errors="replace").splitlines() if p.is_file() else None

suspects, checked = [], 0
for f in sorted(glob.glob(str(WIKI / "review/batch-*/**.facts.json"), recursive=True)):
    facts = json.load(open(f))
    page = Path(f).name.replace(".facts.json", "")
    for i, ft in enumerate(facts):
        ref = ft.get("ref") or ""
        m = re.match(r"(.+):(\d+)$", ref)
        if not m:
            continue
        fpath, lno = m.group(1), int(m.group(2))
        if fpath not in changed:
            continue
        text = ft.get("text") or ft.get("fact") or ""
        if "`" in text:
            continue
        terms = key_terms(text)
        if not terms:
            continue  # 纯中文描述、无可核标识，跳过（人工抽查）
        checked += 1
        nl = lines(fpath)
        if nl is None:
            suspects.append({"page": page, "idx": i + 1, "ref": ref, "text": text[:120], "issue": "ref 文件在新树缺失"})
            continue
        window = "\n".join(nl[max(0, lno - 4): lno + 3])
        missing = [t for t in terms if t not in window]
        if len(missing) == len(terms):
            suspects.append({"page": page, "idx": i + 1, "ref": ref, "text": text[:120],
                             "terms": sorted(terms), "window": window[:300]})
print(f"checked: {checked}, suspects (no key term within ±3 of ref in NEW tree): {len(suspects)}")
Path("/home/hatch/workspace/Operit2-wiki/tracking/unbackticked-suspect-28.json").write_text(
    json.dumps(suspects, ensure_ascii=False, indent=1), encoding="utf-8")
for s in suspects:
    print(f"{s['page']}#{s['idx']} {s['ref']} :: {s['text'][:90]}")
    print(f"   terms: {s.get('terms')}")
