# Connecting to Raspberry Pi 4 and Running the Thermal Logger

## 1. Initial Setup

1. Make sure your Raspberry Pi 4 has Raspberry Pi OS installed
2. Connect your Raspberry Pi to your network (either via Ethernet or WiFi)
3. Enable SSH on your Raspberry Pi (if not already enabled):
   - Create an empty file named `ssh` in the boot partition of the SD card, or
   - Use `sudo raspi-config` and enable SSH under "Interfacing Options"

## 2. Find Your Raspberry Pi's IP Address

On the Raspberry Pi, you can find its IP address by running:
```bash
hostname -I
```

Or from your Mac, you can try:
```bash
ping raspberrypi.local
```

## 3. Connect via SSH

From your Mac's terminal:
```bash
ssh pi@<raspberry-pi-ip-address>
# Example: ssh pi@192.168.1.100
```

The default password is usually 'raspberry' (change this for security)

## 4. Set Up the Project

1. Install git on Raspberry Pi:
```bash
sudo apt update
sudo apt install -y git
```

2. Clone the project:
```bash
git clone https://github.com/yourusername/thermal_logger.git
cd thermal_logger
```

3. Run the installation script:
```bash
chmod +x install.sh
./install.sh
```

## 5. Hardware Setup

1. Connect the FLIR Lepton thermal camera to the Raspberry Pi's SPI pins
2. Connect the HC-12 module to the Raspberry Pi's UART pins:
   - HC-12 TX → Raspberry Pi RX (GPIO15)
   - HC-12 VCC → Raspberry Pi 3.3V
   - HC-12 GND → Raspberry Pi GND
   - HC-12 RX → Raspberry Pi TX (GPIO14)

## 6. Running the System

1. Navigate to the project directory:
```bash
cd thermal_logger
```

2. Activate the virtual environment:
```bash
source venv/bin/activate
```

3. Run the main program:
```bash
python src/main.py
```

## 7. Viewing the Data

The data will be stored in the following directories:
- Thermal images: `data/flir_lepton/`
- GPS coordinates: `data/gps_coord/`
- Timestamps: `data/time_stamp/`
- Raw received data: `data/received_data/`

## Troubleshooting

1. If you can't connect via SSH:
   - Check if the Raspberry Pi is powered on
   - Verify the IP address is correct
   - Ensure you're on the same network

2. If hardware isn't detected:
   - Check physical connections
   - Enable SPI and UART in raspi-config:
     ```bash
     sudo raspi-config
     # Navigate to "Interface Options" and enable SPI and UART
     ```

3. If you get permission errors:
   - Check file permissions:
     ```bash
     sudo chmod -R 755 thermal_logger
     ```
   - Check USB/Serial permissions:
     ```bash
     sudo usermod -a -G dialout $USER
     ```

4. For log files and debugging:
   - Check thermal_logger.log in the project directory
   - Use `dmesg` to check for hardware detection issues

## Remote Development (Optional)

You can develop directly on the Raspberry Pi using VS Code:

1. Install "Remote - SSH" extension in VS Code
2. Press F1, type "Remote-SSH: Connect to Host"
3. Enter `pi@<raspberry-pi-ip-address>`
4. Select the thermal_logger folder when connected
