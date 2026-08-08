#!/usr/bin/env python3
"""Inventory numbers in LaTeX prose and cross-check them against data.

Usage:
    python check_numbers.py <main.tex> [--ref numbers.txt] [--csv data.csv]

Extracts decimal numbers from prose lines and prints them with file and
line number. With --ref, every extracted number must appear in the
reference list. With --csv, numeric cells of the CSV form the reference
set.

Numbers inside math, cite/ref arguments, URLs, years and filenames are
excluded. The output is a review aid: it tells you where each number
appears so it can be checked against the data source. It does not prove
correctness.

Exit code: 0 when no numbers are missing from the reference set, 1
otherwise. Without --ref or --csv, the exit code is always 0.
"""

import argparse
import csv
import re
import sys
from pathlib import Path

NUMBER = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")
YEAR = re.compile(r"^(?:19|20)\d{2}$")
COMMAND_ARGS = re.compile(
    r"\\(?:cite|citep|citet|ref|eqref|pageref|label|includegraphics|input|include)"
    r"(?:\[[^\]]*\])?\{[^}]*\}"
)
URL = re.compile(r"https?://\S+")
MATH_MARKERS = ("$", "\\[", "\\]", "\\begin{align", "\\begin{equation", "\\begin{math}")


def is_math_or_skip(line):
    stripped = line.strip()
    if stripped.startswith("%"):
        return True
    return any(marker in line for marker in MATH_MARKERS)


def normalize(value):
    return float(value.replace(",", "").rstrip("%"))


def collect_reference_set(paths, csv_path):
    refs = set()
    if csv_path:
        with open(csv_path, encoding="utf-8", errors="replace", newline="") as handle:
            for row in csv.reader(handle):
                for cell in row:
                    cell = cell.strip()
                    if cell and re.fullmatch(r"\d[\d,]*\.?\d*%?", cell):
                        refs.add(round(normalize(cell), 4))
    if paths:
        for path in paths:
            with open(path, encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    line = line.strip()
                    if line and re.fullmatch(r"\d[\d,]*\.?\d*%?", line):
                        refs.add(round(normalize(line), 4))
    return refs


def extract(path):
    found = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return found
    in_body = False
    in_bib = False
    for index, line in enumerate(lines, 1):
        if not in_body:
            if "\\begin{document}" in line:
                in_body = True
            continue
        if "\\begin{thebibliography}" in line:
            in_bib = True
            continue
        if "\\end{thebibliography}" in line:
            in_bib = False
            continue
        if in_bib:
            continue
        if is_math_or_skip(line):
            continue
        cleaned = COMMAND_ARGS.sub(" ", line)
        cleaned = URL.sub(" ", cleaned)
        for match in NUMBER.finditer(cleaned):
            token = match.group(0)
            if YEAR.fullmatch(token):
                continue
            found.append((index, token))
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("texfile", help="main .tex file")
    parser.add_argument("--ref", action="append", default=[], help="reference number list file")
    parser.add_argument("--csv", help="data CSV whose numeric cells form the reference set")
    args = parser.parse_args()

    path = Path(args.texfile)
    if not path.is_file():
        print(f"[ERROR] Not a file: {path}")
        return 1

    found = extract(path)
    print(f"[INFO] 正文检出 {len(found)} 个数字（不含公式与引用参数）。")
    if not args.ref and not args.csv:
        for index, token in found:
            print(f"  {path}:{index}: {token}")
        print("[INFO] 未提供对照数据，以上为人工核对清单。")
        return 0

    refs = collect_reference_set(args.ref, args.csv)
    missing = []
    for index, token in found:
        value = round(normalize(token), 4)
        if value not in refs:
            missing.append((index, token))
    if missing:
        print(f"[FAIL] {len(missing)} 个数字不在数据源中：")
        for index, token in missing[:40]:
            print(f"  {path}:{index}: {token}")
        return 1
    print("[OK] 正文数字都能在数据源中找到。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
