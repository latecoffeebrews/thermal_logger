# main.py
#!/usr/bin/env python3
"""
Thermal Logger Main Program
---------------------------
Coordinates data collection from thermal camera and Arduino (GPS/RTC)
and saves it in a format suitable for later use with Google Earth Engine.
"""

import os
import sys
import time
import json
import logging
import signal
import cv2
from datetime import datetime

# Local imports
from config import INTERVALS, DEBUG
from thermal_camera import ThermalCamera
from hc12_receiver import HC12
from data_logger import DataLogger

# Set up logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('thermal_logger.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Directories
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
THERMAL_DIR = os.path.join(PROJECT_ROOT, 'data', 'flir_lepton')

class ThermalLoggerSystem:
    """Main system coordinator for the Thermal Logger project."""
    def __init__(self):
        """Initialize system components."""
        self.running = False
        self.last_thermal = 0
        self.last_gps = 0
        self.last_time = 0

        # Initialize components
        self.data_logger = DataLogger()
        self.thermal = ThermalCamera(device_index=0)
        self.hc12 = HC12(data_logger=self.data_logger)

        # Ensure directories
        os.makedirs(THERMAL_DIR, exist_ok=True)

        # Set up signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """Handle system shutdown gracefully."""
        logger.info("Shutdown signal received. Cleaning up...")
        self.running = False

    def _process_arduino_data(self, current_time):
        """Process Arduino data (GPS and timestamp)."""
        try:
            data = self.hc12.read_data()
            if data:
                arduino_data = json.loads(data)

                # Handle GPS data
                if 'gps' in arduino_data and current_time - self.last_gps >= INTERVALS['gps']:
                    self.data_logger.log_data('gps', arduino_data['gps'])
                    logger.info(f"GPS: {arduino_data['gps']}")
                    self.last_gps = current_time

                # Handle timestamp
                if 'timestamp' in arduino_data and current_time - self.last_time >= INTERVALS['time']:
                    self.data_logger.log_data('time', arduino_data['timestamp'])
                    logger.info(f"Time: {arduino_data['timestamp']}")
                    self.last_time = current_time

                # Save raw HC-12 data
                self.hc12.save_data(data)

        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON data received: {e}")
        except Exception as e:
            logger.error(f"Error processing Arduino data: {e}")
            if DEBUG:
                logger.exception("Detailed error:")

    def run(self):
        """Start the main system loop."""
        logger.info("Starting Thermal Logger System...")
        self.running = True

        try:
            while self.running:
                current_time = time.time()

                # Always capture and display frame
                frame = self.thermal.capture_frame()
                key = self.thermal.display_frame(frame)

                # Periodic save based on interval
                if current_time - self.last_thermal >= INTERVALS['thermal']:
                    try:
                        raw_path, color_path = self.thermal.save_frame(frame, save_dir=THERMAL_DIR)
                        logger.info(f"Saved thermal images: raw={raw_path}, color={color_path}")
                        self.last_thermal = current_time
                    except Exception as e:
                        logger.error(f"Error saving thermal image: {e}")
                        if DEBUG:
                            logger.exception("Detailed error:")

                # Process Arduino every loop
                self._process_arduino_data(current_time)

                # Handle key inputs
                if key == ord('q'):
                    logger.info("Manual quit requested")
                    break
                elif key == ord('s'):
                    # immediate save
                    raw_path, color_path = self.thermal.save_frame(frame, save_dir=THERMAL_DIR)
                    logger.info(f"📸 Manual save: raw={raw_path}, color={color_path}")

                # Brief pause
                time.sleep(0.05)

        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            if DEBUG:
                logger.exception("Detailed error:")
            return False

        finally:
            # Cleanup
            logger.info("Cleaning up resources...")
            cv2.destroyAllWindows()
            self.hc12.close()
            logger.info("Cleanup complete")

        return True

if __name__ == "__main__":
    system = ThermalLoggerSystem()
    success = system.run()
    sys.exit(0 if success else 1)
