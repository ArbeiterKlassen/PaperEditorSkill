#!/usr/bin/env python3
"""Scan TeX and Markdown files for common AI-text style patterns.

Usage:
    python check_ai_style.py <file-or-dir> [--max-sentence-words 45]

Flags with file and line number:
- formulaic openers and filler phrases, Chinese and English
- buzzwords that cannot be verified quantitatively
- sentences longer than the word threshold
- repeated paragraph connectors above a document-level count
- mechanical ordinal enumeration in prose (第X，/ 第X件), which no vocabulary
  list catches and which readers reliably recognise as machine-written
- demonstrative tags such as 这一条 / 这一点 used as sentence props

Exit code: 0 when no flags, 1 when flags are found.
"""

import argparse
import re
import sys
from pathlib import Path

PATTERNS = [
    (re.compile(r"值得注意的是"), "空话开头"),
    (re.compile(r"不难看出"), "空话开头"),
    (re.compile(r"众所周知"), "空话开头"),
    (re.compile(r"近年来"), "空话开头"),
    (re.compile(r"随着.{0,15}的发展"), "空话开头"),
    (re.compile(r"综上所述|总而言之"), "空洞过渡"),
    (re.compile(r"首先|其次"), "排比堆砌"),
    (re.compile(r"显著提升|大幅提升|大幅提高|显著改善"), "大词空词"),
    (re.compile(r"深入探索|深入挖掘|赋能|抓手|落地"), "大词空词"),
    (re.compile(r"\bit is worth noting\b", re.IGNORECASE), "空话开头"),
    (re.compile(r"\bnotably\b", re.IGNORECASE), "空话开头"),
    (re.compile(r"\bin conclusion\b", re.IGNORECASE), "空洞过渡"),
    (re.compile(r"\bin recent years\b", re.IGNORECASE), "空话开头"),
    (re.compile(r"\bwith the rapid (development|growth|advance)", re.IGNORECASE), "空话开头"),
    (re.compile(r"\bdelve( into)?\b", re.IGNORECASE), "大词空词"),
    (re.compile(r"\bleverage\b", re.IGNORECASE), "大词空词"),
    (re.compile(r"\bfacilitate\b", re.IGNORECASE), "大词空词"),
    (re.compile(r"\bseamless\b", re.IGNORECASE), "大词空词"),
    (re.compile(r"\bintricate\b", re.IGNORECASE), "大词空词"),
    (re.compile(r"\bmultifaceted\b", re.IGNORECASE), "大词空词"),
    (re.compile(r"\bparadigm shift\b", re.IGNORECASE), "大词空词"),
    (re.compile(r"\bgroundbreaking\b", re.IGNORECASE), "大词空词"),
    (re.compile(r"\bpivotal\b", re.IGNORECASE), "大词空词"),
    (re.compile(r"\bunderscore(s|d)?\b", re.IGNORECASE), "大词空词"),
    (re.compile(r"\bcomprehensive\b", re.IGNORECASE), "大词空词"),
    (re.compile(r"\bfalsifiable\b", re.IGNORECASE), "拽词"),
    (re.compile(r"\bshed light on\b", re.IGNORECASE), "拽词"),
    (re.compile(r"\bparamount\b", re.IGNORECASE), "拽词"),
    (re.compile(r"\bquintessential\b", re.IGNORECASE), "拽词"),
    (re.compile(r"\brobustly\b", re.IGNORECASE), "拽词"),
    (re.compile(r"\bholistically\b", re.IGNORECASE), "拽词"),
    (re.compile(r"\bmoreover\b|\bfurthermore\b|\badditionally\b", re.IGNORECASE), "连接词"),
]

SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+")
WORD = re.compile(r"[A-Za-z\u4e00-\u9fff]+")
COUNT_PATTERNS = [
    (re.compile(r"\bmoreover\b|\bfurthermore\b|\badditionally\b", re.IGNORECASE), "连接词", 5),
    (re.compile(r"\bstate-of-the-art\b|\bSOTA\b", re.IGNORECASE), "SOTA 出现次数", 4),
    (re.compile(r"\bsignificant(ly)?\b", re.IGNORECASE), "significant 出现次数", 6),
    (re.compile(r"首先|其次|最后"), "排比连接词", 3),
    (re.compile(r"[\u2013\u2014]"), "破折号", 2),
    (re.compile(r"\uFF1A"), "全角冒号", 3),
    (re.compile(r"[\u201C\u201D\u2018\u2019]"), "引号", 1),
    (re.compile(r"第[一二三四五六七八九][，、]"), "序数分点句", 0),
    (re.compile(r"第[一二三四五六七八九](件|种|个)"), "序数分点句", 3),
    # 结构层次（双线划分、三层结构、证明步骤、主张编号）允许少量使用，
    # 阈值放宽到 12；真正要清零的是带逗号的散文序数分点。
    (re.compile(r"第[一二三四五六七八九](层|条|步|部分|方面|类)"), "序数分点句", 12),
    (re.compile(r"(这一条|这一点|这条主张|这条曲线|这条结论|这条原则|该判据|该机制|该原则|该主张)"), "指代标签句", 5),
    (re.compile(r"(需要说明的是|要写清|必须承认|值得一提的是|这里要说明|不可混同|需明确区分|需要指出的是)"), "元话语开场", 2),
    # 模板腔段首：专利与说明书体"所述 X 的……如下"，十余处即构成模板节奏，
    # 不必清零，改一半破节奏；阈值 8。
    (re.compile(r"所述[^。：，]{2,22}如下[。：]"), "模板腔段首", 8),
    # 内部编辑提示：定稿必须清零，阈值 0。
    (re.compile(r"(请按实际修改|请根据实际情况|若与实际不符|待补充|待核对)"), "内部编辑提示", 0),
    # 中文之间的斜杠（和/或、组会/会议），文件路径与公式场景需人工排除，阈值 3。
    (re.compile(r"[一-鿿]/[一-鿿]"), "正文斜杠", 3),
]

TARGET_EXT = {".tex", ".md"}


def is_skip_line(line):
    stripped = line.strip()
    return (
        stripped.startswith("%")
        or stripped.startswith("#")
        or stripped.startswith("\\bibitem")
        or stripped.startswith("\\begin{thebibliography}")
        or stripped.startswith("\\end{thebibliography}")
    )


def scan_file(path, max_words):
    flags = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return flags, ""
    text = "\n".join(
        line for line in lines if not is_skip_line(line)
    )
    for index, line in enumerate(lines, 1):
        if is_skip_line(line):
            continue
        stripped = line.strip()
        for pattern, label in PATTERNS:
            if pattern.search(stripped):
                flags.append(f"{path}:{index} [{label}] {stripped[:90]}")
        if "$" not in line and "\\[" not in line and "\\]" not in line and "&" not in line:
            for sentence in SENTENCE_BREAK.split(stripped):
                words = len(WORD.findall(sentence))
                if words > max_words:
                    flags.append(
                        f"{path}:{index} [长句 {words} 词] {sentence[:90]}"
                    )
    return flags, text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help=".tex or .md file, or directory")
    parser.add_argument("--max-sentence-words", type=int, default=45)
    args = parser.parse_args()

    target = Path(args.target)
    if target.is_dir():
        files = sorted(
            p for p in target.rglob("*")
            if p.is_file() and p.suffix.lower() in TARGET_EXT
        )
    elif target.is_file() and target.suffix.lower() in TARGET_EXT:
        files = [target]
    else:
        print(f"[ERROR] Not a .tex or .md file or directory: {target}")
        return 1

    flags = []
    all_text = ""
    for path in files:
        file_flags, text = scan_file(path, args.max_sentence_words)
        flags.extend(file_flags)
        all_text += text

    for pattern, label, limit in COUNT_PATTERNS:
        count = len(pattern.findall(all_text))
        if count > limit:
            flags.append(f"[计数] {label} {count} 次（阈值 {limit}）")

    if flags:
        print(f"[FLAG] {len(flags)} 处需要人工判断：")
        for item in flags:
            print(f"  - {item}")
        return 1
    print("[OK] 未发现明显 AI 痕迹词。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
