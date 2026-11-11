#!/usr/bin/env python3
"""生成 Operit2-wiki app-host-capability-matrix 的能力 x 平台矩阵。

取数方法（写进正文）：
  能力全集 = core/crates/foundation/host-api/src/*.rs 里 `pub trait` 定义，
  再以 HostManager.rs 的 struct 字段过滤出 34 个有注册槽位的能力 trait。
  其余 trait（连接/会话/监听器等辅助 trait）无注册槽位，不进矩阵，另表说明。
  平台取数范围 = hosts/<platform>/src/lib.rs 里的 createRuntimeHostManager
  （android 另有 createPrivilegedRuntimeHostManager 与共用的
  createBaseRuntimeHostManager）。hosts/apple 无 createRuntimeHostManager，
  只是 ios/macos 共用的实现库，不占平台列。
判定标准：
  支持 = 该平台 create 函数内以 Arc::new(平台实现) 注册进 HostManager
         （直接 withXxxHost 调用、复合 with...Hosts 调用、或字段赋值）。
  部分支持（调用方提供） = 注册位由调用方传入的 Arc<dyn Trait> 参数填充，
         平台只提供槽位，实现归调用方。
  部分支持（依赖调用方回调） = 注册的实现由调用方传入的回调构造。
  部分支持（仅标准版） = 只在 android 标准版注册，特权版无此注册。
  部分支持（已注册，open 一律报错） = iOS SerialPortHost 人工复核项。
  不支持 = 源码或 README 明确写不支持（本批唯一一例：OHOS TtsSynthesisHost）。
  未查到 = 上述取数范围内无注册；不等于不支持（Flutter 桥/CLI 等产品方
         可在 hosts 外另行注册，见 hosts/README.md:38）。
用法：python3 /tmp/gen_host_matrix.py
输出：/tmp/host_matrix.json、/tmp/host_matrix_table.md、/tmp/host_matrix_facts.json
"""
import json
import re
from pathlib import Path

ROOT = Path("/home/hatch/workspace/Operit2")
API = ROOT / "core/crates/foundation/host-api/src"
HM = API / "HostManager.rs"
HOSTS = ROOT / "hosts"
PLATFORMS = ["android", "ios", "linux", "macos", "ohos", "web", "windows"]
PLATFORM_CN = {"android": "Android", "ios": "iOS", "linux": "Linux", "macos": "macOS",
               "ohos": "OpenHarmony", "web": "Web", "windows": "Windows"}

# ---------- 1. trait 全集 ----------
TRAIT_RE = re.compile(r"pub trait (\w+)")
traits = {}  # name -> {file, line, methods}
for f in sorted(API.glob("*.rs")):
    lines = f.read_text(encoding="utf-8").splitlines()
    for i, ln in enumerate(lines):
        m = TRAIT_RE.search(ln)
        if not m:
            continue
        name = m.group(1)
        # 方法计数：trait 体内 4 空格缩进的 fn 行（默认方法体内的更深缩进行不计）
        depth = 0
        methods = []
        started = False
        for j in range(i, len(lines)):
            l = lines[j]
            depth_before = depth
            depth += l.count("{") - l.count("}")
            if j == i:
                started = True
                continue
            if started and depth <= 0:
                break
            mm = re.match(r"    (?:async )?fn (\w+)\s*\(", l)
            if mm and depth_before == 1:
                methods.append((mm.group(1), j + 1))
        traits[name] = {"file": str(f.relative_to(ROOT)), "line": i + 1,
                        "methods": methods}

# ---------- 2. HostManager 槽位 ----------
hm_text = HM.read_text(encoding="utf-8").splitlines()
slot_trait = {}  # field -> trait
slot_field_line = {}  # trait -> HostManager.rs field line
for i, ln in enumerate(hm_text):
    m = re.match(r"    pub (\w+): Option<Arc<dyn ([\w:]+)>>", ln)
    if m:
        trait = m.group(2).split("::")[-1]
        slot_trait[m.group(1)] = trait
        slot_field_line[trait] = i + 1
