#!/usr/bin/env bash
#
# Skill validator: structure + script syntax.
#
# Structure checks:
#   - SKILL.md exists with `name:` and `description:` frontmatter
#   - every markdown link to references/ or scripts/ resolves
#   - agents/openai.yaml, if present, has an `interface:` block
#
# Script syntax checks (best-effort, skipped when an interpreter is missing):
#   - *.py        parsed with ast (no bytecode written)
#   - *.js/.cjs/.mjs  `node --check`
#   - *.sh        `bash -n`
#
# Usage:
#   ./validate.sh [skill_dir]
#   ./validate.sh --no-scripts [skill_dir]

set -u

check_scripts=1
if [ "${1:-}" = "--no-scripts" ]; then
  check_scripts=0
  shift
fi

skill_dir="${1:-$(dirname "$0")/..}"
skill_dir="$(cd "$skill_dir" && pwd)"

fail=0

msg() { printf '%s\n' "$*"; }
err() { msg "FAIL: $*"; fail=1; }

skill_md="$skill_dir/SKILL.md"

if [ ! -f "$skill_md" ]; then
  err "missing SKILL.md"
  exit 1
fi

# frontmatter check
head -c 200 "$skill_md" | grep -q '^---$' || err "SKILL.md does not start with YAML frontmatter"
grep -qE '^name:[[:space:]]' "$skill_md" || err "SKILL.md missing 'name:'"
grep -qE '^description:' "$skill_md" || err "SKILL.md missing 'description:'"

if command -v grep >/dev/null 2>&1; then
  # internal reference links
  rel_links=$(grep -oE '\]\((\./)?(references|scripts)/[^)]*\)' "$skill_md" \
    | sed -E 's/^\]\((\.\/)?//; s/\)$//' | sort -u)
  while IFS= read -r link; do
    [ -z "$link" ] && continue
    target="$skill_dir/$link"
    if [ ! -e "$target" ]; then
      err "broken link in SKILL.md -> $link"
    fi
  done <<EOF
$rel_links
EOF
fi

# references dir consistency: if references/ exists, every .md there should be
# reachable from SKILL.md (warn only, not fatal)
if [ -d "$skill_dir/references" ]; then
  for ref in "$skill_dir"/references/*.md; do
    [ -e "$ref" ] || continue
    base="$(basename "$ref")"
    if ! grep -q "references/$base" "$skill_md"; then
      msg "WARN: references/$base not referenced from SKILL.md"
    fi
  done
fi

if [ -f "$skill_dir/agents/openai.yaml" ]; then
  if ! grep -q '^interface:' "$skill_dir/agents/openai.yaml"; then
    err "agents/openai.yaml missing 'interface:' section"
  fi
fi

# ---- script syntax checks -------------------------------------------------
if [ "$check_scripts" -eq 1 ] && [ -d "$skill_dir/scripts" ]; then
  py_ok=0; js_ok=0; sh_ok=0
  command -v python >/dev/null 2>&1 && py_ok=1
  command -v node   >/dev/null 2>&1 && js_ok=1
  command -v bash   >/dev/null 2>&1 && sh_ok=1

  while IFS= read -r f; do
    [ -z "$f" ] && continue
    case "$f" in
      *.py)
        if [ "$py_ok" -eq 1 ]; then
          python -c 'import ast,sys;ast.parse(open(sys.argv[1],encoding="utf-8",errors="replace").read())' "$f" 2>/dev/null \
            || err "python syntax error: ${f#$skill_dir/}"
        fi
        ;;
      *.js|*.cjs|*.mjs)
        if [ "$js_ok" -eq 1 ]; then
          node --check "$f" >/dev/null 2>&1 || err "node syntax error: ${f#$skill_dir/}"
        fi
        ;;
      *.sh)
        if [ "$sh_ok" -eq 1 ] && [ "$f" != "$skill_dir/scripts/validate.sh" ]; then
          bash -n "$f" 2>/dev/null || err "bash syntax error: ${f#$skill_dir/}"
        fi
        ;;
    esac
  done <<EOF
$(find "$skill_dir/scripts" -type f 2>/dev/null)
EOF
fi

if [ "$fail" -eq 0 ]; then
  msg "OK: $skill_dir"
else
  msg "INVALID: $skill_dir"
  exit 1
fi
