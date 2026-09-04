#!/usr/bin/env python3
"""ccrc subagent statusline.

Renders one row per visible subagent in the agent panel. Reads a single JSON
object on stdin containing `columns` and a `tasks` array; prints one line per
task. See https://code.claude.com/docs/en/statusline#subagent-status-lines
"""
import json
import os
import sys
import time

RESET = "\033[0m"

STATUS_GLYPH = {
    "running": ("▸", 33),
    "in_progress": ("▸", 33),
    "pending": ("○", 244),
    "queued": ("○", 244),
    "completed": ("✓", 34),
    "done": ("✓", 34),
    "failed": ("✗", 160),
    "error": ("✗", 160),
}


def fg(c):
    return f"\033[38;5;{c}m"


def dim(text):
    return f"{fg(244)}{text}{RESET}"


def elapsed(start):
    """Seconds since `start`, which arrives as epoch ms, epoch s, or ISO 8601."""
    if start is None:
        return None
    if isinstance(start, (int, float)):
        secs = start / 1000 if start > 1e11 else start
    else:
        try:
            from datetime import datetime
            secs = datetime.fromisoformat(str(start).replace("Z", "+00:00")).timestamp()
        except (ValueError, TypeError):
            return None
    delta = int(time.time() - secs)
    if delta < 0:
        return None
    if delta < 60:
        return f"{delta}s"
    if delta < 3600:
        return f"{delta // 60}m{delta % 60:02d}s"
    return f"{delta // 3600}h{(delta % 3600) // 60:02d}m"


def visible_len(text):
    """Length ignoring ANSI escape sequences."""
    out, i = 0, 0
    while i < len(text):
        if text[i] == "\033":
            while i < len(text) and text[i] not in "m":
                i += 1
            i += 1
            continue
        out += 1
        i += 1
    return out


def truncate(text, limit):
    if limit <= 0 or visible_len(text) <= limit:
        return text
    out, shown, i = [], 0, 0
    while i < len(text) and shown < limit - 1:
        if text[i] == "\033":
            start = i
            while i < len(text) and text[i] not in "m":
                i += 1
            i += 1
            out.append(text[start:i])
            continue
        out.append(text[i])
        shown += 1
        i += 1
    return "".join(out) + f"{RESET}…"


def row(task, columns):
    status = str(task.get("status") or "").lower()
    glyph, color = STATUS_GLYPH.get(status, ("•", 244))

    name = task.get("label") or task.get("name") or task.get("type") or "agent"
    parts = [f"{fg(color)}{glyph}{RESET} {name}"]

    model = task.get("model") or ""
    if model:
        # Resolved model ids are long; the family is the useful half.
        short = model.replace("claude-", "").split("-")[0]
        effort = task.get("effort")
        parts.append(dim(f"{short}·{effort}" if effort else short))

    tokens = task.get("tokenCount")
    if tokens:
        window = task.get("contextWindowSize")
        text = f"{tokens // 1000}k"
        if window:
            text += f" {tokens * 100 // window}%"
        parts.append(dim(text))

    age = elapsed(task.get("startTime"))
    if age:
        parts.append(dim(age))

    desc = task.get("description")
    if desc:
        parts.append(dim(desc.replace("\n", " ")))

    return truncate(f" {dim('·')} ".join(parts), columns)


def main():
    try:
        d = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return
    if not isinstance(d, dict):
        return
    columns = d.get("columns") or 0
    for task in d.get("tasks") or []:
        if isinstance(task, dict):
            print(row(task, columns))


if __name__ == "__main__":
    main()
