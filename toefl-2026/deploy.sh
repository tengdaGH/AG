#!/bin/bash

# Configuration
USER="root"
HOST="101.32.187.39"
PROJECT_DIR="/root/AG" # Top-level repo directory
REMOTE_SSH="ssh -o StrictHostKeyChecking=no $USER@$HOST"

echo "========================================="
echo "  Deploying to Tencent Cloud ($HOST)...  "
echo "========================================="

# 1. Ensure local changes are pushed
echo "[1/3] Checking Git status..."
git fetch
if [ $(git rev-list HEAD...origin/main --count) -gt 0 ]; then
    echo "⚠️  You have unpushed commits! Please run 'git push' first."
    exit 1
fi
echo "✅ Local branch is up-to-date with remote."

# 2. Trigger pull and restart remotely
echo "[2/3] Processing update on remote server..."
$REMOTE_SSH << 'EOF'
    set -e
    cd /root/AG/
    echo "--> Pulling latest changes from GitHub..."
    git pull origin main
    
    cd toefl-2026/
    echo "--> Restarting Docker containers..."
    docker-compose down
    docker-compose up -d --build
    
    echo "--> Cleanup unused images..."
    docker image prune -f
    
    echo "✅ Services restarted successfully!"
EOF

echo "[3/3] Deployment complete! 🎉"
echo "========================================="
