#!/usr/bin/env python3
"""Check numbering, cross-reference, appendix and layout consistency of a paper.

Usage:
    python check_consistency.py <paper-dir> [--codes DIR] [--log FILE] [--pdf FILE]
                                [--body-range 22-25] [--appendix-range 20-30]
                                [--appendix-marker 附录] [--exclude archive] [--strict]

Checks:
1. 交叉引用层：每个 \\label 是否至少被一个 \\ref 引用，每个 \\ref 是否有对应 \\label。
2. 正文写死层：正文里的 表 9 / 图 3 / 第 6.2 节 / §6.1 / 式 (5)。插入新的表格或插图后，
   这些写死的编号会整体漂移，而 LaTeX 与 check_submission.py 都不会报错。
3. 脚本写死层：代码注释与 print 里的 论文表 3 / 表 2 / 图 1 一类编号，同样会漂移。
    4. 附录完整性：--codes 目录下每个源文件都应在 \\lstinputlisting 里出现，
   且每个 listing 与 \\input 的目标文件都要存在。
    5. 页数配平：--pdf 里正文与附录的页数，对照目标区间（默认正文 22-25、附录 20-30）。
    6. 字体缺字：--log 里的 Missing character 行，附录代码中的 ①②∝ 之类会渲染成空白框。

未指定 --codes / --log / --pdf 时，按论文目录的同级 codes/ 与目录内最新的 .log/.pdf 自动识别。
附录起点取 PDF 里第一次以标记词“开头成行”的那一页（允许前置 A. / 1 / Appendix A 之类的小节标号），
因此正文里“见附录 3”这种行内提及不会误判。判错时用更具体的 --appendix-marker。

Exit code: 0 无阻断项，1 有阻断项；--strict 时警告也算阻断。
"""

import argparse
import re
import sys
from pathlib import Path

LABEL = re.compile(r"\\label\{([^}]+)\}")
REF = re.compile(r"\\(?:ref|eqref|autoref|Cref|cref|nameref)\{([^}]+)\}")
LISTING = re.compile(r"\\lstinputlisting(?:\[[^\]]*\])?\{([^}]+)\}")
INPUT = re.compile(r"\\(?:input|include)\{([^}]+)\}")

# 正文里写死的编号。用 \\ref 的写法不含数字，因此不会命中。
TEX_HARD = [
    (re.compile(r"(?<![A-Za-z0-9_])表\s*\d+"), "表号"),
    (re.compile(r"(?<![A-Za-z0-9_])图\s*\d+"), "图号"),
    (re.compile(r"式\s*\(\s*\d+"), "公式号"),
    (re.compile(r"第\s*\d+(?:\.\d+)*\s*[节章表图页]"), "章节号"),
    (re.compile(r"§\s*\d"), "章节号"),
]

# 代码里写死的编号：注释与 print 标签是最常见的两处。
CODE_HARD = [
    (re.compile(r"论文\s*[表图]\s*\d+"), "论文编号"),
    (re.compile(r"(?<![A-Za-z0-9_])[表图]\s*\d+"), "编号"),
]

SRC_EXT = {
    ".py", ".m", ".jl", ".r", ".c", ".cc", ".cpp", ".h", ".hpp", ".java",
    ".sh", ".js", ".mjs", ".cjs", ".sql", ".do", ".stan", ".ipynb",
}
MISSING_CHAR = re.compile(r"Missing character:\s*There is no (.+?) in font")
SKIP_PARTS = ("archive", ".git", "node_modules", "__pycache__")


def parse_range(text, fallback):
    if not text:
        return fallback
    text = text.strip()
    for pattern, mapper in ((r"^(\d+)\s*-\s*(\d+)$", lambda m: (int(m.group(1)), int(m.group(2)))),
                            (r"^(\d+)$", lambda m: (int(m.group(1)), int(m.group(1))))):
        match = re.match(pattern, text)
        if match:
            return mapper(match)
    raise SystemExit(f"[ERROR] 区间格式应为 A-B 或 N，收到：{text}")


def strip_comment(line):
    """去掉未转义的 % 之后的注释，保留 \\% 与 \\\\。"""
    out = []
    index = 0
    while index < len(line):
        char = line[index]
        if char == "\\" and index + 1 < len(line):
            out.append(line[index:index + 2])
            index += 2
            continue
        if char == "%":
            break
        out.append(char)
        index += 1
    return "".join(out)


