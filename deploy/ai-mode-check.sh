#!/usr/bin/env bash
# Validates bonus B1 (cloud AI-Mode) after a deploy with the "ai" profile:
# calls each feature's AI-Mode endpoint through the backend/API and writes a
# pass/fail log with the model's replies for the report.
#
# Usage: ./deploy/ai-mode-check.sh [host]   (default 20.213.19.132)
# Optional: LOG_FILE
set -uo pipefail

HOST="${1:-20.213.19.132}"
LOG_FILE="${LOG_FILE:-ai-services/logs/cloud_ai_mode_check.log}"

passed=0
failed=0
mkdir -p "$(dirname "$LOG_FILE")"
exec > >(tee "$LOG_FILE") 2>&1

# Local CPU inference is slow, so each call gets up to 10 minutes.
call() {
  local name="$1" method="$2" url="$3" body="${4:-}"
  local out code start seconds
  out=$(mktemp)
  start=$(date +%s)
  if [ -n "$body" ]; then
    code=$(curl -s -o "$out" -w "%{http_code}" --max-time 600 -X "$method" \
      -H "Content-Type: application/json" -d "$body" "$url")
  else
    code=$(curl -s -o "$out" -w "%{http_code}" --max-time 600 -X "$method" "$url")
  fi
  seconds=$(( $(date +%s) - start ))
  if [ "$code" = "200" ]; then
    echo "[PASS] $name: $method $url -> $code (${seconds}s)"
    passed=$((passed + 1))
  else
    echo "[FAIL] $name: $method $url -> ${code:-no response} (${seconds}s)"
    failed=$((failed + 1))
  fi
  echo "       $(head -c 1500 "$out")"
  rm -f "$out"
}

echo "Cloud AI-Mode check for $HOST at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo
call "Savings goals AI-Mode (Grace)" POST "http://$HOST:5003/ai-insights" \
  '{"input": "How am I tracking on my savings goals?"}'
call "Income and expense AI-Mode (Kevin)" GET "http://$HOST:5001/ai-insights"
call "Bills AI-Mode (Luke)" POST "http://$HOST:5004/ai-insights" \
  '{"input": "Which bills should I pay first?"}'

echo
total=$((passed + failed))
if [ "$failed" -eq 0 ]; then
  echo "RESULT: PASS ($passed/$total AI-Mode calls)"
else
  echo "RESULT: FAIL ($passed/$total AI-Mode calls passed)"
fi
echo "Log written to $LOG_FILE"
[ "$failed" -eq 0 ]
