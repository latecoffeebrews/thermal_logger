# Thermal Logger Project Structure
thermal_logger/
│
├── install.sh              # Installation script
├── requirements.txt        # Python dependencies
│
├── data/                   # Data storage
│   ├── thermal/           # Thermal image data
│   ├── gps/              # GPS coordinates
│   ├── time/             # Timestamp data
│   └── raw/              # Raw sensor data
│
├── src/
│   ├── main.py           # Main program entry
│   ├── config.py         # Configuration settings
│   ├── data_logger.py    # Data logging system
│   ├── arduino_handler.py # Arduino communication
│   └── utils/
│       ├── __init__.py
│       ├── gps.py        # GPS data processing
│       └── thermal.py    # Thermal data processing
│
└── docs/
    ├── README.md         # Project documentation
    └── MAINTENANCE.md    # Maintenance guide
