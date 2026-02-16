#!/bin/bash
# ProjectForge VM Setup Script
# Instala todas las dependencias necesarias para ejecutar el proyecto

set -e

echo "🚀 ProjectForge VM Setup"
echo "======================="

# Update system
echo "📦 Updating system packages..."
sudo apt-get update -qq

# Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker installed"
else
    echo "✅ Docker already installed"
fi

# Install Docker Compose
echo "📦 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose installed"
else
    echo "✅ Docker Compose already installed"
fi

# Install Node.js 20
echo "📗 Installing Node.js 20..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
    echo "✅ Node.js installed"
else
    echo "✅ Node.js already installed"
fi

# Install pnpm
echo "📦 Installing pnpm..."
if ! command -v pnpm &> /dev/null; then
    curl -fsSL https://get.pnpm.io/install.sh | sh -
    export PNPM_HOME="$HOME/.local/share/pnpm"
    export PATH="$PNPM_HOME:$PATH"
    echo "✅ pnpm installed"
else
    echo "✅ pnpm already installed"
fi

# Install Go 1.22
echo "🐹 Installing Go 1.22..."
if ! command -v go &> /dev/null; then
    wget https://go.dev/dl/go1.22.0.linux-amd64.tar.gz
    sudo rm -rf /usr/local/go
    sudo tar -C /usr/local -xzf go1.22.0.linux-amd64.tar.gz
    rm go1.22.0.linux-amd64.tar.gz
    echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
    export PATH=$PATH:/usr/local/go/bin
    echo "✅ Go installed"
else
    echo "✅ Go already installed"
fi

# Install Poetry
echo "📚 Installing Poetry..."
if ! command -v poetry &> /dev/null; then
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
    echo "✅ Poetry installed"
else
    echo "✅ Poetry already installed"
fi

# Install PostgreSQL client
echo "🐘 Installing PostgreSQL client..."
sudo apt-get install -y postgresql-client

echo ""
echo "✅ Setup complete!"
echo ""
echo "⚠️  IMPORTANTE: Por favor ejecuta esto para aplicar los cambios:"
echo "   source ~/.bashrc"
echo "   newgrp docker"
echo ""
echo "Luego ejecuta: ./start-dev.sh"
