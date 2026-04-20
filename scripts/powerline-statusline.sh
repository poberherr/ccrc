#!/bin/bash
# Powerline-style statusline for Claude Code.
# Reads session JSON from stdin, prints segmented status with Nerd Font glyphs.
# Segments: [CAVEMAN] | model | cwd | git(branch+worktree) | tokens

set -u

INPUT=$(cat)

j() { printf '%s' "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d$1 if d$1 is not None else '')" 2>/dev/null; }

MODEL=$(j "['model']['display_name']")
CWD=$(j "['workspace']['current_dir']")
PROJECT=$(j "['workspace']['project_dir']")
TRANSCRIPT=$(j "['transcript_path']")

[ -z "$CWD" ] && CWD="$PWD"

# Powerline glyphs (Nerd Font)
SEP=$'\ue0b0'
BRANCH=$'\ue0a0'
TREE=$'\uf1bb'

# 256-color palette
C_CAVE_BG=172; C_CAVE_FG=232
C_MODEL_BG=24;  C_MODEL_FG=255
C_CWD_BG=240;   C_CWD_FG=255
C_GIT_BG=22;    C_GIT_FG=255
C_TOK_BG=54;    C_TOK_FG=255
C_RESET=$'\033[0m'

fg() { printf '\033[38;5;%sm' "$1"; }
bg() { printf '\033[48;5;%sm' "$1"; }

PREV_BG=""
seg() {
  local bg_c=$1 fg_c=$2 text=$3
  if [ -n "$PREV_BG" ]; then
    printf '%s%s%s' "$(bg "$bg_c")$(fg "$PREV_BG")" "$SEP" "$C_RESET"
  fi
  printf '%s%s %s %s' "$(bg "$bg_c")" "$(fg "$fg_c")" "$text" "$C_RESET"
  PREV_BG=$bg_c
}

end_caps() {
  if [ -n "$PREV_BG" ]; then
    printf '%s%s%s' "$(fg "$PREV_BG")" "$SEP" "$C_RESET"
  fi
}

# Caveman badge (only if active)
CAVE_FLAG="$HOME/.claude/.caveman-active"
if [ -f "$CAVE_FLAG" ]; then
  MODE=$(cat "$CAVE_FLAG" 2>/dev/null)
  [ -z "$MODE" ] && MODE="full"
  LABEL="CAVEMAN"
  [ "$MODE" != "full" ] && LABEL="CAVEMAN:$(echo "$MODE" | tr '[:lower:]' '[:upper:]')"
  seg $C_CAVE_BG $C_CAVE_FG "$LABEL"
fi

# Model
[ -n "$MODEL" ] && seg $C_MODEL_BG $C_MODEL_FG "󰚩 $MODEL"

# CWD (replace $HOME with ~)
DISP_CWD="${CWD/#$HOME/~}"
# Shorten: keep last 2 path components if long
if [ ${#DISP_CWD} -gt 30 ]; then
  DISP_CWD=".../$(basename "$(dirname "$CWD")")/$(basename "$CWD")"
fi
seg $C_CWD_BG $C_CWD_FG " $DISP_CWD"

# Git branch + worktree
if cd "$CWD" 2>/dev/null && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  GIT_BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || git rev-parse --short HEAD 2>/dev/null)
  GIT_TEXT="$BRANCH $GIT_BRANCH"
  # Worktree detection: .git is a file in linked worktrees
  GIT_DIR=$(git rev-parse --git-dir 2>/dev/null)
  COMMON_DIR=$(git rev-parse --git-common-dir 2>/dev/null)
  if [ "$GIT_DIR" != "$COMMON_DIR" ]; then
    WT_NAME=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)")
    GIT_TEXT="$GIT_TEXT $TREE $WT_NAME"
  fi
  seg $C_GIT_BG $C_GIT_FG "$GIT_TEXT"
fi

# Token usage from transcript JSONL (last assistant message usage)
if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ]; then
  TOK=$(python3 - "$TRANSCRIPT" <<'PY' 2>/dev/null
import json, sys
path = sys.argv[1]
last = None
try:
    with open(path) as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            u = (d.get('message') or {}).get('usage') if isinstance(d.get('message'), dict) else None
            if u:
                last = u
except Exception:
    sys.exit(0)
if not last:
    sys.exit(0)
total = (last.get('input_tokens') or 0) + (last.get('cache_read_input_tokens') or 0) + (last.get('cache_creation_input_tokens') or 0) + (last.get('output_tokens') or 0)
# Context window 200k for Claude
pct = total * 100 // 200000
print(f"{total//1000}k {pct}%")
PY
)
  [ -n "$TOK" ] && seg $C_TOK_BG $C_TOK_FG "󰈸 $TOK"
fi

end_caps