slots = sorted(set(slot_trait.values()))
assert len(slots) == 34, f"slot count {len(slots)}: {slots}"

# ---------- 3. with 方法与复合构造器 ----------
def short_trait(t):
    return t.split("::")[-1]

with_map = {}   # withXxxHost -> trait
composite = {}  # withXxxHosts -> [traits in param order]
_hm = HM.read_text()
for m in re.finditer(r"pub fn (with\w+)\(\s*mut self,\s*\w+: Arc<dyn ([\w:]+)>", _hm):
    with_map[m.group(1)] = short_trait(m.group(2))
for m in re.finditer(r"pub fn (with\w+Hosts)\(\s*\n((?:.*?\n)*?)    \)", _hm):
    params = re.findall(r"Arc<dyn ([\w:]+)>", m.group(2))
    composite[m.group(1)] = [short_trait(p) for p in params]

# 字段名 -> trait（供字段赋值解析）
field_trait = slot_trait

# ---------- 4. 解析单个平台 lib.rs ----------
def fn_bodies(path):
    """返回 [(fn_name, start_line_1based, [body lines with numbers])]。"""
    lines = path.read_text(encoding="utf-8").splitlines()
    out = []
    for i, ln in enumerate(lines):
        m = re.match(r"(?:pub(?:\(crate\))? )?(?:async )?fn (\w+)\(", ln)
        if not m:
            continue
        depth = 0
        started = False
        body = []
        for j in range(i, len(lines)):
            l = lines[j]
            depth += l.count("{") - l.count("}")
            if "{" in l:
                started = True
            body.append((j + 1, l))
            if started and depth <= 0:
                break
        out.append((m.group(1), i + 1, body))
    return out

def split_top_commas(text):
    parts, depth, cur = [], 0, ""
    for ch in text:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    return [p.strip() for p in parts]

def arg_marker(arg):
    """复合构造器参数行定位标记：Arc::new(XxxHost::...) 取具体类型名，
    裸变量 / 变量.clone() 取变量名。旧写法 arg.split("(")[0] 对
    Arc::new(...) 参数恒得 "Arc"，会错锚到复合调用的第一个参数行
    （即 FileSystemHost 的参数行）。"""
    m = re.search(r"Arc::new\((\w+)", arg)
    if m:
        return m.group(1)
    m = re.match(r"(\w+)", arg)
    return m.group(1) if m else arg.strip()


def classify_arg(arg, params, fn_name, trait, callback_locals=frozenset()):
    """返回 (verdict, note)。"""
    if "fromOwnerCallbacks" in arg or "fromPlatformActions" in arg:
        return ("部分支持", "依赖调用方回调")
    if arg in callback_locals:
        return ("部分支持", "依赖调用方回调")
    if arg.startswith("Arc::new("):
        return ("支持", "平台实现注册")
    if arg in params:
        return ("部分支持", "调用方提供")
    if arg == "systemOperationHost.clone()" or arg == "systemOperationHost":
        return ("支持", "与 SystemOperationHost 共用同一实现")
    if re.match(r"^\w+\.clone\(\)$", arg):
        return ("支持", "与同文件内已注册实现共用")
    return ("支持", "注册")

