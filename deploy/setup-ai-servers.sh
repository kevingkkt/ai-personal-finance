#!/usr/bin/env bash
# Runs on the Azure VM from the repository root (called by azure-deploy.sh for
# the "ai" profile, after setup-ollama.sh). Runs the shared MCP (7001), RAG
# (7002) and Multi-Agent (7003) servers as native, non-containerised systemd
# services. Safe to run again: it refreshes the code and restarts them.
#
# Optional: RAG_MODEL (default qwen2.5:0.5b), MULTI_AGENT_MODEL (default
#           qwen2.5:1.5b; the local default llama3.1:8b is too slow on a 2 vCPU VM)
set -euo pipefail

RUNTIME_DIR="$HOME/ai-services-runtime"
RAG_MODEL="${RAG_MODEL:-qwen2.5:0.5b}"
MULTI_AGENT_MODEL="${MULTI_AGENT_MODEL:-qwen2.5:1.5b}"

if ! python3 -c "import ensurepip" 2> /dev/null; then
  echo "Installing python3-venv"
  sudo apt-get update -qq
  sudo apt-get install -y -qq python3-venv
fi

# Run from a copy outside the repository: the Multi-Agent server writes its
# audit log next to its code, which would otherwise block git pull on deploys.
mkdir -p "$RUNTIME_DIR"
cp ai-services/*.py ai-services/requirements.txt "$RUNTIME_DIR/"
rm -rf "$RUNTIME_DIR/knowledge"
cp -r ai-services/knowledge "$RUNTIME_DIR/knowledge"

[ -d "$RUNTIME_DIR/.venv" ] || python3 -m venv "$RUNTIME_DIR/.venv"
"$RUNTIME_DIR/.venv/bin/pip" install -q --upgrade pip
"$RUNTIME_DIR/.venv/bin/pip" install -q -r "$RUNTIME_DIR/requirements.txt"

ollama pull "$RAG_MODEL"
ollama pull "$MULTI_AGENT_MODEL"

write_service() {
  local name="$1" script="$2"
  sudo tee "/etc/systemd/system/$name.service" > /dev/null <<EOF
[Unit]
Description=AI Personal Finance $name
After=network-online.target ollama.service

[Service]
User=$USER
WorkingDirectory=$RUNTIME_DIR
Environment=OLLAMA_URL=http://localhost:11434/api/generate
Environment=RAG_MODEL=$RAG_MODEL
Environment=MULTI_AGENT_MODEL=$MULTI_AGENT_MODEL
Environment=BILLS_API_URL=http://localhost:5004
ExecStart=$RUNTIME_DIR/.venv/bin/python $script
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
}

write_service ai-mcp mcp_server.py
write_service ai-rag rag_server.py
write_service ai-multi-agent multi_agent_server.py
sudo systemctl daemon-reload
for service in ai-mcp ai-rag ai-multi-agent; do
  sudo systemctl enable "$service"
  sudo systemctl restart "$service"
done

wait_for() {
  local name="$1" url="$2"
  for _ in $(seq 1 30); do
    # Any HTTP response means the server is listening (MCP has no /health).
    if [ "$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "$url")" != "000" ]; then
      echo "PASS $name is listening ($url)"
      return 0
    fi
    sleep 2
  done
  echo "FAIL $name did not start"
  sudo journalctl -u "$3" --no-pager -n 30
  return 1
}

wait_for MCP http://localhost:7001/mcp ai-mcp
wait_for RAG http://localhost:7002/health ai-rag
wait_for Multi-Agent http://localhost:7003/health ai-multi-agent
echo "AI servers ready (RAG: $RAG_MODEL, Multi-Agent: $MULTI_AGENT_MODEL)"
