#!/usr/bin/env bash
# Waits for each student CI workflow to finish on the given commit and fails
# unless all of them succeed. Used by cloud-deployment.yml to gate deployment.
#
# Required: GH_TOKEN, COMMIT_SHA
# Optional: REQUIRED_WORKFLOWS (comma separated), TIMEOUT_SECONDS (default 1800)
set -euo pipefail

: "${COMMIT_SHA:?Set COMMIT_SHA to the commit being deployed}"
REQUIRED_WORKFLOWS="${REQUIRED_WORKFLOWS:-Grace CI,Kevin CI,Bills-Working}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-1800}"

IFS=',' read -ra workflows <<< "$REQUIRED_WORKFLOWS"
deadline=$(( $(date +%s) + TIMEOUT_SECONDS ))

for workflow in "${workflows[@]}"; do
  echo "Waiting for '$workflow' on $COMMIT_SHA"
  while true; do
    run=$(gh run list --workflow "$workflow" --commit "$COMMIT_SHA" --limit 1 \
      --json status,conclusion,url --jq '.[0] // empty')
    status=$(jq -r '.status // empty' <<< "$run")
    conclusion=$(jq -r '.conclusion // empty' <<< "$run")

    if [ "$status" = "completed" ]; then
      if [ "$conclusion" = "success" ]; then
        echo "PASS $workflow ($(jq -r '.url' <<< "$run"))"
        break
      fi
      echo "FAIL $workflow finished with '$conclusion' ($(jq -r '.url' <<< "$run"))"
      exit 1
    fi

    if [ "$(date +%s)" -ge "$deadline" ]; then
      echo "FAIL timed out waiting for $workflow (status: ${status:-not started})"
      exit 1
    fi
    sleep 20
  done
done
echo "All required CI workflows passed"