matrix = {}  # trait -> platform -> {verdict, note, ref}
for plat in PLATFORMS:
    lib = HOSTS / plat / "src/lib.rs"
    rel = str(lib.relative_to(ROOT))
    regs = {}  # trait -> {verdict, note, ref, fn}
    seen_variants = {}  # trait -> {base|standard|privileged}
    for fn_name, fn_line, body in fn_bodies(lib):
        if fn_name not in ("createRuntimeHostManager", "createPrivilegedRuntimeHostManager",
                           "createBaseRuntimeHostManager"):
            continue
        # 该函数签名参数：name -> type line
        sig_lines = body[:12]
        params = {}
        param_lines = {}
        for ln_no, ln in sig_lines:
            m = re.match(r"\s*(\w+): Arc<dyn [\w:]+::(\w+)>", ln)
            if m:
                params[m.group(1)] = m.group(2)
                param_lines[m.group(1)] = ln_no
        # 局部变量定义行：let <name> = ...
        local_lines = {}
        for ln_no, ln in body:
            m = re.match(r"\s*let (?:mut )?(\w+) =", ln)
            if m:
                local_lines.setdefault(m.group(1), ln_no)
        body_text = "\n".join(l for _, l in body)
        body_lines = dict(body)
        # 由调用方回调构造的局部变量（如 ohos 的 systemOperationHost）
        callback_locals = set(re.findall(
            r"let (\w+) = Arc::new\(\w+::(?:fromOwnerCallbacks|fromPlatformActions)\(", body_text))
        variant = "base" if fn_name == "createBaseRuntimeHostManager" else (
            "privileged" if fn_name == "createPrivilegedRuntimeHostManager" else "standard")
        prio = {"base": 3, "standard": 2, "privileged": 1}
        def record(trait, verdict, note, ref):
            seen_variants.setdefault(trait, set()).add(variant)
            cur = regs.get(trait)
            if cur is None or prio[variant] > prio[cur["variant"]]:
                regs[trait] = {"verdict": verdict, "note": note, "ref": ref,
                               "fn": fn_name, "variant": variant}
        # 复合构造器调用
        for m in re.finditer(r"(?:HostManager::|\.)(with\w+Hosts)\(", body_text):
            cname = m.group(1)
            if cname not in composite:
                continue
            start = body_text.index("(", m.start())
            depth, k = 0, start
            while k < len(body_text):
                if body_text[k] == "(":
                    depth += 1
                elif body_text[k] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                k += 1
            args = split_top_commas(body_text[start + 1:k])
            # 找到调用起始行
            upto = body_text[:m.start()].count("\n")
            call_line = body[upto][0]
            for slot_trait_name, arg in zip(composite[cname], args):
                # 参数行：按参数内特征标识（具体 Host 类型名 / 裸变量名）
                # 搜调用起始行之后首次出现的行
                marker = arg_marker(arg)
                arg_line = None
                for ln_no, ln in body:
                    if ln_no >= call_line and marker in ln:
                        arg_line = ln_no
                        break
                verdict, note = classify_arg(arg, params, fn_name, slot_trait_name, callback_locals)
                if verdict == "部分支持" and note == "调用方提供":
                    ref = f"{rel}:{param_lines.get(arg, arg_line)}"
                elif verdict == "部分支持" and note == "依赖调用方回调" and arg in local_lines:
                    ref = f"{rel}:{local_lines[arg]}"
                else:
                    ref = f"{rel}:{arg_line}"
                record(slot_trait_name, verdict, note, ref)
        # 单个 withXxxHost 调用（withHostSecretStore 以 Store 结尾，同样匹配）
        for m in re.finditer(r"\.(with\w+)\(", body_text):
            wname = m.group(1)
            if wname not in with_map:
                continue
            trait = with_map[wname]
            upto = body_text[:m.start()].count("\n")
            call_line = body[upto][0]
            start = body_text.index("(", m.start())
            depth, k = 0, start
            while k < len(body_text):
                if body_text[k] == "(":
                    depth += 1
                elif body_text[k] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                k += 1
            arg = body_text[start + 1:k].strip()
            # 多行参数只取首行表达式
            arg_first = arg.split("\n")[0].strip()
            verdict, note = classify_arg(arg_first, params, fn_name, trait, callback_locals)
            if verdict == "部分支持" and note == "调用方提供":
                ref = f"{rel}:{param_lines.get(arg_first, call_line)}"
            elif verdict == "部分支持" and note == "依赖调用方回调" and arg_first in local_lines:
                ref = f"{rel}:{local_lines[arg_first]}"
            else:
                ref = f"{rel}:{call_line}"
            record(trait, verdict, note, ref)
        # 字段赋值 hostManager.xxxHost = Some(...) / context.xxxHost = Some(...)
        for m in re.finditer(r"(?:hostManager|context)\.(\w+) = Some\((.*?)\)", body_text, re.S):
            field = m.group(1)
            if field not in field_trait:
                continue
            trait = field_trait[field]
            arg = m.group(2).strip().split("\n")[0].strip()
            upto = body_text[:m.start()].count("\n")
            assign_line = body[upto][0]
            verdict, note = classify_arg(arg, params, fn_name, trait, callback_locals)
            if verdict == "部分支持" and note == "调用方提供":
                ref = f"{rel}:{param_lines.get(arg, assign_line)}"
            elif verdict == "部分支持" and note == "依赖调用方回调" and arg in local_lines:
                ref = f"{rel}:{local_lines[arg]}"
            else:
                ref = f"{rel}:{assign_line}"
            record(trait, verdict, note, ref)
    # android 特权版：只在标准版出现、特权版无注册的降为部分支持（仅标准版）
    if plat == "android":
        for trait, r in list(regs.items()):
            if r["variant"] == "standard" and r["fn"] == "createRuntimeHostManager" \
                    and "privileged" not in seen_variants.get(trait, set()):
                r["verdict"] = "部分支持"
                r["note"] = "仅标准版注册，特权版无此注册"
    for trait in slots:
        if trait in regs:
            r = regs[trait]
            matrix.setdefault(trait, {})[plat] = {
                "verdict": r["verdict"], "note": r["note"], "ref": r["ref"]}
        else:
            t = traits[trait]
            matrix.setdefault(trait, {})[plat] = {
                "verdict": "未查到", "note": "取数范围内无注册",
                "ref": f"{t['file']}:{t['line']}"}

