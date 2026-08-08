#!/usr/bin/env python3
"""Snapshot a paper package into archive/v<N> with a changelog entry.

Usage:
    python snapshot_version.py <package-dir> [--message "变更说明"] [--next 22]

Copies source files and PDFs into archive/v<N>/, excluding build artifacts.
Appends one line to archive/CHANGELOG.md.

Exit code: 0 on success, 1 on error.
"""

import argparse
import re
import shutil
import sys
from datetime import date
from pathlib import Path

IGNORED_SUFFIXES = {
    ".aux", ".log", ".out", ".toc", ".nav", ".snm", ".vrb",
    ".fls", ".fdb_latexmk", ".synctex.gz", ".zip", ".gz", ".tmp",
}
IGNORED_DIRS = {"archive", ".git", "__pycache__"}


def next_version(package, override):
    if override:
        return override
    archive = package / "archive"
    versions = []
    if archive.is_dir():
        for item in archive.iterdir():
            if item.is_dir():
                match = re.fullmatch(r"v(\d+)", item.name)
                if match:
                    versions.append(int(match.group(1)))
    return max(versions, default=0) + 1


def ignore_build(dirname, names):
    ignored = set()
    base = Path(dirname)
    for name in names:
        path = base / name
        if path.is_dir():
            if name in IGNORED_DIRS:
                ignored.add(name)
        elif path.suffix.lower() in IGNORED_SUFFIXES:
            ignored.add(name)
    return ignored


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", help="paper package directory")
    parser.add_argument("--message", default="", help="one-line change note")
    parser.add_argument("--next", type=int, help="explicit next version number")
    args = parser.parse_args()

    package = Path(args.package).resolve()
    if not package.is_dir():
        print(f"[ERROR] Not a directory: {package}")
        return 1

    version = next_version(package, args.next)
    archive = package / "archive"
    target = archive / f"v{version}"
    if target.exists():
        print(f"[ERROR] Snapshot already exists: {target}")
        return 1

    shutil.copytree(package, target, ignore=ignore_build)
    message = args.message.strip() or "no note"
    line = f"v{version} {date.today().isoformat()}: {message}"
    changelog = archive / "CHANGELOG.md"
    with changelog.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")

    print(f"[OK] Snapshot created: {target}")
    print(f"[OK] Changelog: {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
