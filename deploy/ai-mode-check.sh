#!/usr/bin/env bash
# Validates bonus B1-B4 after a deploy with the "ai" profile: calls AI-Mode,
# MCP, RAG and the Multi-Agent workflow through each feature's backend/API
# (Grace savings, Kevin income/expense, Luke bills) and writes a pass/fail log
# with the responses for the report.
#
# Usage: ./deploy/ai-mode-check.sh [host]   (default 20.213.19.132)
# Optional: LOG_FILE, GOAL_ID (savings goal used for MCP, default 1)
set -uo pipefail

HOST="${1:-20.213.19.132}"
LOG_FILE="${LOG_FILE:-ai-services/logs/cloud_ai_mode_check.log}"
GOAL_ID="${GOAL_ID:-1}"
GRACE="http://$HOST:5003"
KEVIN="http://$HOST:5001"
LUKE="http://$HOST:5004"

passed=0
failed=0
body=""
mkdir -p "$(dirname "$LOG_FILE")"
exec > >(tee "$LOG_FILE") 2>&1

result() {
  if [ "$2" = "true" ]; then
    echo "[PASS] $1"
    passed=$((passed + 1))
  else
    echo "[FAIL] $1"
    failed=$((failed + 1))
  fi
}

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
  [ "$code" = "200" ] && ok=true || ok=false
  result "$name: $method $url -> ${code:-no response} (${seconds}s)" "$ok"
  echo "       ${body:0:1200}"
}

json_field() {
  python3 -c "import json, sys; print(json.loads(sys.argv[1]).get(sys.argv[2], ''))" "$body" "$1" 2> /dev/null
}

rag_check() {
  local name="$1" url="$2" data="$3"
  call "$name RAG query" POST "$url" "$data"
  local status
  status=$(json_field status)
  [ "$status" = "answered" ] && ok=true || ok=false
  result "$name RAG answer is grounded in retrieved context: status=${status:-missing}" "$ok"
}

# Runs Planner -> Worker -> Reviewer, then approves it as the human reviewer.
multi_agent_check() {
  local name="$1" base="$2" data="$3"
  call "$name Multi-Agent review" POST "$base/multi-agent-review" "$data"
  local workflow_id status
  workflow_id=$(json_field workflow_id)
  status=$(json_field status)
  if [ "$status" = "AWAITING_HUMAN_REVIEW" ] && [ -n "$workflow_id" ]; then
    result "$name Planner, Worker and Reviewer completed: workflow $workflow_id is AWAITING_HUMAN_REVIEW" true
    call "$name Human Review approves workflow" POST \
      "$base/multi-agent/$workflow_id/human-review" '{"decision": "approve"}'
  else
    result "$name Planner, Worker and Reviewer completed: status=${status:-missing}" false
  fi
}

# Kevin's and Luke's frontends send their own records as Multi-Agent evidence.
evidence_task() {
  local task="$1" key="$2" url="$3"
  curl -s --max-time 30 "$url" | python3 -c '
import json, sys
records = json.load(sys.stdin)
print(json.dumps({"task": sys.argv[1], "evidence": {sys.argv[2]: records}}))
' "$task" "$key"
}

echo "Cloud AI services check for $HOST at $(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo
echo "== B1 AI-Mode"
call "Savings (Grace) AI-Mode" POST "$GRACE/ai-insights" \
  '{"input": "How am I tracking on my savings goals?"}'
call "Income and expense (Kevin) AI-Mode" GET "$KEVIN/ai-insights"
call "Bills (Luke) AI-Mode" POST "$LUKE/ai-insights" \
  '{"input": "Which bills should I pay first?"}'

echo
echo "== B2 MCP tool interaction"
call "Savings (Grace) MCP goal progress tool" POST "$GRACE/goals/$GOAL_ID/mcp-summary"
call "Income and expense (Kevin) MCP summary tool" GET "$KEVIN/mcp-income-expense-summary"
call "Bills (Luke) MCP total unpaid tool" GET "$LUKE/mcp/total-unpaid"

echo
echo "== B3 RAG grounded response"
rag_check "Savings (Grace)" "$GRACE/rag-query" \
  '{"query": "How should I prioritise my savings goals?", "feature": "savings"}'
rag_check "Income and expense (Kevin)" "$KEVIN/rag-query" \
  '{"query": "How are income and expenses tracked?", "feature": "income_expense"}'
rag_check "Bills (Luke)" "$LUKE/rag-query" \
  '{"query": "How do I mark a bill as paid?", "feature": "bills"}'

echo
echo "== B4 Multi-Agent Planner -> Worker -> Reviewer -> Human Review"
multi_agent_check "Savings (Grace)" "$GRACE" \
  '{"task": "Review my savings goals and recommend next steps."}'
multi_agent_check "Income and expense (Kevin)" "$KEVIN" \
  "$(evidence_task "Review my income and expenses and recommend next steps." transactions "$KEVIN/transactions")"
multi_agent_check "Bills (Luke)" "$LUKE" \
  "$(evidence_task "Review my bills and recommend which to pay first." bills "$LUKE/bills")"
call "Savings (Grace) Multi-Agent workflow history" GET "$GRACE/multi-agent-history"

echo
total=$((passed + failed))
if [ "$failed" -eq 0 ]; then
  echo "RESULT: PASS ($passed/$total checks)"
else
  echo "RESULT: FAIL ($passed/$total checks passed)"
fi
echo "Log written to $LOG_FILE"
[ "$failed" -eq 0 ]
