#!/usr/bin/env python3
"""Compile a LaTeX project and summarize errors and warnings.

Usage:
    python compile_latex.py <main.tex or directory> [--engine xelatex] [--max-runs 5]

The script:
1. Finds the main .tex file.
2. Runs the engine with -interaction=nonstopmode.
3. Runs bibtex or biber when the auxiliary file shows citations.
4. Re-runs the engine until references stabilize or max runs is reached.
5. Parses the log for errors, warnings, undefined references and citations.
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


def find_main_tex(target):
    target = Path(target)
    if target.is_file():
        return target
    if target.is_dir():
        texs = sorted(target.glob("*.tex"))
    else:
        texs = sorted(Path.cwd().glob("*.tex"))
    if len(texs) == 1:
        return texs[0]
    if not texs:
        print("[ERROR] No .tex file found.")
        return None
    print("[ERROR] Multiple .tex files found; specify the main file explicitly:")
    for tex in texs:
        print(f"        {tex}")
    return None


def run_command(cmd, cwd):
    print(f"[RUN] {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode


def parse_log(log_path):
    if not log_path.exists():
        return None
    lines = log_path.read_text(errors="replace").splitlines()
    errors = []
    warnings = []
    undefined = []
    for line in lines:
        if re.search(r"^! |Error:", line):
            errors.append(line.strip())
        elif re.search(r"Warning:", line):
            warnings.append(line.strip())
        if re.search(r"undefined (reference|citation|label)", line, re.IGNORECASE):
            undefined.append(line.strip())
    return errors, warnings, undefined


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", nargs="?", default=".", help="main .tex file or directory")
    parser.add_argument("--engine", default="xelatex")
    parser.add_argument("--max-runs", type=int, default=5)
    args = parser.parse_args()

    if not shutil.which(args.engine):
        print(f"[ERROR] {args.engine} not found in PATH. Install TeX Live or update PATH.")
        return 1

    main_tex = find_main_tex(args.target)
    if main_tex is None:
        return 1

    workdir = main_tex.parent
    jobname = main_tex.stem
    aux_path = workdir / f"{jobname}.aux"
    log_path = workdir / f"{jobname}.log"

    for _ in range(args.max_runs):
        run_command(
            [args.engine, "-interaction=nonstopmode", "-file-line-error", main_tex.name],
            workdir,
        )
        aux_text = aux_path.read_text(errors="replace") if aux_path.exists() else ""
        if "biblatex" in aux_text:
            run_command(["biber", jobname], workdir)
        elif "\\bibdata" in aux_text:
            run_command(["bibtex", jobname], workdir)
        log_text = log_path.read_text(errors="replace") if log_path.exists() else ""
        if "Rerun to get" not in log_text and "Label(s) may have changed" not in log_text:
            break

    parsed = parse_log(log_path)
    if parsed is None:
        print("[ERROR] Log file not found.")
        return 1
    errors, warnings, undefined = parsed

    pdf_path = workdir / f"{jobname}.pdf"
    if errors:
        print("\n[FAIL] Errors found:")
        for line in errors[:20]:
            print(f"  {line}")
    if undefined:
        print("\n[FAIL] Undefined references or citations:")
        for line in undefined[:20]:
            print(f"  {line}")
    if warnings:
        print(f"\n[INFO] Warnings: {len(warnings)}. First 10:")
        for line in warnings[:10]:
            print(f"  {line}")

    if pdf_path.exists() and not errors and not undefined:
        print(f"\n[OK] {pdf_path.name} compiled successfully.")
        return 0
    print("\n[FAIL] Compilation did not finish cleanly.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
