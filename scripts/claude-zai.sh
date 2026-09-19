#!/bin/bash
# claude CLI pointed at z.ai's Anthropic-compatible endpoint (GLM coding plan).
export ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"
export ANTHROPIC_AUTH_TOKEN="$(cat ~/.config/ringer/zai-token)"   # 0600 perms
# silence warnings that don't apply to a third-party endpoint
export CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT=1     # unknown-model catalog notice
export ENABLE_CLAUDEAI_MCP_SERVERS=0                              # claude.ai connectors notice
for a in "$@"; do
  [[ "$a" == "--model" || "$a" == --model=* ]] && model_set=1
done
if [[ -n "$model_set" ]]; then
  exec claude "$@"
else
  exec claude --model glm-5.3 "$@"
fi
