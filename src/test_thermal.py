#!/usr/bin/env python3
from thermal_camera import ThermalCamera
import cv2
import time
import sys
import os
import usb.core
import usb.util
from datetime import datetime

def check_system_requirements():
    """Check if all system requirements are met"""
    issues = []
    
    # Check OpenCV
    try:
        print(f"OpenCV version: {cv2.__version__}")
    except ImportError:
        issues.append("OpenCV (cv2) is not installed")
    
    # Check USB devices
    try:
        flir_devices = list(usb.core.find(idVendor=0x1e4e, idProduct=0x0100, find_all=True))
        if not flir_devices:
            issues.append("No FLIR camera found. Check USB connection")
        else:
            print(f"Found {len(flir_devices)} FLIR camera(s)")
            for dev in flir_devices:
                try:
                    print(f"  - Bus: {dev.bus}")
                    print(f"  - Manufacturer: {usb.util.get_string(dev, dev.iManufacturer)}")
                    print(f"  - Product: {usb.util.get_string(dev, dev.iProduct)}")
                except:
                    print("  - Device info unavailable (permission issue)")
    except usb.core.NoBackendError:
        issues.append("USB backend not available. Try: brew install libusb")
    except Exception as e:
        issues.append(f"USB Error: {str(e)}")
    
    return issues

def test_thermal_camera():
    print("=== FLIR Lepton Camera Test ===")
    print("Running system checks...")
    # Check system requirements
    issues = check_system_requirements()
    if issues:
        print("\nSystem Check Failed!")
        print("Found the following issues:")
        for issue in issues:
            print(f" - {issue}")
        print("\nPlease fix these issues and try again.")
        sys.exit(1)
    
    print("\nSystem Check Passed!")
    
    # Check if running with sudo
    if os.geteuid() != 0:
        print("\nError: This script needs to be run with sudo privileges!")
        print("Please run: sudo python3 src/test_thermal.py")
        sys.exit(1)
    
    print("\nInitializing Thermal Camera...")
    try:
        camera = ThermalCamera()
    except Exception as e:
        print(f"\nFailed to initialize camera: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Make sure the camera is properly connected")
        print("2. Try unplugging and replugging the camera")
        print("3. Check if the camera appears in system_profiler SPUSBDataType")
        print("4. Ensure libusb is installed: brew install libusb")
        sys.exit(1)
    camera = ThermalCamera()
    
    print("\nControls:")
    print("- Press 's' to save current frame")
    print("- Press 'c' to change colormap")
    print("- Press 'q' to quit")
    print("\nStarting camera feed...")
    
    # Available colormaps
    colormaps = [
        cv2.COLORMAP_JET,
        cv2.COLORMAP_HOT,
        cv2.COLORMAP_INFERNO,
        cv2.COLORMAP_RAINBOW
    ]
    current_colormap = 0
    
    try:
        while True:
            try:
                # Capture frame with timing
                start_time = time.time()
                frame = camera.capture_frame()
                capture_time = time.time() - start_time
                
                # Process frame
                colored_frame = cv2.applyColorMap(frame, colormaps[current_colormap])
                display_frame = cv2.resize(colored_frame, (400, 300))
                
                # Calculate and display FPS and frame info
                fps = 1.0 / capture_time
                min_temp = frame.min()
                max_temp = frame.max()
                avg_temp = frame.mean()
                
                # Add text to display frame
                info_text = f"FPS: {fps:.1f} | Min: {min_temp} | Max: {max_temp} | Avg: {avg_temp:.1f}"
                cv2.putText(display_frame, info_text, (10, 30), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Display the frame
                cv2.imshow("FLIR Lepton 3.5 Frame", display_frame)
                
                # Print periodic debug info
                if time.time() % 5 < 0.1:  # Every 5 seconds
                    print(f"\nDebug Info:")
                    print(f"Frame Rate: {fps:.1f} FPS")
                    print(f"Frame Size: {frame.shape}")
                    print(f"Temperature Range: {min_temp} to {max_temp}")
                    print(f"Memory Usage: {frame.nbytes / 1024:.1f}KB")
                
                # Check for key presses
                key = cv2.waitKey(1) & 0xFF
                
                # 's' to save frame
                if key == ord('s'):
                    # Save both raw and colored frames
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    raw_filename = camera.save_frame(frame)
                    color_filename = os.path.join(camera.save_dir, f'thermal_colored_{timestamp}.png')
                    cv2.imwrite(color_filename, colored_frame)
                    print(f"Saved frames to:\n - Raw: {raw_filename}\n - Colored: {color_filename}")
                
                # 'c' to change colormap
                elif key == ord('c'):
                    current_colormap = (current_colormap + 1) % len(colormaps)
                    print(f"Changed colormap to: {colormaps[current_colormap]}")
                
                # 'q' to quit
                elif key == ord('q'):
                    print("\nQuitting...")
                
            except Exception as e:
                print(f"Error: {e}")
                print("Retrying in 1 second...")
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        cv2.destroyAllWindows()

if __name__ == "__main__":
    test_thermal_camera()
