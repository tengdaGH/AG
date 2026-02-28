#!/bin/bash
set -e

echo "🚀 Starting TOEFL 2026 Deployment..."

# 1. Install Docker & Git if missing
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker and Docker Compose..."
    sudo apt-get update
    sudo apt-get install -y docker.io git curl
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.29.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# 2. Clone or pull repository
if [ ! -d "AG" ]; then
    echo "⬇️ Cloning codebase..."
    git clone https://github.com/tengdaGH/AG.git
else
    echo "🔄 Updating codebase..."
    cd AG
    git pull origin main
    cd ..
fi

# 3. Enter the project folder
cd AG/toefl-2026

# Detect the server's public IP dynamically
export SERVER_IP=$(curl -s http://icanhazip.com)
echo "🌍 Server IP detected as: $SERVER_IP"

# 4. Build and start via Docker Compose
echo "🐳 Building and starting containers... (This may take a few minutes for the first run)"
sudo -E /usr/local/bin/docker-compose up -d --build

echo "==============================================="
echo "✅ DEPLOYMENT SUCCESSFUL!"
echo "🟢 Your TOEFL 2026 Platform is now LIVE at:"
echo "👉 http://$SERVER_IP:3000/login"
echo "==============================================="
