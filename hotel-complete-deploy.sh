#!/bin/bash

# Hotel Management System - Ubuntu 25.04 Compatible Deployment Script
# This script deploys the complete hotel management application avoiding all dependency issues

set -e

echo "🏨 Deploying Complete Hotel Management System (Ubuntu 25.04 Compatible)..."
echo "=============================================================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# Get configuration
read -p "Enter your domain/IP: " DOMAIN
DOMAIN=${DOMAIN:-$(curl -s ifconfig.me 2>/dev/null || echo "localhost")}
MONGO_PASSWORD="HotelManagement2024SecurePass!"

print_info "Using domain/IP: $DOMAIN"

# Update system and fix package issues
print_status "Updating system and fixing package conflicts..."
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y
sudo apt autoclean

# Remove any existing Node.js installations
print_status "Cleaning previous Node.js installations..."
sudo apt remove --purge nodejs npm -y 2>/dev/null || true
sudo apt autoremove -y
sudo rm -rf /etc/apt/sources.list.d/nodesource* 2>/dev/null || true
sudo rm -rf /usr/share/keyrings/nodesource* 2>/dev/null || true

# Install essential packages
print_status "Installing essential packages..."
sudo apt install -y curl wget git build-essential software-properties-common apt-transport-https ca-certificates gnupg lsb-release

# Install Node.js using Snap (more reliable for Ubuntu 25.04)
print_status "Installing Node.js via Snap (Ubuntu 25.04 compatible)..."
sudo snap install node --classic

# Create symlinks for system-wide access
sudo ln -sf /snap/bin/node /usr/local/bin/node 2>/dev/null || true
sudo ln -sf /snap/bin/npm /usr/local/bin/npm 2>/dev/null || true
sudo ln -sf /snap/bin/npx /usr/local/bin/npx 2>/dev/null || true

# Verify Node.js installation
NODE_VERSION=$(node --version 2>/dev/null || echo "failed")
NPM_VERSION=$(npm --version 2>/dev/null || echo "failed")

if [[ "$NODE_VERSION" == "failed" ]]; then
    print_error "Node.js installation failed. Trying alternative method..."
    
    # Alternative: Download and install manually
    print_status "Installing Node.js manually..."
    cd /tmp
    wget https://nodejs.org/dist/v20.10.0/node-v20.10.0-linux-x64.tar.xz
    tar -xf node-v20.10.0-linux-x64.tar.xz
    sudo mv node-v20.10.0-linux-x64 /opt/nodejs
    sudo ln -sf /opt/nodejs/bin/node /usr/local/bin/node
    sudo ln -sf /opt/nodejs/bin/npm /usr/local/bin/npm
    sudo ln -sf /opt/nodejs/bin/npx /usr/local/bin/npx
    
    NODE_VERSION=$(node --version 2>/dev/null || echo "manual installation failed")
    NPM_VERSION=$(npm --version 2>/dev/null || echo "manual installation failed")
fi

print_status "Node.js version: $NODE_VERSION"
print_status "NPM version: $NPM_VERSION"

# Install Python with stable version
print_status "Setting up Python..."
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Install Docker
print_status "Installing Docker..."
sudo apt install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker

# Install PM2
print_status "Installing PM2..."
sudo npm install -g pm2 2>/dev/null || /snap/bin/npm install -g pm2 || /opt/nodejs/bin/npm install -g pm2

# Install Nginx
print_status "Installing Nginx..."
sudo apt install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Create application user
if ! id "hotelapp" &>/dev/null; then
    print_status "Creating hotelapp user..."
    sudo adduser --disabled-password --gecos "" hotelapp
    sudo usermod -aG sudo,docker hotelapp
fi

# Setup MongoDB with Docker
print_status "Setting up MongoDB with Docker..."
sudo docker stop mongodb-hotel 2>/dev/null || true
sudo docker rm mongodb-hotel 2>/dev/null || true

sudo docker run -d \
  --name mongodb-hotel \
  --restart unless-stopped \
  -p 27017:27017 \
  -v mongodb-hotel-data:/data/db \
  -e MONGO_INITDB_ROOT_USERNAME=hotelapp \
  -e MONGO_INITDB_ROOT_PASSWORD="$MONGO_PASSWORD" \
  mongo:7.0

print_info "Waiting for MongoDB to start..."
sleep 20

# Test MongoDB
if sudo docker exec mongodb-hotel mongosh -u hotelapp -p "$MONGO_PASSWORD" --authenticationDatabase admin --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
    print_status "MongoDB is running successfully"
else
    print_error "MongoDB startup failed"
    exit 1
fi

# Create application structure
print_status "Creating application structure..."
sudo rm -rf /home/hotelapp/hotel-management
sudo -u hotelapp mkdir -p /home/hotelapp/hotel-management/{backend,frontend,logs}

###########################################
# BACKEND SETUP - Complete Hotel Management System
###########################################
print_status "Setting up complete backend system..."
cd /home/hotelapp/hotel-management/backend
