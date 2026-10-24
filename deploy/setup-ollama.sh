#!/usr/bin/env bash
# Runs on the Azure VM (called by azure-deploy.sh for the "ai" profile).
# Installs Ollama as a native, non-containerised service and pulls the model
# used by AI-Mode. Safe to run again: it skips steps that are already done.
#
# Optional: AI_MODEL (default deepseek-r1:1.5b)
set -euo pipefail

AI_MODEL="${AI_MODEL:-deepseek-r1:1.5b}"

echo "VM resources:"
nproc
free -h

if ! command -v ollama > /dev/null; then
  echo "Installing Ollama"
  curl -fsSL https://ollama.com/install.sh | sh
fi

# Listen on all interfaces so the backend containers can reach it through
# host.docker.internal. The Azure NSG (DenyAllInBound) keeps 11434 closed to
# the internet.
sudo mkdir -p /etc/systemd/system/ollama.service.d
printf '[Service]\nEnvironment="OLLAMA_HOST=0.0.0.0:11434"\n' \
  | sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl restart ollama

for _ in $(seq 1 30); do
  curl -sf http://localhost:11434/api/tags > /dev/null && break
  sleep 2
done
curl -sf http://localhost:11434/api/tags > /dev/null || { echo "Ollama did not start"; exit 1; }

ollama pull "$AI_MODEL"
ollama list
echo "Ollama ready with $AI_MODEL"
