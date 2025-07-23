#!/bin/bash

echo "=== FLIR Camera Setup Script ==="
echo "This script will set up your Mac for FLIR camera access"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run this script with sudo"
    exit 1
fi

# Install Homebrew if not installed
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install required packages
echo "Installing required packages..."
brew install libusb
brew install python@3.9

# Create USB access group
echo "Setting up USB permissions..."
dseditgroup -o create -q com.apple.access_usb
dseditgroup -o edit -a $SUDO_USER -t user com.apple.access_usb

# Create udev rules directory if it doesn't exist
mkdir -p /etc/udev/rules.d/

# Create rules file
echo "Creating USB rules..."
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="1e4e", ATTRS{idProduct}=="0100", MODE="0666", GROUP="com.apple.access_usb"' > /etc/udev/rules.d/99-purethermal.rules

# Set up Python environment
echo "Setting up Python environment..."
cd /Users/christiangarcia/thermal_logger
python3 -m venv venv
source venv/bin/activate
pip install opencv-python numpy pyusb pandas

# Fix USB permissions
echo "Fixing USB permissions..."
if [ -d "/dev/usb" ]; then
    chown -R root:wheel /dev/usb
    chmod -R 666 /dev/usb
fi

echo "Setup complete!"
echo "Please:"
echo "1. Unplug your FLIR camera"
echo "2. Log out and log back in"
echo "3. Plug in your FLIR camera"
echo "4. Run: sudo python3 src/test_thermal.py"
