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
  3. 调用 vendor/llm-wiki-skill 的 build-graph-data.sh 生成图谱数据，随后
     把 vendor 的 Louvain 社区改写为 11 章群落（rewrite_communities_to_chapters），
     并把 11 个章枢纽钉在群落中心（.wiki-graph-layout.json），再调
     build-graph-html.sh 生成离线单文件图谱（数字山水前端）
  4. 在生成产物上做两处外观定制（vendor 源码不动，找不到原文就报错）：
     强制纸墨浅色主题并隐藏墨夜切换（force_paper_theme，2026-11-12）；
     山水主题 9 色 pastel 群落调色板 -> 11 色克制墨色、引擎初始布局 8 个
     群落中心 -> 11 个章中心（patch_community_look，章节群落图方向）
  5. 拷贝到 site/data/graph/knowledge-graph.html，供 site/graph.html 内嵌；
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
from datetime import date, datetime
from zoneinfo import ZoneInfo
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
        f"｜大纲 v1（{datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat()}）",
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


def force_paper_theme(html_path: Path) -> None:
    """强制纸墨浅色主题（2026-11-12）：图谱页默认山水主题本就是浅色，但页面
    右上角有个「墨夜」切换按钮，一点就变成深色星空且 localStorage 会记住，
    用户觉得丑。整站是纸墨设计，图谱只留浅色：无视已存的 mo-ye 值，并隐藏
    切换按钮。vendor 脚本不动，只改生成产物；找不到待替换的原文时直接报错，
    不静默出一个未修的版本。"""
    text = html_path.read_text(encoding="utf-8")
    old_fn = (
        '      function readStoredTheme() {\n'
        '        try {\n'
        '          var value = window.localStorage && window.localStorage.getItem(themeKey);\n'
        '          return value === "mo-ye" ? "mo-ye" : "shan-shui";\n'
        '        } catch (_) {\n'
        '          storageAvailable = false;\n'
        '          return "shan-shui";\n'
        '        }\n'
        '      }'
    )
    new_fn = (
        '      function readStoredTheme() {\n'
        '        // 本站强制纸墨浅色主题：忽略已存的 mo-ye 值。\n'
        '        return "shan-shui";\n'
        '      }'
    )
    if old_fn not in text:
        raise RuntimeError("强制纸墨主题失败：生成产物里找不到 readStoredTheme 原文")
    text = text.replace(old_fn, new_fn, 1)
    hide = "<style>.offline-theme-toggle{display:none!important}</style>"
    if "</head>" not in text:
        raise RuntimeError("强制纸墨主题失败：生成产物里找不到 </head>")
    text = text.replace("</head>", hide + "</head>", 1)
    html_path.write_text(text, encoding="utf-8")


# 章节群落图（2026-11-12，用户选定方向 2：Beautiful Graph 路线）
# 11 章各一个克制墨色 + 柔和群落底色 + 枢纽钉住放大。
CHAPTER_PALETTE = [
    "#2e2a26",  # ch01 定位与入门：墨
    "#315f72",  # ch02 架构总览：黛
    "#8b2e24",  # ch03 Core：朱砂
    "#a06a1c",  # ch04 Agent 回路：赭
    "#3e6b6b",  # ch05 应用与 Host：青
    "#4b7564",  # ch06 插件系统：玉
    "#6f557f",  # ch07 多设备同步：紫
    "#8a4b5e",  # ch08 UI 与主题：梅
    "#a8893a",  # ch09 模型与 Provider：金
    "#3e6b4b",  # ch10 Edge 与厂商接入：松
    "#a35a2a",  # ch11 开发与工具：锈
]
# 11 个群落中心（百分比坐标，与引擎初始布局的 0-100 空间一致；节点环绕
# 半径约 ±21x/±16y，中心间距取 24 以上避免大章群落重叠）
CHAPTER_CENTERS = [
    (18, 16), (50, 13), (82, 16),
    (12, 42), (36, 38), (62, 38), (88, 42),
    (16, 68), (38, 72), (62, 70), (84, 68),
]


def chapter_map(outline: dict) -> tuple[dict[str, str], dict[str, str], list[dict]]:
    """返回 (pid -> 章 slug, module -> 主导章 slug, 章列表)。
    本大纲每个 module 只属于一章，主导章即唯一章。"""
    pid_to_chapter: dict[str, str] = {}
    chapters: list[dict] = []
    module_chapters: dict[str, set[str]] = {}
    for idx, ch in enumerate(outline["chapters"], 1):
        slug = f"chapter-{idx:02d}"
        chapters.append({"slug": slug, "name": ch["chapter"], "index": idx - 1})
        for p in ch["pages"]:
            pid_to_chapter[p["id"]] = slug
            module_chapters.setdefault(p.get("module", ""), set()).add(slug)
    module_to_chapter = {
        m: sorted(s)[0] for m, s in module_chapters.items() if m
    }
    return pid_to_chapter, module_to_chapter, chapters


