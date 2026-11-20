#!/usr/bin/env python3
"""context 2.0 领域检查：6 条通用工具查不了的运行时不变量。

R1 ADR supersede 一致性  R2 STATE.recent 上限  R3 车道租约过期
R4 OPEN 必须有 project   R5 同一 IP:port 多处出现  R6 NOTES 禁“回复式”文件名
"""
import re, subprocess, sys, time
from pathlib import Path

def repo_root() -> Path:
    out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
    return Path(out)

def front_matter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    d = {}
    for line in m.group(1).splitlines():
        if line.startswith((" ", "\t", "-")) or ":" not in line:
            continue
        k, v = line.split(":", 1)
        d[k.strip()] = v.strip().strip('"')
    return d

def count_recent(state_text: str) -> int:
    lines = state_text.splitlines()
    try:
        start = lines.index("recent:") + 1
    except ValueError:
        return 0
    n = 0
    for line in lines[start:]:
        if line.startswith("  - "):
            n += 1
        elif line.strip() and not line.startswith((" ", "\t")):
            break
    return n

def is_loopback_ipport(v: str) -> bool:
    import ipaddress
    host = v.rsplit(":", 1)[0]
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return host in {"localhost", "::1"}


def parse_ids(raw) -> set:
    """把 `D-0018` / `[18,19]` / `18` 统一成 {D-0018, ...}。"""
    if raw is None:
        return set()
    text = str(raw).strip().strip("[]")
    out = set()
    for part in re.split(r"[,\s]+", text):
        part = part.strip().strip('"\'')
        if not part:
            continue
        m = re.fullmatch(r"(?:D-)?(\d{1,4})", part)
        if m:
            out.add("D-%04d" % int(m.group(1)))
    return out

def main() -> int:
    root = repo_root()
    errors, hints = [], []

    # R1 决策取代一致性
    dstat = {}
    for p in sorted((root / "DECISIONS").glob("*.md")):
        fm = front_matter(p.read_text(encoding="utf-8"))
        did = (fm.get("id") or "").split("#")[0].strip()
        if did:
            dstat[did] = ((fm.get("status") or "").split("#")[0].strip(), p)
    for p in sorted((root / "DECISIONS").glob("*.md")):
        text = p.read_text(encoding="utf-8")
        fm = front_matter(text)
        targets = set(re.findall(r"反转\s*(D-\d{4})", text))
        targets |= parse_ids(fm.get("supersedes"))
        for d in sorted(targets):
            if d in dstat and dstat[d][0] != "superseded":
                errors.append(f"{p.name} 声称取代/反转 {d}，但 {dstat[d][1].name} 仍是 {dstat[d][0] or '(空)'}")

    # R2 recent 上限（预算读 governance/budgets.toml）
    try:
        import tomllib
        budgets_path = root / "governance" / "budgets.toml"
        budgets = tomllib.loads(budgets_path.read_text(encoding="utf-8"))
    except Exception:
        budgets = {}
    limit = int(budgets.get("state", {}).get("recent_max", 6))
    state = root / "STATE.yaml"
    if state.exists():
        n = count_recent(state.read_text(encoding="utf-8"))
        if n > limit:
            errors.append(f"STATE.recent 有 {n} 条，超过预算 {limit}")

    # R3 车道：已迁 GitHub Issues；LANES/ 残留只提示
    lanes = root / "LANES"
    if lanes.is_dir() and any(lanes.glob("*.yaml")):
        hints.append("LANES/ 已废弃（车道在 GitHub Issues，`lane list`），确认无遗漏后 git rm -r LANES")

    # R4 OPEN 归属
    openf = root / "OPEN.yaml"
    if openf.exists():
        text = openf.read_text(encoding="utf-8")
        blocks = re.split(r"(?m)^  - id:\s*", text)[1:]
        project_of = {}
        for b in blocks:
            oid = b.split("\n", 1)[0].strip()
            pm = re.search(r"(?m)^\s+project:\s*(\S+)\s*$", b)
            sm = re.search(r"(?m)^\s+status:\s*(\S+)\s*$", b)
            if sm and sm.group(1) == "resolved":
                continue
            project_of[oid] = pm.group(1).strip('"') if pm else ""
            if not project_of[oid]:
                msg = f"{oid} 在 open 状态但没有 project 字段"
                (errors if root.name == "workspace" else hints).append(msg)
            elif root.name == "workspace" and project_of[oid] == "server":
                errors.append(f"{oid} 是系统级事项（project=server），应迁到 profile/context")

    # R5 同一 IP:port 多处出现（AGENTS 与 NOTES 不得重复）
    ipre = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}:\d{2,5}\b")
    seen = {}
    candidates = []
    agents = root.parent / "AGENTS.md"
    if agents.exists():
        candidates.append(agents)
    candidates += sorted((root / "NOTES").glob("*.md"))
    for p in candidates:
        for v in set(ipre.findall(p.read_text(encoding="utf-8", errors="ignore"))):
            if is_loopback_ipport(v):
                continue
            seen.setdefault(v, set()).add(p.name)
    for v, files in sorted(seen.items()):
        if "AGENTS.md" in files and len(files) > 1:
            hints.append(f"{v} 同时出现在 AGENTS.md 与 {', '.join(sorted(files - {'AGENTS.md'}))}（一处为准，其余给指针）")

    # R6 NOTES 文件名
    for p in sorted((root / "NOTES").glob("*.md")):
        if re.search(r"-(reply|reply-service|contract-ack|ack|final|final-review)$", p.stem):
            errors.append(f"NOTES/{p.name} 属“回复式”命名，应合并进主题文件")
        elif re.search(r"-(handoff|review)-?\d*$", p.stem):
            hints.append(f"NOTES/{p.name} 是阶段性交接/评审，后续应并入主题文件")

    # R7 本仓 SCHEMA 只写差异，通用规则在 governance/SCHEMA.md
    schema = root / "SCHEMA.md"
    if schema.exists():
        stext = schema.read_text(encoding="utf-8")
        slines = len(stext.splitlines())
        smax = 40
        try:
            import tomllib
            bpath = Path(__file__).resolve().parents[1] / "budgets.toml"
            smax = int(tomllib.loads(bpath.read_text()).get("schema", {}).get("max_lines", 40))
        except Exception:
            pass
        if "governance/SCHEMA.md" not in stext:
            errors.append("SCHEMA.md 未指向 governance/SCHEMA.md（通用规则应在治理仓，本仓只写差异）")
        if slines > smax:
            errors.append(f"SCHEMA.md 有 {slines} 行，超过 schema.max_lines={smax}；通用内容应在 governance/SCHEMA.md")

    for h in hints:
        print(f"HINT  {h}")
    for e in errors:
        print(f"ERROR {e}")
    if errors:
        print(f"-- domain_check: FAIL（{len(errors)} 处，{len(hints)} 提示）")
        return 1
    print(f"-- domain_check: PASS（{len(hints)} 提示）")
    return 0

if __name__ == "__main__":
    sys.exit(main())
