#!/usr/bin/env bash
# Validates the cloud endpoint and data security controls (bonus B5/B6)
# against a deployed host and writes a pass/fail log for the report.
#
# Usage: ./deploy/security-check.sh [host]   (default 20.213.19.132)
# Optional: ALLOWED_ORIGIN (default http://<host>:3003), LOG_FILE
set -uo pipefail

HOST="${1:-20.213.19.132}"
ALLOWED_ORIGIN="${ALLOWED_ORIGIN:-http://$HOST:3003}"
BAD_ORIGIN="https://evil.example"
LOG_FILE="${LOG_FILE:-ai-services/logs/cloud_security_check.log}"

frontends=(8080 3001 3003 3004)
backends=(5001 5003 5004)
databases=(6001 6003 6004)

passed=0
failed=0
mkdir -p "$(dirname "$LOG_FILE")"
exec > >(tee "$LOG_FILE") 2>&1

check() {
  local name="$1" ok="$2" detail="$3"
  if [ "$ok" = "true" ]; then
    echo "[PASS] $name: $detail"
    passed=$((passed + 1))
  else
    echo "[FAIL] $name: $detail"
    failed=$((failed + 1))
  fi
}

header() {
  curl -s -D - -o /dev/null --max-time 5 "${@:2}" "$1" | tr -d '\r'
}

echo "Cloud security check for $HOST at $(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo
echo "== B6 Data security: databases not reachable from the internet"
for port in "${databases[@]}"; do
  if nc -z -w 3 "$HOST" "$port" 2>/dev/null; then
    check "Database port $port closed" false "port is reachable"
  else
    check "Database port $port closed" true "connection refused or filtered"
  fi
done

echo
echo "== B5 Endpoint security: API only accepts the app's own frontends"
for port in "${backends[@]}"; do
  bad=$(header "http://$HOST:$port/health" -H "Origin: $BAD_ORIGIN" | grep -i '^access-control-allow-origin:' || true)
  if [ -z "$bad" ]; then
    check "Port $port rejects $BAD_ORIGIN" true "no Access-Control-Allow-Origin header"
  else
    check "Port $port rejects $BAD_ORIGIN" false "$bad"
  fi
  good=$(header "http://$HOST:$port/health" -H "Origin: $ALLOWED_ORIGIN" | grep -i '^access-control-allow-origin:' || true)
  if [ -n "$good" ]; then
    check "Port $port allows $ALLOWED_ORIGIN" true "$good"
  else
    check "Port $port allows $ALLOWED_ORIGIN" false "no Access-Control-Allow-Origin header"
  fi
done

echo
echo "== B5 Endpoint security: no debug pages on errors"
for port in "${backends[@]}"; do
  body=$(curl -s --max-time 5 "http://$HOST:$port/no-such-route-security-check")
  if grep -qi 'traceback\|werkzeug debugger' <<< "$body"; then
    check "Port $port hides debug output" false "debug page returned"
  else
    check "Port $port hides debug output" true "plain error response"
  fi
done

echo
echo "== B5 Endpoint security: rate limiting"
limited=false
for _ in $(seq 1 400); do
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://$HOST:5003/health")
  if [ "$code" = "429" ]; then
    limited=true
    break
  fi
done
check "Port 5003 rate limits a burst of requests" "$limited" "expected 429 within 400 requests"

echo
echo "== B5 Endpoint security: frontend security headers"
for port in "${frontends[@]}"; do
  headers=$(header "http://$HOST:$port/")
  for name in X-Content-Type-Options X-Frame-Options Referrer-Policy Content-Security-Policy; do
    if grep -qi "^$name:" <<< "$headers"; then
      check "Port $port sends $name" true "$(grep -i "^$name:" <<< "$headers")"
    else
      check "Port $port sends $name" false "header missing"
    fi
  done
  if grep -qi '^server: nginx/[0-9]' <<< "$headers"; then
    check "Port $port hides nginx version" false "$(grep -i '^server:' <<< "$headers")"
  else
    check "Port $port hides nginx version" true "no version in Server header"
  fi
done

echo
total=$((passed + failed))
if [ "$failed" -eq 0 ]; then
  echo "RESULT: PASS ($passed/$total checks)"
else
  echo "RESULT: FAIL ($passed/$total checks passed)"
fi
echo "Log written to $LOG_FILE"
[ "$failed" -eq 0 ]
