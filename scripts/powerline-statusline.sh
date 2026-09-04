#!/bin/bash
# Entry point for the ccrc statusline. Kept as a .sh because settings.json
# invokes it with `bash`; the rendering lives in statusline.py.
set -u
SELF="${BASH_SOURCE[0]}"
while [ -L "$SELF" ]; do
  TARGET=$(readlink "$SELF")
  case "$TARGET" in
    /*) SELF="$TARGET" ;;
    *)  SELF="$(dirname "$SELF")/$TARGET" ;;
  esac
done
exec python3 "$(cd "$(dirname "$SELF")" && pwd)/statusline.py"