def read_lines(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def tex_sources(root, excludes):
    files = []
    for path in sorted(root.rglob("*.tex")):
        parts = set(path.parts)
        if any(skip in parts for skip in SKIP_PARTS):
            continue
        rel = path.relative_to(root).as_posix()
        if any(bad in rel for bad in excludes):
            continue
        files.append((path, rel))
    return files


def check_tex(root, codes_dirs, excludes):
    fails, warns = [], []
    labels, refs, listing_seen = {}, [], []
    input_targets = []
    tex_count = 0

    for path, rel in tex_sources(root, excludes):
        tex_count += 1
        for index, raw in enumerate(read_lines(path), 1):
            line = strip_comment(raw)
            if not line.strip():
                continue
            for match in LABEL.finditer(line):
                labels.setdefault(match.group(1), (rel, index))
            for match in REF.finditer(line):
                refs.append((rel, index, match.group(1)))
            for match in LISTING.finditer(line):
                listing_seen.append((rel, index, match.group(1), path.parent))
            for match in INPUT.finditer(line):
                input_targets.append((rel, index, match.group(1), path.parent))
            for pattern, kind in TEX_HARD:
                for match in pattern.finditer(line):
                    warns.append((
                        "正文写死编号",
                        f"{rel}:{index} 写死{kind}“{match.group(0).strip()}”，应改用 \\ref: {line.strip()[:80]}",
                    ))

    referenced = {target for _, _, target in refs}
    for name, (rel, index) in labels.items():
        if name not in referenced:
            warns.append(("label 未引用", f"{rel}:{index} label 未被任何 \\ref 引用: {name}"))
    for rel, index, target in refs:
        if target not in labels:
            fails.append(f"{rel}:{index} \\ref 指向不存在的 label: {target}")

    for rel, index, target, base in input_targets:
        if not (base / target).exists() and not (base / target).with_suffix(".tex").exists():
            fails.append(f"{rel}:{index} \\input 目标不存在: {target}")

    listed_names = set()
    for rel, index, target, base in listing_seen:
        candidate = base / target
        if not candidate.exists():
            fails.append(f"{rel}:{index} \\lstinputlisting 目标不存在: {target}")
        listed_names.add(Path(target).name)

    for codes in codes_dirs:
        sources = [
            p for p in sorted(codes.rglob("*"))
            if p.is_file() and p.suffix.lower() in SRC_EXT and not any(s in p.parts for s in SKIP_PARTS)
        ]
        missing = [p for p in sources if p.name not in listed_names]
        for path in missing:
            warns.append(("附录缺文件", f"{path.name}：在 {codes} 内但没有任何 \\lstinputlisting 挂载它"))
        if sources:
            warns.append((
                "附录完整性",
                f"{codes.name}/ 源文件 {len(sources)} 个，附录 listing 目标 {len(listed_names)} 个，"
                f"未挂载 {len(missing)} 个；附录须含全部可运行源程序时，未挂载即不合规",
            ))

    info = f"扫描 {tex_count} 个 .tex：label {len(labels)} 个，\\ref {len(refs)} 处，listing 目标 {len(listed_names)} 个"
    return fails, warns, info


def check_codes(codes_dirs, excludes):
    warns = []
    for codes in codes_dirs:
        for path in sorted(codes.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in SRC_EXT:
                continue
            if any(s in path.parts for s in SKIP_PARTS):
                continue
            rel = path.as_posix()
            if any(bad in rel for bad in excludes):
                continue
            for index, line in enumerate(read_lines(path), 1):
                for pattern, kind in CODE_HARD:
                    for match in pattern.finditer(line):
                        warns.append((
                            "代码写死编号",
                            f"{path.name}:{index} 写死{kind}“{match.group(0).strip()}”，"
                            f"正文增删浮动体后会漂移: {line.strip()[:80]}",
                        ))
    return warns


def check_log(log_path):
    warns, info = [], ""
    if not log_path or not Path(log_path).is_file():
        return warns, info
    counter = {}
    for line in read_lines(Path(log_path)):
        match = MISSING_CHAR.search(line)
        if match:
            counter[match.group(1)] = counter.get(match.group(1), 0) + 1
    if counter:
        detail = "、".join(f"{char} ×{count}" for char, count in sorted(counter.items()))
        warns.append((
            "字体缺字",
            f"{Path(log_path).name}: 字体缺字 {sum(counter.values())} 处（{detail}）。"
            "附录代码里的这类字符会渲染成空白框，换成中文或 ASCII 再重编译",
        ))
    info = f"日志 {Path(log_path).name}：字体缺字字符 {len(counter)} 种"
    return warns, info


def check_pdf(pdf_path, marker, body_range, appendix_range, appendix_page=None):
    warns, infos = [], []
    if not pdf_path or not Path(pdf_path).is_file():
        return warns, infos
    try:
        import pymupdf as fitz  # PyMuPDF >= 1.24
    except Exception:
        try:
            import fitz
        except Exception:
            return warns, [f"跳过页数检查：未安装 PyMuPDF（pip install pymupdf），无法读取 {pdf_path}"]

    # 标题行：可选的 A. / 1 小节标号前缀，然后是标记词本身。
    heading = re.compile(
        r"^\s{0,6}(?:[A-Z]\.?|\d{1,2}\.?)?\s*" + re.escape(marker)
    )
    doc = fitz.open(pdf_path)
    total = doc.page_count
    if appendix_page:
        start = int(appendix_page)
        hits = [start]
    else:
        hits = [
            index + 1 for index, page in enumerate(doc)
            if any(heading.match(line) for line in page.get_text().splitlines())
        ]
        if not hits:
            return warns, [
                f"{Path(pdf_path).name} 总 {total} 页；没有以“{marker}”开头的标题行，跳过正文/附录页数拆分。"
                "换更具体的 --appendix-marker，或直接给 --appendix-page"
            ]
        start = hits[0]
    body = start - 1
    appendix = total - start + 1
    infos.append(
        f"{Path(pdf_path).name} 共 {total} 页：正文 {body} 页（目标 {body_range[0]}-{body_range[1]}），"
        f"附录 {appendix} 页（目标 {appendix_range[0]}-{appendix_range[1]}），附录标题在第 {start} 页"
    )
    if len(hits) > 1:
        infos.append(f"“{marker}”还出现在第 {', '.join(str(h) for h in hits[1:])} 页；"
                     f"若正文提前提到该词导致起点取错，请换更具体的标记词")
    if not body_range[0] <= body <= body_range[1]:
        warns.append(("页数", f"正文 {body} 页超出目标 {body_range[0]}-{body_range[1]} 页"))
    if not appendix_range[0] <= appendix <= appendix_range[1]:
        warns.append(("页数", f"附录 {appendix} 页超出目标 {appendix_range[0]}-{appendix_range[1]} 页"))
    return warns, infos


def newest(directory, suffix):
    if not directory or not Path(directory).is_dir():
        return None
    candidates = [p for p in Path(directory).glob(f"*{suffix}") if p.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paper", help="论文目录，内含 .tex 源文件")
    parser.add_argument("--codes", action="append", default=[],
                        help="附录代码目录，可重复；默认取论文目录同级的 codes/")
    parser.add_argument("--log", help="LaTeX 编译日志；默认取论文目录内最新的 .log")
    parser.add_argument("--pdf", help="编译产物 PDF；默认取论文目录内最新的 .pdf")
    parser.add_argument("--body-range", default="22-25", help="正文页数目标区间，默认 22-25")
    parser.add_argument("--appendix-range", default="20-30", help="附录页数目标区间，默认 20-30")
    parser.add_argument("--appendix-marker", default="附录", help="附录标题里的标记词，默认“附录”")
    parser.add_argument("--appendix-page", help="直接指定附录起始页，跳过文本定位")
    parser.add_argument("--exclude", action="append", default=[],
                        help="路径含该子串时跳过，可重复")
    parser.add_argument("--max-per-kind", type=int, default=5,
                        help="每类警告最多列几条，默认 5；要看全部给一个大数")
    parser.add_argument("--strict", action="store_true", help="警告也算阻断")
    args = parser.parse_args()

    root = Path(args.paper)
    if not root.is_dir():
        print(f"[ERROR] 不是目录：{root}")
        return 1

    codes_dirs = [Path(p) for p in args.codes]
    if not codes_dirs:
        guess = root.parent / "codes"
        if guess.is_dir():
            codes_dirs = [guess.resolve()]

    log_path = args.log or newest(root, ".log")
    pdf_path = args.pdf or newest(root, ".pdf")

    body_range = parse_range(args.body_range, (22, 25))
    appendix_range = parse_range(args.appendix_range, (20, 30))

    fails, warns, infos = [], [], []
    tex_fails, tex_warns, tex_info = check_tex(root, codes_dirs, args.exclude)
    fails += tex_fails
    warns += tex_warns
    infos.append(tex_info)
    warns += check_codes(codes_dirs, args.exclude)
    log_warns, log_info = check_log(log_path)
    warns += log_warns
    if log_info:
        infos.append(log_info)
    pdf_warns, pdf_infos = check_pdf(pdf_path, args.appendix_marker, body_range, appendix_range,
                                     args.appendix_page)
    warns += pdf_warns
    infos += pdf_infos

    for item in infos:
        print(f"[INFO] {item}")
    if fails:
        print(f"\n[FAIL] {len(fails)} 处阻断项：")
        for item in fails:
            print(f"  - {item}")
    if warns:
        groups = {}
        for group, message in warns:
            groups.setdefault(group, []).append(message)
        print(f"\n[WARN] {len(warns)} 处需人工判断（按类折叠，每类最多 {args.max_per_kind} 条）：")
        for group, items in groups.items():
            print(f"  [{group}] {len(items)} 处")
            for message in items[:args.max_per_kind]:
                print(f"    - {message}")
            rest = len(items) - args.max_per_kind
            if rest > 0:
                print(f"    ... 另有 {rest} 处同类，看全量加 --max-per-kind 999")
    if not fails and not warns:
        print("\n[OK] 编号、附录完整性与页数均一致。")
    elif not fails and not args.strict:
        print("\n[OK] 无阻断项（警告项按人工判断处理）。")

    return 1 if fails or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
