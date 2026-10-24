#!/usr/bin/env bash
# Validates bonus B1-B4 after a deploy with the "ai" profile: calls AI-Mode,
# MCP, RAG and the Multi-Agent workflow through the backend/API and writes a
# pass/fail log with the responses for the report.
#
# Usage: ./deploy/ai-mode-check.sh [host]   (default 20.213.19.132)
# Optional: LOG_FILE, GOAL_ID (savings goal used for MCP, default 1)
set -uo pipefail

HOST="${1:-20.213.19.132}"
LOG_FILE="${LOG_FILE:-ai-services/logs/cloud_ai_mode_check.log}"
GOAL_ID="${GOAL_ID:-1}"

passed=0
failed=0
body=""
mkdir -p "$(dirname "$LOG_FILE")"
exec > >(tee "$LOG_FILE") 2>&1

# Local CPU inference is slow, so each call gets up to 15 minutes.
call() {
  local name="$1" method="$2" url="$3" data="${4:-}"
  local out code start seconds
  out=$(mktemp)
  start=$(date +%s)
  if [ -n "$data" ]; then
    code=$(curl -s -o "$out" -w "%{http_code}" --max-time 900 -X "$method" \
      -H "Content-Type: application/json" -d "$data" "$url")
  else
    code=$(curl -s -o "$out" -w "%{http_code}" --max-time 900 -X "$method" "$url")
  fi
  seconds=$(( $(date +%s) - start ))
  body=$(cat "$out")
  rm -f "$out"
  if [ "$code" = "200" ]; then
    echo "[PASS] $name: $method $url -> $code (${seconds}s)"
    passed=$((passed + 1))
  else
    echo "[FAIL] $name: $method $url -> ${code:-no response} (${seconds}s)"
    failed=$((failed + 1))
  fi
  echo "       ${body:0:1500}"
}

json_field() {
  python3 -c "import json, sys; print(json.loads(sys.argv[1]).get(sys.argv[2], ''))" "$body" "$1" 2> /dev/null
}

echo "Cloud AI services check for $HOST at $(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo
echo "== B1 AI-Mode"
call "Savings goals AI-Mode (Grace)" POST "http://$HOST:5003/ai-insights" \
  '{"input": "How am I tracking on my savings goals?"}'
call "Income and expense AI-Mode (Kevin)" GET "http://$HOST:5001/ai-insights"
call "Bills AI-Mode (Luke)" POST "http://$HOST:5004/ai-insights" \
  '{"input": "Which bills should I pay first?"}'

echo
echo "== B2 MCP tool interaction"
call "Savings MCP progress tool (Grace)" POST "http://$HOST:5003/goals/$GOAL_ID/mcp-summary"

echo
echo "== B3 RAG grounded response"
call "Savings RAG query (Grace)" POST "http://$HOST:5003/rag-query" \
  '{"query": "How should I prioritise my savings goals?", "feature": "savings"}'
rag_status=$(json_field status)
if [ "$rag_status" = "answered" ]; then
  echo "[PASS] RAG answer is grounded in retrieved context: status=answered"
  passed=$((passed + 1))
else
  echo "[FAIL] RAG answer is grounded in retrieved context: status=${rag_status:-missing}"
  failed=$((failed + 1))
fi

echo
echo "== B4 Multi-Agent Planner -> Worker -> Reviewer -> Human Review"
call "Savings Multi-Agent review (Grace)" POST "http://$HOST:5003/multi-agent-review" \
  '{"task": "Review my savings goals and recommend next steps."}'
workflow_id=$(json_field workflow_id)
workflow_status=$(json_field status)
if [ "$workflow_status" = "AWAITING_HUMAN_REVIEW" ] && [ -n "$workflow_id" ]; then
  echo "[PASS] Planner, Worker and Reviewer completed: workflow $workflow_id is AWAITING_HUMAN_REVIEW"
  passed=$((passed + 1))
  call "Human review approves workflow" POST \
    "http://$HOST:5003/multi-agent/$workflow_id/human-review" '{"decision": "approve"}'
  call "Multi-Agent workflow history" GET "http://$HOST:5003/multi-agent-history"
else
  echo "[FAIL] Planner, Worker and Reviewer completed: status=${workflow_status:-missing}"
  failed=$((failed + 1))
fi

echo
total=$((passed + failed))
if [ "$failed" -eq 0 ]; then
  echo "RESULT: PASS ($passed/$total checks)"
else
  echo "RESULT: FAIL ($passed/$total checks passed)"
fi
echo "Log written to $LOG_FILE"
[ "$failed" -eq 0 ]
