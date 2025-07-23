#!/bin/bash
#############################################################
# Thermal Logger Installation Script for Raspberry Pi
# Author: [Your Name]
# Description: Sets up the thermal logging system environment
#############################################################

echo "===== Thermal Logger System Setup ====="
echo "This script will set up your Raspberry Pi for thermal logging."

# Function to check if a command succeeded
check_status() {
    if [ $? -eq 0 ]; then
        echo "✓ $1"
    else
        echo "✗ Error: $1 failed"
        exit 1
    fi
}

# 1. System Updates
echo -e "\n[1/6] Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y
check_status "System update"

# 2. Install Required System Packages
echo -e "\n[2/6] Installing required system packages..."
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    git \
    i2c-tools \
    python3-smbus
check_status "Package installation"

# 3. Enable Required Interfaces
echo -e "\n[3/6] Enabling I2C and Serial interfaces..."
if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt; then
    echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt
fi
if ! grep -q "^enable_uart=1" /boot/config.txt; then
    echo "enable_uart=1" | sudo tee -a /boot/config.txt
fi
check_status "Interface configuration"

# 4. Set up Python Environment
echo -e "\n[4/6] Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
check_status "Python environment setup"

# 5. Create Data Directories
echo -e "\n[5/6] Creating data directories..."
mkdir -p data/{thermal,gps,time,raw}
chmod 777 data/*
check_status "Data directory creation"

# 6. Set up Service
echo -e "\n[6/6] Setting up system service..."
sudo tee /etc/systemd/system/thermal-logger.service << EOF
[Unit]
Description=Thermal Logger System
After=multi-user.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python3 src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
check_status "Service creation"

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable thermal-logger
sudo systemctl start thermal-logger
check_status "Service activation"

echo -e "\n===== Installation Complete ====="
echo "Important Notes:"
echo "1. Data is stored in: $(pwd)/data/"
echo "2. Logs can be viewed with: journalctl -u thermal-logger -f"
echo "3. Service can be controlled with: sudo systemctl [start|stop|restart] thermal-logger"
echo "4. Reboot your Raspberry Pi to complete setup"
echo -e "\nReboot now? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]; then
    sudo reboot
fi
