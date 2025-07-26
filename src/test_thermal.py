#!/usr/bin/env python3
"""
test_thermal.py

Initialize and run the ThermalCamera class from thermal_camera.py.
Usage: sudo python3 test_thermal.py
Controls: s = save frame, q = quit
"""

import os
import sys
from datetime import datetime

# ── Make sure we can import thermal_camera.py from the same folder ──
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from thermal_camera import ThermalCamera

def main():
    # determine where to save images (project_root/data/flir_lepton)
    project_root = os.path.dirname(script_dir)
    save_dir = os.path.join(project_root, "data", "flir_lepton")
    
    # initialize camera
    try:
        cam = ThermalCamera(device_index=0)
    except Exception as e:
        print("❌ Error initializing camera:", e)
        sys.exit(1)

    print("✅ Camera initialized. Press 's' to save, 'q' to quit.")

    # capture–display loop
    while True:
        frame = cam.capture_frame()
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        key = cam.display_frame(frame, timestamp=timestamp)

        if key == ord('s'):
            raw_path, color_path = cam.save_frame(frame, save_dir=save_dir)
            print(f"📸 Saved raw → {raw_path}\n    colored → {color_path}")
        elif key == ord('q'):
            print("✂️ Exiting.")
            break

    cam.close()

if __name__ == "__main__":
    main()
