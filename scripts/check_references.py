#!/usr/bin/env python3
"""Check reference integrity and flag likely fabrication risks.

Usage:
    python check_references.py <references.bib> [--tex <main.tex>] [--online]

Offline checks:
- duplicate keys
- missing required fields (title, author, year)
- implausible year
- key year that differs from entry year
- entry year that contradicts the arXiv ID prefix
- "and others" or "et al." in the author field
- malformed DOI

With --tex, the bibliography labels in the tex file are compared with the
bib entry years, and unused bib entries are listed.

With --online:
- arXiv IDs are looked up on the arXiv API
- DOIs are looked up on Crossref
- entries without arXiv or DOI are listed for manual search

Exit code: 0 when no blocking issues, 1 when blocking issues are found.
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REQUIRED_FIELDS = {"title", "author", "year"}
ARXIV_ID = re.compile(r"(\d{4}\.\d{4,5}(?:v\d+)?|[a-z-]+/\d{7})")
DOI = re.compile(r"10\.\d{4,9}/[^\s,}]+")
YEAR_IN_KEY = re.compile(r"(?:19|20)\d{2}")
BIBITEM = re.compile(r"\\bibitem\s*(\[[^\]]*\])?\s*\{([^}]*)\}")


def parse_bib(text):
    entries = []
    for match in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text, re.IGNORECASE):
        entry_type = match.group(1).lower()
        key = match.group(2).strip()
        start = match.end()
        depth = 1
        index = start
        while index < len(text) and depth > 0:
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
            index += 1
        block = text[start : index - 1]
        fields = {}
        for field_match in re.finditer(r"(\w+)\s*=\s*", block):
            name = field_match.group(1).lower()
            value_start = field_match.end()
            while value_start < len(block) and block[value_start] in " \t\r\n":
                value_start += 1
            if value_start >= len(block):
                continue
            if block[value_start] == "{":
                depth = 1
                value_end = value_start + 1
                while value_end < len(block) and depth > 0:
                    if block[value_end] == "{":
                        depth += 1
                    elif block[value_end] == "}":
                        depth -= 1
                    value_end += 1
                value = block[value_start + 1 : value_end - 1]
            elif block[value_start] in "\"'":
                quote = block[value_start]
                end_quote = block.find(quote, value_start + 1)
                value = (
                    block[value_start + 1 : end_quote]
                    if end_quote != -1
                    else block[value_start:]
                )
            else:
                end_bare = block.find(",", value_start)
                value = (
                    block[value_start:end_bare]
                    if end_bare != -1
                    else block[value_start:]
                )
            fields[name] = value.strip()
        entries.append((entry_type, key, fields))
    return entries


def parse_bibitems(text):
    items = {}
    for match in BIBITEM.finditer(text):
        label = match.group(1)
        key = match.group(2).strip()
        label_year = None
        if label:
            year_match = YEAR_IN_KEY.search(label)
            if year_match:
                label_year = year_match.group(0)
        items[key] = label_year
    return items


def arxiv_year_hint(arxiv_id):
    match = re.match(r"(\d{2})\d{2}\.\d{4,5}", arxiv_id)
    if not match:
        return None
    prefix = int(match.group(1))
    if prefix <= 6:
        return 2000 + prefix
    return 2000 + prefix


def offline_checks(entries):
    fails = []
    warns = []
    seen = {}
    for entry_type, key, fields in entries:
        if key in seen:
            fails.append(f"重复 key: {key}")
        seen[key] = entry_type

        missing = [name for name in REQUIRED_FIELDS if not fields.get(name)]
        if missing:
            fails.append(f"{key}: 缺少字段 {', '.join(missing)}")

        year = fields.get("year", "")
        if year:
            if not re.fullmatch(r"\d{4}", year) or not (1950 <= int(year) <= 2030):
                fails.append(f"{key}: 年份不合理 {year}")

        key_year = None
        key_match = YEAR_IN_KEY.search(key)
        if key_match:
            key_year = key_match.group(0)
            if year and key_year != year:
                warns.append(f"{key}: key 年份 {key_year} 与条目年份 {year} 不一致")

        authors = fields.get("author", "")
        if re.search(r"\b(others|et al\.)\b", authors, re.IGNORECASE):
            warns.append(f"{key}: author 字段含 others/et al.，投稿前应补全作者")

        arxiv_id = find_arxiv_id(fields)
        if arxiv_id:
            hint = arxiv_year_hint(arxiv_id)
            if hint and year:
                if abs(int(year) - hint) > 1:
                    warns.append(
                        f"{key}: arXiv {arxiv_id} 年份前缀 {hint} 与条目年份 {year} 不一致"
                    )

        doi = fields.get("doi", "")
        if doi and not DOI.search(doi):
            warns.append(f"{key}: DOI 格式可疑 {doi[:60]}")

    return fails, warns


def find_arxiv_id(fields):
    for name in ("eprint", "url", "journal", "note"):
        value = fields.get(name, "")
        match = ARXIV_ID.search(value)
        if match:
            return match.group(1)
    return None


def http_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "check_references/1.0"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.read().decode("utf-8", errors="replace")


def online_checks(entries):
    results = []
    network_ok = True
    for entry_type, key, fields in entries:
        arxiv_id = find_arxiv_id(fields)
        doi = fields.get("doi", "")
        if arxiv_id:
            try:
                payload = http_json(
                    f"https://export.arxiv.org/api/query?id_list={urllib.parse.quote(arxiv_id)}"
                )
                exists = "<entry>" in payload and arxiv_id.split("v")[0] in payload
                results.append((key, "arXiv", arxiv_id, exists))
            except (urllib.error.URLError, TimeoutError, OSError):
                network_ok = False
                break
        elif doi:
            try:
                payload = http_json(
                    f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
                )
                data = json.loads(payload)
                exists = data.get("status") == "ok"
                results.append((key, "DOI", doi, exists))
            except (urllib.error.URLError, TimeoutError, OSError, ValueError):
                network_ok = False
                break
    return results, network_ok


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bibfile", help="references.bib file")
    parser.add_argument("--tex", help="main .tex file for bibliography label comparison")
    parser.add_argument("--online", action="store_true", help="verify arXiv and DOI online")
    args = parser.parse_args()

    path = Path(args.bibfile)
    if not path.is_file():
        print(f"[ERROR] Not a file: {path}")
        return 1
    text = path.read_text(encoding="utf-8", errors="replace")
    entries = parse_bib(text)
    if not entries:
        print("[ERROR] No bib entries parsed.")
        return 1

    fails, warns = offline_checks(entries)
    print(f"[INFO] {len(entries)} 条文献")

    if fails:
        print(f"[FAIL] {len(fails)} 个问题：")
        for item in fails:
            print(f"  - {item}")
    else:
        print("[OK] 无结构性错误。")

    if warns:
        print(f"\n[WARN] {len(warns)} 项需人工核对：")
        for item in warns:
            print(f"  - {item}")

    if args.tex:
        tex_path = Path(args.tex)
        if not tex_path.is_file():
            print(f"[ERROR] Not a file: {args.tex}")
            return 1
        bibitems = parse_bibitems(
            tex_path.read_text(encoding="utf-8", errors="replace")
        )
        by_key = {key: fields for _, key, fields in entries}
        print("\n[VS-TEX] 与 thebibliography 对照：")
        any_mismatch = False
        for key, label_year in bibitems.items():
            fields = by_key.get(key)
            if fields is None:
                print(f"  - {key}: thebibliography 有条目，但 .bib 中没有")
                any_mismatch = True
                continue
            year = fields.get("year", "")
            if label_year and year and label_year != year:
                print(
                    f"  - {key}: 标签年份 {label_year} 与 bib 条目年份 {year} 不一致"
                )
                any_mismatch = True
        unused = sorted(set(by_key) - set(bibitems))
        if unused:
            print(f"  - bib 中未被引用的条目：{', '.join(unused)}")
        if not any_mismatch and not unused:
            print("  一致。")
        if any_mismatch:
            fails.append("thebibliography 与 .bib 年份不一致")

    if args.online:
        print("\n[ONLINE] 联网核验：")
        results, network_ok = online_checks(entries)
        if not network_ok:
            print("  网络不可用，跳过联网核验。")
        else:
            for key, kind, identifier, exists in results:
                status = "存在" if exists else "未找到"
                print(f"  - {key} ({kind} {identifier}): {status}")
            no_id = [
                key for _, key, fields in entries
                if not find_arxiv_id(fields) and not fields.get("doi")
            ]
            if no_id:
                print(f"  无 arXiv/DOI 的条目，需人工检索标题确认：{', '.join(no_id)}")

    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
