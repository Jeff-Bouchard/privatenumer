#!/bin/bash
# ENUM Backend Setup Script for Raspberry Pi
# Run as root or with sudo

set -e

echo "=== ENUM Backend Setup for Antisip with Emercoin NVS ==="

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/home/pi/enum-server"
SERVICE_FILE="/etc/systemd/system/enum-backend.service"
NGINX_CONF="/etc/nginx/sites-available/enum-backend"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root (use sudo)${NC}" 
   exit 1
fi

# Check if Emercoin is installed
echo -e "${YELLOW}[1/8] Checking Emercoin installation...${NC}"
if command -v emercoin-cli &> /dev/null; then
    EMC_CLI=$(which emercoin-cli)
    echo -e "${GREEN}✓ Emercoin CLI found at: $EMC_CLI${NC}"
    
    # Test connection
    if sudo -u pi $EMC_CLI getinfo &> /dev/null; then
        echo -e "${GREEN}✓ Emercoin node is running and responding${NC}"
    else
        echo -e "${YELLOW}⚠ Emercoin node is not responding. Ensure emercoind is running.${NC}"
    fi
else
    echo -e "${RED}✗ emercoin-cli not found. Please install Emercoin first.${NC}"
    exit 1
fi

# Update system
echo -e "${YELLOW}[2/8] Updating system packages...${NC}"
apt update
apt upgrade -y

# Install dependencies
echo -e "${YELLOW}[3/8] Installing dependencies...${NC}"
apt install -y python3 python3-pip python3-venv nginx git

# Create installation directory
echo -e "${YELLOW}[4/8] Creating installation directory...${NC}"
mkdir -p $INSTALL_DIR
mkdir -p $INSTALL_DIR/logs
chown -R pi:pi $INSTALL_DIR

# Copy files
echo -e "${YELLOW}[5/8] Copying application files...${NC}"
cp enum_backend.py $INSTALL_DIR/
cp requirements.txt $INSTALL_DIR/
chown -R pi:pi $INSTALL_DIR

# Install Python dependencies
echo -e "${YELLOW}[6/8] Installing Python dependencies...${NC}"
sudo -u pi pip3 install --user -r $INSTALL_DIR/requirements.txt

# Install systemd service
echo -e "${YELLOW}[7/8] Installing systemd service...${NC}"
cp systemd/enum-backend.service $SERVICE_FILE

# Update service file with actual paths
sed -i "s|/home/pi/enum-server|$INSTALL_DIR|g" $SERVICE_FILE
sed -i "s|/usr/local/bin/emercoin-cli|$EMC_CLI|g" $SERVICE_FILE

systemctl daemon-reload
systemctl enable enum-backend.service

# Configure firewall
echo -e "${YELLOW}[8/8] Configuring firewall...${NC}"
if command -v ufw &> /dev/null; then
    ufw allow 8080/tcp comment 'ENUM Backend'
    ufw allow 80/tcp comment 'HTTP'
    ufw allow 443/tcp comment 'HTTPS'
    echo -e "${GREEN}✓ Firewall rules added${NC}"
fi

# Start service
echo -e "${YELLOW}Starting ENUM backend service...${NC}"
systemctl start enum-backend.service

# Check status
sleep 2
if systemctl is-active --quiet enum-backend.service; then
    echo -e "${GREEN}✓ ENUM backend service is running${NC}"
    
    # Test endpoint
    if curl -s http://localhost:8080/health > /dev/null; then
        echo -e "${GREEN}✓ Health check endpoint responding${NC}"
    else
        echo -e "${YELLOW}⚠ Service running but health check failed${NC}"
    fi
else
    echo -e "${RED}✗ Failed to start service. Check logs with: journalctl -u enum-backend -n 50${NC}"
    exit 1
fi

# Display connection info
IP_ADDRESS=$(hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo ""
echo "ENUM Backend is now running on port 8080"
echo ""
echo "Configuration for Antisip:"
echo "  ENUM Server URL: http://$IP_ADDRESS:8080/enum/lookup?number="
echo ""
echo "API Endpoints:"
echo "  Health Check:  http://$IP_ADDRESS:8080/health"
echo "  ENUM Lookup:   http://$IP_ADDRESS:8080/enum/lookup?number=+1234567890"
echo "  Register ENUM: http://$IP_ADDRESS:8080/enum/register (POST)"
echo "  List All:      http://$IP_ADDRESS:8080/enum/list"
echo ""
echo "Service Management:"
echo "  Status:  systemctl status enum-backend"
echo "  Stop:    systemctl stop enum-backend"
echo "  Start:   systemctl start enum-backend"
echo "  Restart: systemctl restart enum-backend"
echo "  Logs:    journalctl -u enum-backend -f"
echo ""
echo "Next Steps:"
echo "  1. Register ENUM records using the /enum/register endpoint"
echo "  2. Configure Antisip with the ENUM server URL"
echo "  3. (Optional) Set up NGINX reverse proxy for HTTPS"
echo ""
