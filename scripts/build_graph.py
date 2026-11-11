#!/usr/bin/env python3
"""为 Operit2-wiki 生成知识图谱（2026-11-12 重写，替代一代残留版）。

旧版问题（Issue #57「知识图谱无法渲染」根因）：脚本沿用 Operit 一代骨架，
读 wiki-work/outline.yaml（24 条目、Kotlin 模块）与一代 CROSS_LINKS 白名单，
但本仓库只有 outline/outline-v1.yaml（115 页、11 章），wiki-work/ 根本不存在，
load_outline() 直接 FileNotFoundError，deploy 时只留一句 WARN，site/data/graph/
从未生成过，graph.html 的 iframe 与 graph-meta.json 全部 404。

新版流程（全部确定性，无 LLM）：
  1. 读取 outline/outline-v1.yaml（115 个规划条目、11 章、13 个 module 值）
  2. 在 wiki-work/graph-kb/ 暂存一个 llm-wiki 兼容的知识库：
     wiki/topics/<id>.md（条目） + wiki/entities/<stem>.md（章枢纽 + 模块实体）
     边全部由确定性规则生成：
       - 条目 -> 所属章枢纽实体        -> confidence: EXTRACTED（大纲 chapter 字段）
       - 条目 -> 所属模块实体          -> confidence: EXTRACTED（大纲 module 字段）
       - 正文 [[id|标题]] 真实交叉引用 -> confidence: EXTRACTED（解析已写 review/*.md，
         只保留大纲里真实存在的 id；未写页无正文、暂无此边）
     注意：不做同章全互链——115 页按旧版做法会产生约 1500 条 INFERRED 边，
     图谱成毛线团；章枢纽星形边已表达同章归属。
  3. 调用 vendor/llm-wiki-skill 的 build-graph-data.sh / build-graph-html.sh
     生成离线单文件图谱（数字山水前端）
  4. 拷贝到 site/data/graph/knowledge-graph.html，供 site/graph.html 内嵌；
     并写 site/data/graph/graph-meta.json（节点/边/孤立点/桥节点数）

注意：vendor/llm-wiki-skill 为 MIT 协议第三方代码，仅作构建工具使用。
状态口径：条目状态取 review/batch-*/<id>.status.json（approved=已发布、
review-pending=待评审），无 .status.json 的为未写。
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTLINE = ROOT / "outline" / "outline-v1.yaml"
WORK = ROOT / "wiki-work"
KB = WORK / "graph-kb"
SITE_GRAPH = ROOT / "site" / "data" / "graph"
VENDOR = Path.home() / "workspace" / "vendor" / "llm-wiki-skill"
REVIEW = ROOT / "review"

LINK_RE = re.compile(r"\[\[([a-z0-9-]+)(?:\|[^\]]*)?\]\]")

STATUS_LABEL = {"approved": "已发布", "review-pending": "待评审"}


def load_outline() -> dict:
    import yaml
    return yaml.safe_load(OUTLINE.read_text(encoding="utf-8"))


def page_status(pid: str) -> str:
    for f in REVIEW.glob(f"batch-*/{pid}.status.json"):
        try:
            return STATUS_LABEL.get(json.loads(f.read_text(encoding="utf-8")).get("status", ""), "待评审")
        except (json.JSONDecodeError, OSError):
            return "待评审"
    return "未写"


def real_cross_links() -> dict[str, set[str]]:
    """解析已写正文里的 [[id|标题]]，只保留大纲 id。"""
    links: dict[str, set[str]] = {}
    for md in REVIEW.glob("batch-*/*.md"):
        pid = md.stem
        targets = {m.group(1) for m in LINK_RE.finditer(md.read_text(encoding="utf-8"))}
        targets.discard(pid)
        if targets:
            links[pid] = targets
    return links


def link_line(target: str, display: str, conf: str) -> str:
    # llm-wiki 的 wikilink 按文件名解析（不是按 # 标题），用 [[文件名|显示标题]] 写法
    return f"- [[{target}|{display}]] <!-- confidence: {conf} -->"


def write_topic(path: Path, info: dict, pages: dict[str, dict],
                chapter_slug: str, chapter_name: str,
                cross: dict[str, set[str]]) -> None:
    pid = info["id"]
    links: list[tuple[str, str, str]] = []
    # 1. 所属章枢纽（EXTRACTED）
    links.append((chapter_slug, chapter_name, "EXTRACTED"))
    # 2. 所属模块实体（EXTRACTED）
    module = info.get("module", "")
    if module:
        links.append((f"module-{module}", f"模块 {module}", "EXTRACTED"))
    # 3. 正文真实交叉引用（EXTRACTED）
    for other in sorted(cross.get(pid, ())):
        if other in pages:
            links.append((other, pages[other]["title"], "EXTRACTED"))

    lines = [
        f"# {info['title']}",
        "",
        f"> 状态：{page_status(pid)}｜章节：{chapter_name}｜模块：{module or '—'}"
        f"｜大纲 v1（{date.today().isoformat()}）",
        "",
        "## 计划覆盖的问题",
        "",
    ]
    lines += [f"- {q}" for q in info.get("questions", [])]
    lines += ["", "## 种子文件", ""]
    lines += [f"- `{s}`" for s in info.get("seed_files", [])]
    lines += ["", "## 关联条目", ""]
    seen = set()
    for target, display, conf in links:
        if target in seen:
            continue
        seen.add(target)
        lines.append(link_line(target, display, conf))
    lines += [
        "",
        "> 本页为大纲规划占位或已写条目的图谱投影：内容仅来自 outline-v1.yaml "
        "的确定性字段与已写正文的真实交叉引用，未引入任何推测。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_entity(path: Path, title: str, lines_body: list[str],
                 member_links: list[tuple[str, str]]) -> None:
    lines = [f"# {title}", "", "> 由 outline-v1.yaml 确定性生成", "", *lines_body,
             "", "## 关联条目", ""]
    seen = set()
    for target, display in member_links:
        if target in seen:
            continue
        seen.add(target)
        lines.append(link_line(target, display, "EXTRACTED"))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def stage_kb(outline: dict) -> tuple[dict[str, dict], int, int]:
    if KB.exists():
        shutil.rmtree(KB)
    topics = KB / "wiki" / "topics"
    entities = KB / "wiki" / "entities"
    topics.mkdir(parents=True)
    entities.mkdir(parents=True)

    (KB / "purpose.md").write_text(
        "# Operit2-wiki 知识图谱\n\n> 由 Operit2-wiki 大纲 v1（115 页、11 章）与已写正文的"
        "真实交叉引用确定性生成；节点为规划条目、章枢纽与模块实体，边全部标注置信度。\n",
        encoding="utf-8",
    )

    pages: dict[str, dict] = {}
    chapters: list[tuple[str, str, list[str]]] = []  # (slug, name, [ids])
    modules: dict[str, list[str]] = {}
    for idx, ch in enumerate(outline["chapters"], 1):
        cname = ch["chapter"]
        slug = f"chapter-{idx:02d}"
        ids: list[str] = []
        for p in ch["pages"]:
            info = dict(p)
            info["chapter"] = cname
            info["chapter_slug"] = slug
            pages[p["id"]] = info
            ids.append(p["id"])
            modules.setdefault(p.get("module", ""), []).append(p["id"])
        chapters.append((slug, cname, ids))

    cross = real_cross_links()
    for pid, info in pages.items():
        write_topic(topics / f"{pid}.md", info, pages,
                    info["chapter_slug"], info["chapter"], cross)

    for idx, (slug, cname, ids) in enumerate(chapters, 1):
        write_entity(
            entities / f"{slug}.md",
            f"第 {idx} 章 {cname}",
            [f"- 条目数：{len(ids)}", f"- 章节：{cname}"],
            [(pid, pages[pid]["title"]) for pid in ids],
        )
    for mod, ids in sorted(modules.items()):
        if not mod:
            continue
        write_entity(
            entities / f"module-{mod}.md",
            f"模块 {mod}",
            [f"- 条目数：{len(ids)}"],
            [(pid, pages[pid]["title"]) for pid in ids],
        )

    n_entities = len(chapters) + len([m for m in modules if m])
    return pages, len(pages), n_entities


def run_graph_pipeline() -> Path:
    engine = VENDOR / "packages" / "graph-engine" / "dist" / "engine.iife.js"
    if not engine.exists():
        raise RuntimeError(
            f"图谱引擎未构建：{engine} 不存在，"
            "请先在 vendor/llm-wiki-skill 执行 npm run build -w @llm-wiki/graph-engine"
        )
    scripts = VENDOR / "scripts"
    for script, args in [
        ("build-graph-data.sh", [str(KB)]),
        ("build-graph-html.sh", [str(KB)]),
    ]:
        r = subprocess.run(
            ["bash", str(scripts / script), *args],
            capture_output=True, text=True, timeout=300,
        )
        if r.returncode != 0:
            raise RuntimeError(f"{script} 失败：{r.stderr[-2000:]}")
    html = KB / "wiki" / "knowledge-graph.html"
    if not html.exists():
        raise RuntimeError("knowledge-graph.html 未生成")
    return html


def main() -> int:
    outline = load_outline()
    pages, n_topics, n_entities = stage_kb(outline)
    print(f"暂存知识库：{n_topics} 个条目 + {n_entities} 个实体 -> {KB}")

    try:
        html = run_graph_pipeline()
    except RuntimeError as e:
        print(f"WARN: {e}\n跳过图谱构建（保留旧版）。", file=sys.stderr)
        return 2

    SITE_GRAPH.mkdir(parents=True, exist_ok=True)
    dest = SITE_GRAPH / "knowledge-graph.html"
    shutil.copy2(html, dest)

    data = json.loads((KB / "wiki" / "graph-data.json").read_text(encoding="utf-8"))
    ins = data.get("insights", {})
    meta = {
        "built": date.today().isoformat(),
        "nodes": len(data.get("nodes", [])),
        "edges": len(data.get("edges", [])),
        "isolated_nodes": len(ins.get("isolated_nodes", [])),
        "bridge_nodes": len(ins.get("bridge_nodes", [])),
        "source": "outline-v1.yaml + 已写正文交叉引用（确定性生成）",
    }
    (SITE_GRAPH / "graph-meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"图谱已生成：{dest}（{meta['nodes']} 节点 / {meta['edges']} 边）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
