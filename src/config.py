"""
Configuration settings for the Thermal Logger system.
Edit these settings to customize the system behavior.
"""

import os

# Base directory for the project (automatically set)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data storage paths
DATA_PATHS = {
    'thermal': os.path.join(BASE_DIR, 'data', 'thermal'),
    'gps': os.path.join(BASE_DIR, 'data', 'gps'),
    'time': os.path.join(BASE_DIR, 'data', 'time'),
    'raw': os.path.join(BASE_DIR, 'data', 'raw')
}

# Arduino configuration
ARDUINO_CONFIG = {
    'baud_rate': 9600,
    'timeout': 1,
    'ports': [  # Ports to try, in order
        '/dev/ttyUSB0',
        '/dev/ttyUSB1',
        '/dev/ttyACM0',
        '/dev/ttyACM1'
    ]
}

# Data collection intervals (in seconds)
INTERVALS = {
    'gps': 6,        # GPS data collection interval
    'thermal': 30,   # Thermal image capture interval
    'time': 3        # Timestamp logging interval
}

# File naming formats
FILENAME_FORMATS = {
    'thermal': 'thermal_%Y%m%d_%H%M%S.npy',
    'gps': 'gps_%Y%m%d.csv',
    'time': 'time_%Y%m%d.csv'
}

# CSV Headers
CSV_HEADERS = {
    'gps': ['timestamp', 'latitude', 'longitude', 'altitude', 'satellites'],
    'time': ['timestamp', 'source']
}

# Debug mode (set to False in production)
DEBUG = True
