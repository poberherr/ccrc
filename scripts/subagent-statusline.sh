#!/bin/bash
set -u
SELF="${BASH_SOURCE[0]}"
while [ -L "$SELF" ]; do
  TARGET=$(readlink "$SELF")
  case "$TARGET" in
    /*) SELF="$TARGET" ;;
    *)  SELF="$(dirname "$SELF")/$TARGET" ;;
  esac
done
exec python3 "$(cd "$(dirname "$SELF")" && pwd)/subagent-statusline.py"
