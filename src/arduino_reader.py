#!/usr/bin/env python3
import serial
import time
import os
from datetime import datetime
from data_logger import DataLogger

class ArduinoReader:
    def __init__(self, port='/dev/ttyUSB0', baud_rate=9600):
        """Initialize Arduino serial connection"""
        self.port = port
        self.baud_rate = baud_rate
        self.serial = None
        self.logger = DataLogger()
        self.connected = False

    def connect(self):
        """Attempt to connect to Arduino"""
        try:
            self.serial = serial.Serial(self.port, self.baud_rate, timeout=1)
            self.connected = True
            print(f"Connected to Arduino on {self.port}")
            return True
        except Exception as e:
            print(f"Error connecting to Arduino: {e}")
            return False

    def find_arduino(self):
        """Try different USB ports to find Arduino"""
        possible_ports = [
            '/dev/ttyUSB0',
            '/dev/ttyUSB1',
            '/dev/ttyACM0',
            '/dev/ttyACM1'
        ]
        
        for port in possible_ports:
            try:
                self.port = port
                if self.connect():
                    return True
            except:
                continue
        return False

    def process_data(self, line):
        """Process incoming data from Arduino"""
        try:
            parts = line.split(',')
            if len(parts) < 2 or parts[0] != 'DATA':
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
                print(f"Logged GPS: {gps_data['latitude']}, {gps_data['longitude']}")

            elif data_type == 'RTC' and len(parts) >= 3:
                # RTC data format: DATA,RTC,timestamp
                rtc_data = {
                    'timestamp': parts[2]
                }
                self.logger.log_data('time', rtc_data)
                print(f"Logged RTC: {rtc_data['timestamp']}")

        except Exception as e:
            print(f"Error processing data: {e}")

    def run(self):
        """Main loop to read and process Arduino data"""
        if not self.connected and not self.find_arduino():
            print("Could not find Arduino. Please check connection.")
            return

        print("Starting Arduino data collection...")
        while True:
            try:
                if self.serial.in_waiting:
                    line = self.serial.readline().decode('utf-8').strip()
                    if line:
                        self.process_data(line)
                time.sleep(0.1)  # Prevent CPU overuse

            except KeyboardInterrupt:
                print("\nStopping data collection...")
                break
            except Exception as e:
                print(f"Error reading serial: {e}")
                # Try to reconnect
                self.connected = False
                time.sleep(5)
                self.find_arduino()

        if self.serial:
            self.serial.close()

if __name__ == "__main__":
    reader = ArduinoReader()
    reader.run()
