#!/usr/bin/env python3
"""Self-check for the badge logic: python3 scripts/test_statusline.py"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PAYLOAD = json.dumps({"workspace": {"current_dir": HERE},
                      "context_window": {"used_percentage": 10}})


def render(enabled_plugins, flags):
    """Run statusline.py against a throwaway HOME and return its output."""
    with tempfile.TemporaryDirectory() as home:
        os.mkdir(os.path.join(home, ".claude"))
        if enabled_plugins is not None:
            with open(os.path.join(home, ".claude", "settings.json"), "w") as f:
                json.dump({"enabledPlugins": enabled_plugins}, f)
        for flag, level in flags.items():
            with open(os.path.join(home, ".claude", f".{flag}-active"), "w") as f:
                f.write(level)
        return subprocess.run(
            [sys.executable, os.path.join(HERE, "statusline.py")],
            input=PAYLOAD, capture_output=True, text=True,
            env={**os.environ, "HOME": home},
        ).stdout


both = {"caveman": "full", "ponytail": "full"}

out = render({"caveman@caveman": True, "ponytail@ponytail": True}, both)
assert "CAVEMAN" in out and "PONYTAIL" in out, out

# Stale flag, plugin no longer enabled: badge stays dark.
out = render({"ccrc@ccrc": True}, both)
assert "CAVEMAN" not in out and "PONYTAIL" not in out, out

out = render({"caveman@caveman": True}, {"caveman": "ultra", "ponytail": "full"})
assert "CAVEMAN:ULTRA" in out and "PONYTAIL" not in out, out

# No enabledPlugins key at all (project-scoped install): trust the flags.
out = render(None, both)
assert "CAVEMAN" in out and "PONYTAIL" in out, out

print("ok")
