#!/usr/bin/env python3
import serial
import time
import os
from datetime import datetime
from data_logger import DataLogger

class SerialReader:
    def __init__(self, port='/dev/ttyUSB0', baud_rate=9600):
        self.port = port
        self.baud_rate = baud_rate
        self.serial = None
        self.logger = DataLogger()

    def connect(self):
        try:
            self.serial = serial.Serial(self.port, self.baud_rate)
            print(f"Connected to {self.port}")
            return True
        except Exception as e:
            print(f"Error connecting to {self.port}: {e}")
            return False

    def read_and_log(self):
        if not self.serial:
            if not self.connect():
                return

        try:
            line = self.serial.readline().decode('utf-8').strip()
            if not line:
                return

            # Parse the line based on the format
            parts = line.split(',')
            if len(parts) < 2:
                return

            if parts[0] != 'DATA':
                print(f"Status: {line}")  # Print status messages
                return

            data_type = parts[1]
            if data_type == 'GPS' and len(parts) >= 7:
                # GPS data format: DATA,GPS,timestamp,lat,lon,alt,sats
                gps_data = {
                    'timestamp': parts[2],
                    'latitude': float(parts[3]),
                    'longitude': float(parts[4]),
                    'altitude': float(parts[5]),
                    'satellites': int(parts[6])
                }
                self.logger.log_data('gps', gps_data)
                print(f"Logged GPS data: {gps_data}")

            elif data_type == 'RTC' and len(parts) >= 3:
                # RTC data format: DATA,RTC,timestamp
                rtc_data = {
                    'timestamp': parts[2]
                }
                self.logger.log_data('time', rtc_data)
                print(f"Logged RTC data: {rtc_data}")

        except Exception as e:
            print(f"Error reading data: {e}")

    def run(self):
        print("Starting serial reader...")
        while True:
            self.read_and_log()
            time.sleep(0.1)  # Small delay to prevent CPU overuse

if __name__ == "__main__":
    # Try common USB ports for Arduino
    ports = [
        '/dev/ttyUSB0',  # Common Linux/Raspberry Pi
        '/dev/ttyACM0',  # Another common Arduino port
        '/dev/tty.usbmodem14201'  # Common Mac port
    ]

    reader = None
    for port in ports:
        try:
            reader = SerialReader(port=port)
            if reader.connect():
                break
        except:
            continue

    if reader and reader.serial:
        try:
            reader.run()
        except KeyboardInterrupt:
            print("\nStopping serial reader...")
            if reader.serial:
                reader.serial.close()
    else:
        print("Could not connect to any serial port. Is the Arduino connected?")
