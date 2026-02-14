#!/usr/bin/env bash
set -euo pipefail

CFG="${1:-.hf-tui/smoke-config.json}"
LOG="${2:-.hf-tui/smoke-tmux.log}"
mkdir -p "$(dirname "$CFG")"
cat > "$CFG" <<JSON
{
  "cache_dir": ".hf-tui/smoke-cache",
  "active_model": "mock",
  "temperature": 0.0,
  "max_new_tokens": 8,
  "thinking": false,
  "checkpoints": []
}
JSON

SESSION="hf_tui_smoke"
tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" "PYTHONPATH=src python -m hf_tui.cli --config $CFG"
sleep 1
# type model + load
 tmux send-keys -t "$SESSION" "mock" Enter
sleep 1
# jump to prompt input and send one message (layout dependent but exercises interactive loop)
tmux send-keys -t "$SESSION" "hi from tmux" Enter
sleep 1
# open and close model modal
tmux send-keys -t "$SESSION" "m"
sleep 1
tmux send-keys -t "$SESSION" Escape
sleep 1
# quit app
tmux send-keys -t "$SESSION" C-c
sleep 1

tmux capture-pane -pt "$SESSION" > "$LOG" || true
tmux kill-session -t "$SESSION" 2>/dev/null || true
echo "tmux smoke log: $LOG"
