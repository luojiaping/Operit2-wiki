#!/usr/bin/env python3
"""生成正式 Wiki 站的数据：site/data/wiki/pages.json。

正式 wiki 不再有"预览/评审中/规划中"之分：每一页都直接嵌入正文。
- 大纲 11 章 115 页：正文取自 review-queue.json 对应条目的 review/<id>.md（去 frontmatter）。
- 当前只有大纲条目（batch-00/outline）且不在大纲章节内，故 pages.json 现为空章节；
  第一批正文页写完进评审后，本脚本会自动把已批准的页拼进来。
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "data" / "wiki" / "pages.json"

# 不在大纲里、需要并入附录章的条目（固定阅读顺序）。
# Operit2-wiki 目前没有此类条目；有附录页时再往这里加。
APPENDIX_EXTRA = []

FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.S)


def strip_frontmatter(md: str) -> str:
    return FRONTMATTER_RE.sub("", md, count=1)


def page_from_entry(entry: dict, pid: str, title: str, module: str) -> dict:
    md_path = ROOT / entry["md"]
    md = strip_frontmatter(md_path.read_text(encoding="utf-8")) if md_path.exists() else ""
    updated = ""
    st_path = (ROOT / "review" / entry["id"]).with_suffix(".status.json")
    if st_path.exists():
        try:
            updated = json.loads(st_path.read_text(encoding="utf-8")).get("updated", "")
        except Exception:
            pass
    return {
        "id": pid, "title": title, "module": module, "md": md,
        "updated": updated, "issue": entry.get("issue"),
    }


def main() -> None:
    v1 = ROOT / "outline" / "outline-v1.yaml"
    op = v1 if v1.exists() else (ROOT / "wiki-work" / "outline.yaml")
    outline = yaml.safe_load(op.read_text(encoding="utf-8"))
    queue = json.loads((ROOT / "review-queue.json").read_text(encoding="utf-8"))
    entries = queue.get("entries", [])

    # page_id（去掉 batch 前缀）-> queue entry
    by_page: dict[str, dict] = {}
    by_full: dict[str, dict] = {}
    for e in entries:
        eid = e.get("id", "")
        by_full[eid] = e
        pid = eid.split("/", 1)[1] if "/" in eid else eid
        by_page[pid] = e

    chapters = []
    total = 0
    for ch in outline["chapters"]:
        pages = []
        for p in ch["pages"]:
            pid = p["id"]
            e = by_page.get(pid)
            if e is None:
                continue
            pages.append(page_from_entry(e, pid, p["title"], p["module"]))
            total += 1
        # 附录章：追加大纲之外的附录页
        if ch["chapter"] == "附录":
            for full_id in APPENDIX_EXTRA:
                e = by_full.get(full_id)
                if e is None:
                    continue
                pid = full_id.split("/", 1)[1]
                pages.append(page_from_entry(e, pid, e["title"], e.get("module", "附录")))
                total += 1
        chapters.append({"chapter": ch["chapter"], "pages": pages})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "built": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "outline_version": outline.get("version"),
        "counts": {"total": total},
        "chapters": chapters,
    }, ensure_ascii=False), encoding="utf-8")
    print(f"正式 wiki 数据：{OUT}（共 {total} 页）")


if __name__ == "__main__":
    main()
