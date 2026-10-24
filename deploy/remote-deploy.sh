#!/usr/bin/env bash
# Runs on the Azure VM from the repository root (called by azure-deploy.sh).
# Rebuilds the containers with the cloud profile (AI services disabled) and
# fails the deployment if any frontend or backend does not respond.
set -euo pipefail

ENV_FILE="${ENV_FILE:-.env.cloud}"

docker compose --env-file "$ENV_FILE" up -d --build
docker compose ps

urls=(
  "http://localhost:8080/"          # front page
  "http://localhost:3001/"          # Kevin frontend
  "http://localhost:5001/health"    # Kevin backend
  "http://localhost:3002/"          # Budget manager frontend
  "http://localhost:5002/health"    # Budget manager backend
  "http://localhost:3003/"          # Grace frontend
  "http://localhost:5003/health"    # Grace backend
  "http://localhost:3004/"          # Bills frontend
  "http://localhost:5004/health"    # Bills backend
)

failed=0
for url in "${urls[@]}"; do
  code=""
  for _ in $(seq 1 20); do
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" || true)
    [ "$code" = "200" ] && break
    sleep 3
  done
  if [ "$code" = "200" ]; then
    echo "PASS $url -> $code"
  else
    echo "FAIL $url -> ${code:-no response}"
    failed=1
  fi
done

if [ "$failed" -ne 0 ]; then
  docker compose logs --no-color --tail 50
  echo "Deployment health check failed"
  exit 1
fi
echo "Deployment health check passed"
