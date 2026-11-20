#!/usr/bin/env python3
"""context 2.0 预算检查：读 governance/budgets.toml，量现状，写 reports/governance.md。"""
import argparse, subprocess, sys, tomllib
from pathlib import Path

def root() -> Path:
    return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="超预算时非零退出")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--write", action="store_true", help="写 reports/governance.md")
    a = ap.parse_args()

    r = root()
    b = tomllib.loads((r / "governance" / "budgets.toml").read_text(encoding="utf-8"))
    files_b = b.get("files", {})
    rows, bad = [], 0

    def check(path: Path, max_lines: int, max_bytes: int):
        nonlocal bad
        text = path.read_text(encoding="utf-8", errors="ignore")
        n, size = text.count("\n") + (0 if text.endswith("\n") else 1), len(text.encode())
        over = n > max_lines or size > max_bytes
        if over:
            bad += 1
        rows.append((str(path.relative_to(r)), n, max_lines, size, max_bytes, "OVER" if over else "ok"))

    for pat, key in (("NOTES/*.md", "notes"), ("PROJECTS/*.md", "projects"), ("DECISIONS/*.md", "decisions")):
        for p in sorted(r.glob(pat)):
            check(p, int(files_b.get(f"{key}_max_lines", 9999)), int(files_b.get(f"{key}_max_bytes", 10**9)))

    # STATE.recent 与 INDEX
    state = r / "STATE.yaml"
    if state.exists():
        lines = state.read_text(encoding="utf-8").splitlines()
        try:
            st = lines.index("recent:") + 1
        except ValueError:
            st = len(lines)
        n = 0
        for ln in lines[st:]:
            if ln.startswith("  - "):
                n += 1
            elif ln.strip() and not ln.startswith((" ", "\t")):
                break
        lim = int(b.get("state", {}).get("recent_max", 6))
        if n > lim:
            bad += 1
        rows.append(("STATE.yaml:recent", n, lim, 0, 0, "OVER" if n > lim else "ok"))
    idx = r / "INDEX.md"
    if idx.exists():
        size = idx.stat().st_size
        lim = int(b.get("index", {}).get("max_bytes", 12288))
        if size > lim:
            bad += 1
        rows.append(("INDEX.md", 0, 0, size, lim, "OVER" if size > lim else "ok"))

    out = r / "reports" / "governance.md"
    if not a.write:
        out = None
    else:
        out.parent.mkdir(exist_ok=True)
    table = ["# 治理报告（生成，勿手改）", "",
             "| 文件 | 行/上限 | 字节/上限 | 状态 |", "|---|---:|---:|---|"]
    for name, n, nl, size, sl, st in rows:
        table.append(f"| `{name}` | {n}/{nl if nl else '-'} | {size}/{sl if sl else '-'} | {st} |")
    table += ["", f"合计 {len(rows)} 项，超预算 {bad} 项。", ""]
    if out is not None:
        out.write_text("\n".join(table), encoding="utf-8")

    if not a.quiet:
        for name, n, nl, size, sl, st in rows:
            if st == "OVER":
                print(f"OVER  {name}  行 {n}/{nl}  字节 {size}/{sl}")
    print(f"-- budgets: {'FAIL' if bad else 'PASS'}（{len(rows)} 项，超 {bad}）")
    return 1 if (a.strict and bad) else 0

if __name__ == "__main__":
    sys.exit(main())
