#!/usr/bin/env bash
# Deploy the integrated application to the Azure VM over SSH.
# Used by .github/workflows/cloud-deployment.yml and can be run from a terminal.
#
# Required: VM_HOST, VM_USER
# Optional: SSH_KEY (default ~/.ssh/azure_vm_key), DEPLOY_BRANCH (default kevin-release2),
#           APP_DIR (default ~/ai-personal-finance on the VM)
#
# Example: VM_HOST=20.213.19.132 VM_USER=azureuser ./deploy/azure-deploy.sh
set -euo pipefail

: "${VM_HOST:?Set VM_HOST to the Azure VM public IP or DNS name}"
: "${VM_USER:?Set VM_USER to the Azure VM admin user}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/azure_vm_key}"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-kevin-release2}"
APP_DIR="${APP_DIR:-~/ai-personal-finance}"

echo "Deploying branch $DEPLOY_BRANCH to $VM_USER@$VM_HOST:$APP_DIR"

# Pull the branch first so the VM always runs the latest remote-deploy.sh.
ssh -i "$SSH_KEY" -o BatchMode=yes "$VM_USER@$VM_HOST" \
  "set -e
   cd $APP_DIR
   git fetch origin
   git switch $DEPLOY_BRANCH
   git pull --ff-only origin $DEPLOY_BRANCH
   bash deploy/remote-deploy.sh"
