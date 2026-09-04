#!/usr/bin/env python3
"""ccrc powerline statusline.

Reads Claude Code session JSON on stdin, prints two ANSI lines:
  1. session name | model | cwd | git | PR
  2. context bar | cost | 5h + 7d rate limits | mode badges

Everything except the git branch comes from the payload; see
https://code.claude.com/docs/en/statusline for the schema.
"""
import json
import os
import subprocess
import sys
import zlib

RESET = "\033[0m"
SEP = ""          # powerline right arrow
G_GIT = ""        # branch
G_TREE = ""       # worktree
G_TAG = ""        # session name
G_BOT = "\U000f06a9"    # model (nf-md-robot)
G_DIR = ""        # cwd
G_PR = ""         # pull request

# Session-name colors: medium-dark 256 shades, all readable under white text.
NAME_COLORS = [25, 26, 54, 55, 56, 88, 89, 90, 94, 95, 96, 124, 125, 126,
               130, 131, 132, 160, 161, 166, 167, 168, 22, 23, 28, 29, 64,
               65, 70, 71, 97, 98]


def fg(c):
    return f"\033[38;5;{c}m"


def bg(c):
    return f"\033[48;5;{c}m"


def dig(d, *path, default=None):
    """Nested dict lookup that tolerates missing keys and null values."""
    for key in path:
        if not isinstance(d, dict):
            return default
        d = d.get(key)
        if d is None:
            return default
    return d


def heat(pct):
    """Background color for a 0-100 usage percentage."""
    if pct < 50:
        return 28
    if pct < 75:
        return 136
    if pct < 90:
        return 166
    return 160


class Line:
    """Accumulates powerline segments and renders them with separators."""

    def __init__(self):
        self.parts = []
        self.prev = None

    def seg(self, bg_c, fg_c, text):
        if not text:
            return self
        if self.prev is not None:
            self.parts.append(f"{bg(bg_c)}{fg(self.prev)}{SEP}{RESET}")
        self.parts.append(f"{bg(bg_c)}{fg(fg_c)} {text} {RESET}")
        self.prev = bg_c
        return self

    def render(self):
        if self.prev is None:
            return ""
        return "".join(self.parts) + f"{fg(self.prev)}{SEP}{RESET}"


def link(url, text):
    """OSC 8 hyperlink. Degrades to plain text in terminals without support."""
    return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"


def enabled_plugins():
    """Plugin names from `enabledPlugins` in user settings ("<name>@<marketplace>").

    None when the key is absent or unreadable: the flag file is then the only
    evidence there is, so it gets trusted.
    """
    try:
        with open(os.path.expanduser("~/.claude/settings.json")) as f:
            entries = json.load(f).get("enabledPlugins")
    except (OSError, ValueError):
        return None
    if not isinstance(entries, dict):
        return None
    return {name.split("@")[0] for name, on in entries.items() if on}


def mode_badges(line):
    """Badges for the caveman/ponytail plugins, which drop a flag file when on.

    Nothing removes that flag on exit, so it outlives the session that wrote it
    and the badge would keep burning after the plugin is disabled or removed.
    Cross-check it against the enabled plugin list.
    ponytail: user settings only, add project scopes if per-project enabling
    ever matters.
    """
    enabled = enabled_plugins()
    for flag, label, bg_c in (("caveman", "CAVEMAN", 172), ("ponytail", "PONYTAIL", 108)):
        if enabled is not None and flag not in enabled:
            continue
        path = os.path.expanduser(f"~/.claude/.{flag}-active")
        try:
            with open(path) as f:
                level = f.read().strip()
        except OSError:
            continue
        text = label if level in ("", "full") else f"{label}:{level.upper()}"
        line.seg(bg_c, 232, text)


def short_cwd(cwd):
    home = os.path.expanduser("~")
    disp = cwd.replace(home, "~", 1) if cwd.startswith(home) else cwd
    if len(disp) > 30:
        disp = f".../{os.path.basename(os.path.dirname(cwd))}/{os.path.basename(cwd)}"
    return disp


def git_branch(cwd):
    try:
        out = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    if out.returncode != 0:
        return ""
    branch = out.stdout.strip()
    if branch != "HEAD":
        return branch
    # Detached: show the short SHA instead.
    out = subprocess.run(
        ["git", "-C", cwd, "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True, timeout=2,
    )
    return out.stdout.strip()


def build_identity(d, cwd):
    line = Line()

    # Session name is absent until /rename, --name, or an AI-generated title
    # exists, so fall back to the session id to keep panes distinguishable.
    name = dig(d, "session_name") or dig(d, "session_id", default="")[:8]
    if name:
        color = NAME_COLORS[zlib.crc32(name.encode()) % len(NAME_COLORS)]
        line.seg(color, 255, f"{G_TAG} {name}")

    model = dig(d, "model", "display_name")
    if model:
        effort = dig(d, "effort", "level")
        text = f"{G_BOT} {model}"
        if effort:
            text += f"·{effort}"
        if dig(d, "fast_mode"):
            text += " ⚡"
        line.seg(24, 255, text)

    line.seg(240, 255, f"{G_DIR} {short_cwd(cwd)}")

    branch = git_branch(cwd)
    if branch:
        text = f"{G_GIT} {branch}"
        worktree = dig(d, "worktree", "name") or dig(d, "workspace", "git_worktree")
        if worktree:
            text += f" {G_TREE} {worktree}"
        line.seg(22, 255, text)

    pr_num = dig(d, "pr", "number")
    if pr_num:
        state = dig(d, "pr", "review_state", default="")
        bg_c = {"approved": 28, "changes_requested": 88,
                "pending": 94, "draft": 238}.get(state, 94)
        kind = "MR" if dig(d, "pr", "kind") == "mr" else "PR"
        text = f"{G_PR} {kind} #{pr_num}"
        url = dig(d, "pr", "url")
        line.seg(bg_c, 255, link(url, text) if url else text)

    return line.render()


def build_budget(d):
    line = Line()

    pct = dig(d, "context_window", "used_percentage")
    if pct is not None:
        pct = int(pct)
        size = dig(d, "context_window", "context_window_size", default=0)
        used = (dig(d, "context_window", "total_input_tokens", default=0)
                + dig(d, "context_window", "total_output_tokens", default=0))
        filled = pct * 12 // 100
        bar = "█" * filled + "░" * (12 - filled)
        text = f"{bar} {pct}%"
        if size:
            cap = f"{size // 1000000}M" if size >= 1000000 else f"{size // 1000}k"
            text += f" {used // 1000}k/{cap}"
        line.seg(heat(pct), 255, text)

    cost = dig(d, "cost", "total_cost_usd")
    if cost:
        line.seg(54, 255, f"${cost:.2f}")

    for key, label in (("five_hour", "5h"), ("seven_day", "7d")):
        used = dig(d, "rate_limits", key, "used_percentage")
        if used is not None:
            line.seg(heat(used), 255, f"{label} {int(used)}%")

    mode_badges(line)
    return line.render()


def main():
    try:
        d = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return
    if not isinstance(d, dict):
        return

    cwd = dig(d, "workspace", "current_dir") or dig(d, "cwd") or os.getcwd()
    for out in (build_identity(d, cwd), build_budget(d)):
        if out:
            print(out)


if __name__ == "__main__":
    main()
