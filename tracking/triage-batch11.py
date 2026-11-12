#!/usr/bin/env python3
"""Triage verify-batch11 bad items into (a) verifier artifacts vs (b) real errors.
For each bad item, try relaxed matching of the span against the ref window:
- strip trailing () / args: publish_release() -> publish_release
- paths: basename must appear (build_release.py in tools/release/build_release.py)
- dotted names: last component must appear
- multi-token strings: every whitespace-separated token must appear in the window
- version patterns (major.minor.patch...): each dot-separated token must appear
Items still failing after all relaxations are REAL errors (wrong ref line or wrong fact).
Prints per-category counts and the real-error list."""
import json, re
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
def window_text(path, lineno):
    lines = read_lines(path)
    if lines is None or lineno < 1 or lineno > len(lines): return None
    lo, hi = max(0, lineno-6), min(len(lines), lineno+5)
    return "\n".join(lines[lo:hi])
def skip_span(s):
    if "<" in s and ">" in s: return True
    if not re.search(r"[A-Za-z0-9_]", s): return True
    if REF_RE.fullmatch(s): return True
    return False
def relaxed_ok(span, text, ref_path=None):
    if text is None: return False, "ref-missing"
    # span is the name of the file being cited itself (or ends with it)
    if ref_path:
        base = ref_path.rsplit("/", 1)[-1]
        if span == base or span.endswith("/" + base): return True, "self-filename"
    s = span
    # signature form: name(...) -> name
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_.]*)\(.*\)$", s)
    if m and m.group(1) in text: return True, "signature-form"
    # path: basename in text
    if "/" in s:
        base = s.rsplit("/", 1)[-1]
        if base and base in text: return True, "path-basename"
        # path without extension dir part: check last two components
        parts = s.split("/")
        if len(parts) >= 2 and "/".join(parts[-2:]) in text: return True, "path-tail"
    # dotted: last component
    if "." in s and " " not in s:
        last = s.rsplit(".", 1)[-1]
        if last and len(last) > 2 and last in text: return True, "dotted-last"
    # multi-token: every token present
    toks = re.split(r"[\s=+\[\]|,;]+", s)
    toks = [t for t in toks if len(t) > 1]
    if len(toks) >= 2 and all(t in text for t in toks): return True, "all-tokens"
    # filename itself is the ref file's basename (span == file being cited)
    return False, "real?"
real = []
from collections import Counter
cats = Counter()
# re-run the same check as verify-batch11, but triage each bad item
for facts_path in sorted(BATCH.glob("*.facts.json")):
    pid = facts_path.name[:-len(".facts.json")]
    facts = json.loads(facts_path.read_text(encoding="utf-8"))
    for idx, f in enumerate(facts):
        ref = f["ref"]; m = ref.rsplit(":", 1); path, lineno = m[0], int(m[1])
        for span in SPAN_RE.findall(f["fact"]):
            if skip_span(span): continue
            t = window_text(path, lineno)
            if t is not None and span in t: continue
            ok, why = relaxed_ok(span, t, path)
            cats[why] += 1
            if not ok: real.append(f"{pid}.facts.json#{idx} `{span}` ref {ref} ({why})")
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
            ok_any = False; why_any = "real?"
            for r in refs:
                p, ln2 = r.rsplit(":", 1)
                t = window_text(p, int(ln2))
                if t is not None and span in t: ok_any = True; why_any = "literal-ok"; break
                ok, why = relaxed_ok(span, t, p)
                if ok: ok_any = True; why_any = why; break
            if not ok_any:
                cats["real?"] += 1
                real.append(f"{pid}.md:{ln} `{span}` refs {refs}")
            elif why_any != "literal-ok":
                cats[why_any] += 1
print("triage:", dict(cats))
print(f"REAL errors: {len(real)}")
for r in real: print("  " + r)
