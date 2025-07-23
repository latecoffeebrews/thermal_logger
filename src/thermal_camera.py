import cv2
import numpy as np
import usb.core
import usb.util
import os
from datetime import datetime

class ThermalCamera:
    def __init__(self, save_dir='data/flir_lepton'):
        self.save_dir = save_dir
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

    def capture_frame(self):
        # Find the PureThermal device
        dev = usb.core.find(idVendor=0x1e4e, idProduct=0x0100)
        if dev is None:
            raise ValueError('Device not found')
        
        # Set up the device
        try:
            if dev.is_kernel_driver_active(0):
                dev.detach_kernel_driver(0)
        except Exception:
            pass
        
        dev.set_configuration()
        
        # Get an endpoint instance
        cfg = dev.get_active_configuration()
        intf = cfg[(0,0)]
        
        ep = usb.util.find_descriptor(
            intf,
            custom_match = \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_IN)
        
        # Read raw data
        data = dev.read(ep.bEndpointAddress, ep.wMaxPacketSize)
        
        # Convert to numpy array
        frame = np.frombuffer(data, dtype=np.uint16).reshape((60, 80))
        
        # Normalize to 8-bit for display
        frame = np.clip((frame - frame.min()) * 255.0 / (frame.max() - frame.min()), 0, 255).astype(np.uint8)
        return frame

    def save_frame(self, frame):
        """Save the thermal image with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.save_dir, f'thermal_{timestamp}.png')
        cv2.imwrite(filename, frame)
        return filename

    def display_frame(self, frame):
        """Display the thermal image"""
        cv2.imshow("FLIR Lepton 3.5 Frame", frame)
        cv2.waitKey(1)  # Show for 1ms, non-blocking