def rewrite_communities_to_chapters(outline: dict) -> None:
    """把 vendor 的 Louvain 社区改写为 11 章群落。

    改 graph-data.json 三处：节点 community 字段、learning.communities 列表、
    insights.bridge_nodes 里的社区引用。边、节点 id、meta.initial_view 不动。
    """
    pid_to_chapter, module_to_chapter, chapters = chapter_map(outline)
    chapter_by_slug = {c["slug"]: c for c in chapters}
    data_path = KB / "wiki" / "graph-data.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))

    def chapter_of_node(node: dict) -> str:
        nid = node["id"]
        if nid.startswith("wiki/topics/"):
            return pid_to_chapter[nid[len("wiki/topics/"):-len(".md")]]
        if nid.startswith("wiki/entities/chapter-"):
            return nid[len("wiki/entities/"):-len(".md")]
        if nid.startswith("wiki/entities/module-"):
            return module_to_chapter[nid[len("wiki/entities/module-"):-len(".md")]]
        return pid_to_chapter.get(nid, chapters[0]["slug"])

    for node in data["nodes"]:
        node["community"] = chapter_of_node(node)

    # learning.communities：11 章，顺序即调色板顺序，color_index 显式钉死
    edge_weight: dict[str, float] = {c["slug"]: 0.0 for c in chapters}
    for e in data["edges"]:
        a = next(n for n in data["nodes"] if n["id"] == e["from"])
        b = next(n for n in data["nodes"] if n["id"] == e["to"])
        if a["community"] == b["community"]:
            edge_weight[a["community"]] += float(e.get("weight", 0.5))
    by_id = {n["id"]: n for n in data["nodes"]}
    communities = []
    for c in chapters:
        members = [n for n in data["nodes"] if n["community"] == c["slug"]]
        communities.append({
            "id": c["slug"],
            "label": f"第 {c['index'] + 1} 章 {c['name']}",
            "node_count": len(members),
            "internal_edge_weight": round(edge_weight[c["slug"]], 3),
            "is_primary": False,
            "is_weak": False,
            "source_count": 0,
            "recommended_start_node_id": f"wiki/entities/{c['slug']}.md",
            "color_index": c["index"],
        })
    data.setdefault("learning", {})["communities"] = communities

    # insights：bridge_nodes 的社区引用从 Louvain 节点 id 改为章 slug
    ins = data.get("insights", {})
    for b in ins.get("bridge_nodes", []):
        b["community"] = chapter_of_node(by_id[b["community"]]) if b.get("community") in by_id else b.get("community")
        b["connected_communities"] = sorted({
            chapter_of_node(by_id[c]) for c in b.get("connected_communities", []) if c in by_id
        })
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"群落改写：{len(communities)} 章群落，节点 community 已全部指向章节")


