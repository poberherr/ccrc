# ccrc — Claude Code Runtime Configuration

Opinionated Claude Code plugin. Powerline statusline with caveman badge, model, git, and token usage.

<!-- screenshot here: drop a screenshot of the statusline in your terminal -->

## What you get

- **CAVEMAN badge** — shown when [caveman plugin](https://github.com/JuliusBrussee/caveman) is active (detects `~/.claude/.caveman-active`)
- **Model** — current Claude model name
- **cwd** — working dir (auto-shortened when long)
- **Git** — branch + worktree marker when inside a linked worktree
- **Tokens** — total context usage as `{k}k {pct}%` (assumes 200k window)

## Requirements

- Terminal with a **Nerd Font** (for powerline glyphs)
- `python3` on `PATH` (used to parse session JSON)

## Install

```
/plugin marketplace add poberherr/ccrc
/plugin install ccrc@ccrc
```

Statusline registers automatically via `plugin.json`. No `settings.json` edit needed.

## Customize

Edit the script directly after install:

```
~/.claude/plugins/cache/ccrc-ccrc/*/scripts/powerline-statusline.sh
```

Knobs at the top of the script:

- `C_*_BG` / `C_*_FG` — 256-color palette per segment
- `SEP`, `BRANCH`, `TREE` — Nerd Font glyphs
- Path-shortening threshold (default 30 chars)

Or fork the repo and point the marketplace at your fork.

## Caveman integration

When the caveman plugin flips `~/.claude/.caveman-active`, this bar prepends an orange `CAVEMAN` or `CAVEMAN:ULTRA` badge. No coupling — if caveman isn't installed, the segment is just omitted.

## License

MIT — see [LICENSE](LICENSE).
