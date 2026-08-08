#!/usr/bin/env python3
"""Scan a paper package for common submission issues.

Usage:
    python check_submission.py <package-dir> [--anonymous]

Checks:
1. Backup or old-version files in the package.
2. Stale version notes in source comments.
3. Anonymous-submission leaks (with --anonymous):
   - active author or affiliation blocks that are not placeholders
   - Chinese comments and real names in .tex/.bib sources
   - absolute local paths
4. Undefined references or citations in .log files.
5. \\cite keys without a matching \\bibitem or bib entry.
6. \\includegraphics, \\input and \\include targets that do not exist.

Exit code: 0 when no blocking issues, 1 when blocking issues are found.
"""

import argparse
import re
import sys
from pathlib import Path

BACKUP_PATTERN = re.compile(
    r"(backup|\.bak$|_old$|\.old$|\.orig$|\.tmp$|\.temp$| - Copy$| copy$)",
    re.IGNORECASE,
)
VERSION_NOTE = re.compile(r"(?<![A-Za-z0-9])v\d{1,3}\b")
CJK = re.compile(r"[\u4e00-\u9fff]")
ABS_PATH = re.compile(
    r"(?:/home/|/Users/|/data\d*/|/workspace/|/root/|/tmp/|"
    r"[A-Za-z]:[\\/]Users[\\/]|[A-Za-z]:[\\/]Windows[\\/]|"
    r"[A-Za-z]:[\\/]Program\sFiles)"
)
UNDEFINED = re.compile(
    r"undefined (reference|citation|label)|multiply defined",
    re.IGNORECASE,
)
CITE = re.compile(r"\\cite(?:t|p)?(?:\[[^\]]*\])?\{([^}]*)\}")
BIBITEM = re.compile(r"\\bibitem(?:\[[^\]]*\])?\{([^}]*)\}")
BIBENTRY = re.compile(r"@\w+\{([^,]+),")
REFERENCE = re.compile(r"\\(?:includegraphics|input|include|bibliography)(?:\[[^\]]*\])?\{([^}]*)\}")

TEXT_EXT = {
    ".tex", ".bib", ".py", ".md", ".txt", ".sty", ".cls", ".bst",
    ".sh", ".yml", ".yaml", ".json", ".csv",
}
REF_EXT = [".pdf", ".png", ".jpg", ".jpeg", ".tex"]


def is_comment_line(line):
    stripped = line.strip()
    return stripped.startswith("%") or stripped.startswith("#") or stripped.startswith("//")


def scan(package, anonymous):
    package = Path(package)
    fails = []
    warns = []
    files = sorted(
        p for p in package.rglob("*")
        if p.is_file() and ".git" not in p.parts and "archive" not in p.parts
    )

    for path in files:
        rel = path.relative_to(package).as_posix()
        if BACKUP_PATTERN.search(path.name):
            fails.append(f"{rel}: 备份或旧版本文件")

        if path.suffix.lower() not in TEXT_EXT:
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        active_lines = []
        for index, line in enumerate(lines, 1):
            stripped = line.strip()
            if anonymous:
                if CJK.search(line):
                    warns.append(f"{rel}:{index} 源文件含中文字符: {stripped[:80]}")
                if ABS_PATH.search(line):
                    fails.append(f"{rel}:{index} 绝对路径: {stripped[:80]}")
                if re.search(r"\\author\s*\{", line):
                    if is_comment_line(line):
                        warns.append(f"{rel}:{index} 注释中的作者块: {stripped[:80]}")
                    elif "Anonymous" not in line:
                        fails.append(f"{rel}:{index} 非匿名作者块: {stripped[:80]}")
                if re.search(r"\\affiliations\s*\{", line):
                    if is_comment_line(line):
                        warns.append(f"{rel}:{index} 注释中的机构块: {stripped[:80]}")
                    elif "Paper ID" not in line:
                        fails.append(f"{rel}:{index} 真实机构信息: {stripped[:80]}")
            if (
                path.suffix.lower() not in {".sty", ".bst", ".cls"}
                and is_comment_line(line)
                and VERSION_NOTE.search(line)
            ):
                warns.append(f"{rel}:{index} 注释中的版本号: {stripped[:80]}")
            if not is_comment_line(line):
                active_lines.append((index, line))

        text = "\n".join(line for _, line in active_lines)
        for match in REFERENCE.finditer(text):
            ref = match.group(1).strip()
            if not ref:
                continue
            candidate = path.parent / ref
            exists = False
            if candidate.suffix.lower() in REF_EXT or not candidate.suffix:
                exists = candidate.exists()
            if not exists:
                for ext in REF_EXT:
                    if candidate.with_suffix(ext).exists():
                        exists = True
                        break
            if not exists:
                fails.append(f"{rel}: 引用的文件不存在: {ref}")

    if anonymous:
        for path in files:
            if path.suffix.lower() in TEXT_EXT:
                continue
            try:
                data = path.read_bytes()
            except OSError:
                continue
            if len(data) > 200 * 1024 * 1024:
                continue
            rel = path.relative_to(package).as_posix()
            for match in re.finditer(rb"[\x20-\x7e]{6,}", data):
                text = match.group(0).decode("ascii", errors="ignore")
                if ABS_PATH.search(text):
                    fails.append(f"{rel}: 二进制文件含路径: {text[:100]}")
                    break

    cited = set()
    defined = set()
    for path in files:
        if path.suffix.lower() not in {".tex", ".bib"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        active = "\n".join(
            line for line in text.splitlines() if not is_comment_line(line)
        )
        for match in CITE.finditer(active):
            for key in match.group(1).split(","):
                if key.strip():
                    cited.add(key.strip())
        for match in BIBITEM.finditer(active):
            defined.add(match.group(1).strip())
        for match in BIBENTRY.finditer(active):
            defined.add(match.group(1).strip())
    for key in sorted(cited - defined):
        fails.append(f"引用了未定义的 key: {key}")

    for path in files:
        if path.suffix.lower() != ".log":
            continue
        rel = path.relative_to(package).as_posix()
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            if UNDEFINED.search(line):
                fails.append(f"{rel}: {line.strip()[:100]}")

    return fails, warns


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", help="paper package directory")
    parser.add_argument("--anonymous", action="store_true", help="scan for anonymous-submission leaks")
    args = parser.parse_args()

    package = Path(args.package)
    if not package.is_dir():
        print(f"[ERROR] Not a directory: {package}")
        return 1

    fails, warns = scan(package, args.anonymous)

    if fails:
        print(f"[FAIL] {len(fails)} blocking issue(s):")
        for item in fails:
            print(f"  - {item}")
    else:
        print("[OK] No blocking issues.")

    if warns:
        print(f"\n[WARN] {len(warns)} item(s) to review manually:")
        for item in warns:
            print(f"  - {item}")

    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
