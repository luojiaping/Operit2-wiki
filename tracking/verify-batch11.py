#!/usr/bin/env python3
"""batch-11 mechanical check (same口径 as batch-10, stored in tracking/ — /tmp gets wiped):
- facts.json: each backtick span must appear within +/-5 lines of its ref.
- .md: each line's backtick spans must appear within +/-5 of any path:line ref on that line.
- Skip: spans containing <...> (generics), pure punctuation, spans that are themselves a path:line ref.
- Skip frontmatter and the '## 来源' section in .md.
- Refs resolve against Operit2 first, then the gen-1 Operit repo (migrate-operit1 only).
- REF_RE extended vs batch-10: also .mjs/.cs/.xaml/.wxs/.ps1/.kt/.rb/.js/.cjs/.csproj/.xml/.gradle
  (lint's regex lacks .rs/.mjs, so this script is the only check for those)."""
import json, re, sys
from pathlib import Path
REPO = Path("/home/hatch/workspace/Operit2")
REPO1 = Path("/home/hatch/workspace/Operit")
BATCH = Path("/home/hatch/workspace/Operit2-wiki/review/batch-11")
SPAN_RE = re.compile(r"`([^`]+)`")
REF_RE = re.compile(r"([A-Za-z0-9_.\-/]+\.(?:rs|md|json|ts|dart|py|toml|yaml|yml|txt|sh|lock|mjs|cs|xaml|wxs|ps1|kt|rb|js|cjs|csproj|xml|gradle|go|java|swift|kts|html|css):\d+)")
file_cache = {}
def read_lines(path):
    if path not in file_cache:
        for root in (REPO, REPO1):
            fp = root / path
            if fp.is_file():
                file_cache[path] = fp.read_text(encoding="utf-8", errors="replace").splitlines()
                break
        else:
            file_cache[path] = None
    return file_cache[path]
def in_window(path, lineno, symbol):
    lines = read_lines(path)
    if lines is None: return False, "ref 文件不存在"
    if lineno < 1 or lineno > len(lines): return False, "ref 行号越界"
    lo, hi = max(0, lineno-6), min(len(lines), lineno+5)
    return (symbol in "\n".join(lines[lo:hi])), ""
def skip_span(s):
    if "<" in s and ">" in s: return True
    if not re.search(r"[A-Za-z0-9_]", s): return True
    if REF_RE.fullmatch(s): return True
    return False
bad = []
total_facts = 0
only = sys.argv[1] if len(sys.argv) > 1 else None
for facts_path in sorted(BATCH.glob("*.facts.json")):
    pid = facts_path.name[:-len(".facts.json")]
    if only and pid != only: continue
    facts = json.loads(facts_path.read_text(encoding="utf-8"))
    total_facts += len(facts)
    for idx, f in enumerate(facts):
        ref = f["ref"]; m = ref.rsplit(":", 1); path, lineno = m[0], int(m[1])
        for span in SPAN_RE.findall(f["fact"]):
            if skip_span(span): continue
            ok, why = in_window(path, lineno, span)
            if not ok: bad.append(f"{pid}.facts.json#{idx} `{span}` not within ±5 of {ref}" + (f" ({why})" if why else ""))
    md_path = BATCH / f"{pid}.md"
    text = md_path.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("\n---", 3); text = text[end+4:] if end != -1 else text
    in_sources = False
    for ln, line in enumerate(text.splitlines(), 1):
        if line.startswith("## 来源"): in_sources = True
        if in_sources: continue
        spans = SPAN_RE.findall(line)
        if not spans: continue
        refs = REF_RE.findall(line)
        if not refs: continue
        for span in spans:
            if skip_span(span): continue
            ok = False
            for r in refs:
                p, ln2 = r.rsplit(":", 1)
                o, _ = in_window(p, int(ln2), span)
                if o: ok = True; break
            if not ok: bad.append(f"{pid}.md:{ln} `{span}` not within ±5 of any ref {refs}")
print(f"total facts checked: {total_facts}, bad: {len(bad)}")
for b in bad: print("  " + b)
