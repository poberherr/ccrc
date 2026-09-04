#!/bin/bash
# The plugin's install path is hashed and changes on update, so give
# ~/.claude/settings.json a stable target to point at.
ln -sfn "${CLAUDE_PLUGIN_ROOT}/scripts/powerline-statusline.sh" "$HOME/.claude/ccrc-statusline.sh"
ln -sfn "${CLAUDE_PLUGIN_ROOT}/scripts/subagent-statusline.sh" "$HOME/.claude/ccrc-subagent-statusline.sh"