# 人工复核覆盖：iOS SerialPortHost 已注册但 open 一律报错
matrix["SerialPortHost"]["ios"] = {
    "verdict": "部分支持", "note": "已注册，open 一律报错、无原生配件提供方",
    "ref": "hosts/ios/src/serial.rs:11"}
# 明确不支持：OHOS TtsSynthesisHost（README 明文）
matrix["TtsSynthesisHost"]["ohos"] = {
    "verdict": "不支持", "note": "API 18 SDK 无公开系统语音合成接口，不提供 SYSTEM_TTS",
    "ref": "hosts/ohos/README.md:29"}

# ---------- 5. 输出 ----------
counts = {}
for trait in slots:
    for plat in PLATFORMS:
        v = matrix[trait][plat]["verdict"]
        counts[v] = counts.get(v, 0) + 1

# RuntimeStorageHost：注册行只含 camelCase 局部变量时，改锚到构造实例的行
#（该行含 XxxRuntimeStorageHost，窗口内见 RuntimeStorageHost）。
# 限定为 `let runtimeStorageHost = ...` 行：同文件内另有 `let secrets =
# Arc::new(AndroidRuntimeStorageHost::new(...))`（android :82），不得锚到它。
for plat in PLATFORMS:
    lib_lines = (HOSTS / plat / "src/lib.rs").read_text(encoding="utf-8").splitlines()
    for j, ln in enumerate(lib_lines):
        if re.search(r"let runtimeStorageHost = Arc::new\(\w*RuntimeStorageHost::new\(", ln):
            c = matrix["RuntimeStorageHost"][plat]
            if c["verdict"] == "支持":
                c["ref"] = f"hosts/{plat}/src/lib.rs:{j + 1}"
            break

out = {"capabilities": slots, "platforms": PLATFORMS, "counts": counts,
       "trait_info": {t: {"file": traits[t]["file"], "line": traits[t]["line"],
                          "method_count": len(traits[t]["methods"]),
                          "methods": [m for m, _ in traits[t]["methods"]]}
                      for t in slots},
       "aux_traits_no_slot": sorted(set(traits) - set(slots)),
       "matrix": matrix}
