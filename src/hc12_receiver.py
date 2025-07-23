import serial
import time
import os
from datetime import datetime

class HC12:
    def __init__(self, port='/dev/ttyS0', baudrate=9600, data_logger=None):
        self.port = port
        self.baudrate = baudrate
        self.data_logger = data_logger
        
        # Initialize serial connection
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1
        )

    def read_data(self):
        """Read data from HC-12"""
        if self.ser.in_waiting:
            return self.ser.readline().decode('utf-8').strip()
        return None

    def save_data(self, data):
        """Save received data using DataLogger"""
        if data and self.data_logger:
            return self.data_logger.log_data('received', {'data': data})
        return None

    def close(self):
        """Close serial connection"""
        self.ser.close()