def write_chapter_pins(outline: dict) -> None:
    """把 11 个章枢纽实体钉在群落中心（百分比坐标，version 1）。
    被钉住的节点在引擎里渲染为最大尺寸（10），成为每章的锚点印章；
    其余节点经力导布局自然聚向各自枢纽。"""
    _, _, chapters = chapter_map(outline)
    pins = {
        f"wiki/entities/{c['slug']}.md": {"x": x, "y": y}
        for c, (x, y) in zip(chapters, CHAPTER_CENTERS)
    }
    layout = {"version": 1, "pins": pins, "updatedAt": datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()}
    (KB / ".wiki-graph-layout.json").write_text(
        json.dumps(layout, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"章枢纽已钉住：{len(pins)} 个")


def recommit_warning_pair() -> None:
    """用 vendor 自身的 commit-pair 把告警配对重新提交。

    rewrite_communities_to_chapters 改写 graph-data.json 后，meta.warning_summary
    里的旧 build_id 与重算值不符，build-graph-html.sh 的 warning-embed 会判
    build_id_mismatch，iframe 里出现红色「告警详情暂不可用」。
    commit-pair 用 vendor 自己的 assemble 逻辑重算 build_id 并同时写回
    graph-data.json 与 graph-warnings.json（告警分组沿用现有的，一般为空）。
    """
    import tempfile
    warnings_path = KB / "wiki" / "graph-warnings.json"
    bundle = json.loads(warnings_path.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        groups_path = Path(tmp) / "warning-groups.json"
        sets_path = Path(tmp) / "candidate-sets.json"
        groups_path.write_text(json.dumps(bundle.get("groups", []), ensure_ascii=False), encoding="utf-8")
        sets_path.write_text(json.dumps(bundle.get("candidate_sets", []), ensure_ascii=False), encoding="utf-8")
        r = subprocess.run(
            ["node", str(VENDOR / "scripts" / "wiki-link-cli.js"), "commit-pair",
             str(KB), str(KB / "wiki" / "graph-data.json"),
             str(groups_path), str(sets_path), str(KB / "wiki" / "graph-data.json")],
            capture_output=True, text=True, timeout=120,
        )
        if r.returncode != 0:
            raise RuntimeError(f"commit-pair 失败：{r.stderr[-1000:]}")
    data = json.loads((KB / "wiki" / "graph-data.json").read_text(encoding="utf-8"))
    bundle = json.loads(warnings_path.read_text(encoding="utf-8"))
    if data["meta"]["warning_summary"]["build_id"] != bundle["build_id"]:
        raise RuntimeError("告警配对重提交后 build_id 仍不一致")
    print(f"告警配对已重提交：build_id {bundle['build_id'][:12]}…（{len(bundle.get('groups', []))} 组告警）")


def patch_community_look(html_path: Path) -> None:
    """在生成产物里替换两处引擎内联值（vendor 源码不动）：
    山水主题的 9 色 pastel 群落调色板 -> 11 色克制墨色；
    引擎初始布局的 8 个群落中心 -> 11 个章中心（与 pins 一致）。
    找不到原文时直接报错，不静默出旧版。"""
    text = html_path.read_text(encoding="utf-8")
    old_palette = "[`#dd9c82`,`#8fb0c9`,`#a6c187`,`#d8b563`,`#b9a3cf`,`#8ec4b3`,`#cda37e`,`#d9a0ad`,`#bdb389`]"
    new_palette = "[" + ",".join(f"`{c}`" for c in CHAPTER_PALETTE) + "]"
    if text.count(old_palette) != 1:
        raise RuntimeError(f"群落调色板替换失败：原文出现 {text.count(old_palette)} 次")
    text = text.replace(old_palette, new_palette, 1)
    old_centers = "[{x:50,y:48},{x:30,y:34},{x:70,y:36},{x:30,y:72},{x:72,y:70},{x:18,y:52},{x:84,y:52},{x:50,y:78}]"
    new_centers = "[" + ",".join(f"{{x:{x},y:{y}}}" for x, y in CHAPTER_CENTERS) + "]"
    if text.count(old_centers) != 1:
        raise RuntimeError(f"群落中心替换失败：原文出现 {text.count(old_centers)} 次")
    text = text.replace(old_centers, new_centers, 1)
    html_path.write_text(text, encoding="utf-8")
    print("群落外观已替换：11 色墨色调色板 + 11 个群落中心")


def run_graph_data() -> None:
    engine = VENDOR / "packages" / "graph-engine" / "dist" / "engine.iife.js"
    if not engine.exists():
        raise RuntimeError(
            f"图谱引擎未构建：{engine} 不存在，"
            "请先在 vendor/llm-wiki-skill 执行 npm run build -w @llm-wiki/graph-engine"
        )
    r = subprocess.run(
        ["bash", str(VENDOR / "scripts" / "build-graph-data.sh"), str(KB)],
        capture_output=True, text=True, timeout=300,
    )
    if r.returncode != 0:
        raise RuntimeError(f"build-graph-data.sh 失败：{r.stderr[-2000:]}")


def run_graph_html() -> Path:
    r = subprocess.run(
        ["bash", str(VENDOR / "scripts" / "build-graph-html.sh"), str(KB)],
        capture_output=True, text=True, timeout=300,
    )
    if r.returncode != 0:
        raise RuntimeError(f"build-graph-html.sh 失败：{r.stderr[-2000:]}")
    html = KB / "wiki" / "knowledge-graph.html"
    if not html.exists():
        raise RuntimeError("knowledge-graph.html 未生成")
    return html


def run_graph_pipeline() -> Path:
    run_graph_data()
    return run_graph_html()


def main() -> int:
    outline = load_outline()
    pages, n_topics, n_entities = stage_kb(outline)
    print(f"暂存知识库：{n_topics} 个条目 + {n_entities} 个实体 -> {KB}")

    try:
        run_graph_data()
        rewrite_communities_to_chapters(outline)
        recommit_warning_pair()
        write_chapter_pins(outline)
        html = run_graph_html()
        force_paper_theme(html)
        patch_community_look(html)
    except RuntimeError as e:
        print(f"WARN: {e}\n跳过图谱构建（保留旧版）。", file=sys.stderr)
        return 2

    SITE_GRAPH.mkdir(parents=True, exist_ok=True)
    dest = SITE_GRAPH / "knowledge-graph.html"
    shutil.copy2(html, dest)

    data = json.loads((KB / "wiki" / "graph-data.json").read_text(encoding="utf-8"))
    ins = data.get("insights", {})
    meta = {
        "built": datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat(),
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