Path("/tmp/host_matrix.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

# markdown 表格
hdr = "| 能力 | Android | iOS | Linux | macOS | OpenHarmony | Web | Windows |"
sep = "| --- | --- | --- | --- | --- | --- | --- | --- |"
rows = [hdr, sep]
for trait in slots:
    cells = []
    for plat in PLATFORMS:
        c = matrix[trait][plat]
        cell = c["verdict"]
        if c["note"] not in ("平台实现注册", "取数范围内无注册"):
            cell += f"（{c['note']}）"
        cell += f"（{c['ref']}）"
        cells.append(cell)
    rows.append(f"| {trait} | " + " | ".join(cells) + " |")
Path("/tmp/host_matrix_table.md").write_text("\n".join(rows) + "\n", encoding="utf-8")

# facts 草稿：每格一条 + trait 定义/槽位事实
# 注册行只含 camelCase 字段名时，事实措辞改用行内实际标识符（RuntimeSqliteHost、
# iOS/OHOS 的 WebSocketHost），使反引号符号落在 ref 行 ±5 内；槽位事实另立。
facts = []
for trait in slots:
    t = traits[trait]
    facts.append({"fact": f"`{trait}` trait 定义含 {len(t['methods'])} 个方法",
                  "ref": f"{t['file']}:{t['line']}"})
    facts.append({"fact": f"`{trait}` 在 HostManager 有注册槽位",
                  "ref": f"core/crates/foundation/host-api/src/HostManager.rs:{slot_field_line[trait]}"})
for trait in slots:
    for plat in PLATFORMS:
        c = matrix[trait][plat]
        pcn = PLATFORM_CN[plat]
        if trait == "TtsSynthesisHost" and plat == "ohos":
            facts.append({"fact": "OpenHarmony 不支持 TtsSynthesisHost：API 18 SDK 无公开系统语音合成接口，不提供 `SYSTEM_TTS`",
                          "ref": c["ref"]})
        elif trait == "RuntimeSqliteHost" and c["verdict"] == "支持":
            facts.append({"fact": f"{pcn} 的 createRuntimeHostManager 注册 `runtimeSqliteHost` 槽位",
                          "ref": c["ref"]})
        elif trait == "WebSocketHost" and plat in ("ios", "ohos"):
            import re as _re
            _line = (ROOT / c["ref"].split(":")[0]).read_text(encoding="utf-8").splitlines()[int(c["ref"].split(":")[1]) - 1]
            _cm = _re.search(r"Arc::new\((\w+)", _line)
            _concrete = _cm.group(1) if _cm else "HttpHost"
            facts.append({"fact": f"{pcn} 的 createRuntimeHostManager 把 `webSocketHost` 字段设为 `{_concrete}` 实例",
                          "ref": c["ref"]})
        elif c["verdict"] == "支持":
            f = f"{pcn} 的 createRuntimeHostManager 注册 `{trait}`"
        elif c["verdict"] == "不支持":
            f = f"{pcn} 不支持 `{trait}`：{c['note']}"
        elif c["verdict"] == "部分支持":
            f = f"{pcn} 的 `{trait}` 为部分支持：{c['note']}"
        else:
            f = f"{pcn} 的 createRuntimeHostManager 注册中未查到 `{trait}`"
        if not (trait == "TtsSynthesisHost" and plat == "ohos") and not (
                trait == "RuntimeSqliteHost" and c["verdict"] == "支持") and not (
                trait == "WebSocketHost" and plat in ("ios", "ohos")):
            facts.append({"fact": f, "ref": c["ref"]})
Path("/tmp/host_matrix_facts.json").write_text(json.dumps(facts, ensure_ascii=False, indent=2), encoding="utf-8")

print("traits total:", len(traits))
print("slots:", len(slots))
print("aux traits no slot:", sorted(set(traits) - set(slots)))
print("counts:", counts, "total cells:", sum(counts.values()))
print("facts draft:", len(facts))
for t in slots:
    print(f"  {t}: {len(traits[t]['methods'])} methods, {traits[t]['file']}:{traits[t]['line']}")
