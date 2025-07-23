# Thermal Logger
A Python application for capturing and displaying thermal images from a FLIR Lepton 3.5 camera using a PureThermal board.

## Requirements
- Raspberry Pi 4 B
- FLIR Lepton 3.5 camera with PureThermal board
- Python 3.7+

## Installation

1. Clone this repository:
```bash
git clone https://github.com/YOUR_USERNAME/thermal_logger.git
cd thermal_logger
```

2. Install the required packages:
```bash
pip3 install -r requirements.txt
```

3. Set up USB permissions on Raspberry Pi:
```bash
sudo usermod -a -G plugdev $USER
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="1e4e", ATTRS{idProduct}=="0100", MODE="0666"' | sudo tee /etc/udev/rules.d/99-purethermal.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

4. Run the application:
```bash
python3 src/camera.py/camera.py
```

## Usage
The application will:
1. Connect to the FLIR Lepton camera
2. Display the thermal image in a window
3. Press any key to exit

## Troubleshooting
If you get permission errors:
1. Make sure you've set up the udev rules correctly
2. Try running with sudo: `sudo python3 src/camera.py/camera.py`
3. Ensure the camera is properly connected via USB
