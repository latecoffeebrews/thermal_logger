#!/usr/bin/env python3
"""
Module: thermal_camera.py
Provides a ThermalCamera class to interface with the FLIR Lepton 3.5
via the V4L2 backend and OpenCV for live display, capture, and saving.
"""

import os
import sys
import cv2
import numpy as np
from datetime import datetime

# Force Qt to use the X11 (xcb) plugin instead of Wayland
os.environ['QT_QPA_PLATFORM'] = 'xcb'

class ThermalCamera:
    def __init__(
        self,
        device_index=0,
        width=160,
        height=120,
        window_name="Thermal View",
        display_size=(800, 600)
    ):
        """
        Initialize the thermal camera.

        device_index: integer index for /dev/videoX (e.g., 0 for /dev/video0)
        width, height: expected frame dimensions
        window_name: title for the OpenCV window
        display_size: pixel size for the resizable window
        """
        self.device_index = device_index
        self.device = f"/dev/video{device_index}"
        self.width = width
        self.height = height
        self.window_name = window_name
        self.display_size = display_size

        # Open the V4L2 device
        self.cap = cv2.VideoCapture(self.device_index, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open thermal camera at {self.device}")

        # Colormap selection
        self.colormaps = [
            cv2.COLORMAP_JET,
            cv2.COLORMAP_HOT,
            cv2.COLORMAP_INFERNO,
            cv2.COLORMAP_RAINBOW
        ]
        self.cmap_idx = 0

        # Zoom & pan
        self.zoom_level = 1
        self.pan_x = 0
        self.pan_y = 0

        # Auto-contrast
        self.auto_scale = True
        self.min_val = 0
        self.max_val = 255

        # ==== FUTURE UPGRADE HOOKS ====
        # TODO: integrate radiometric calibration (map raw to temperature)
        # TODO: overlay GPS/altitude metadata on display
        # TODO: streaming callback for remote viewing (e.g., via Flask)
        # TODO: multi-camera support (stitching, switching)

        # Create the display window
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, *self.display_size)
        print("Controls: c=colormap, +=zoom in, -=zoom out, arrows=pan, a=toggle autoscale, s=save, q=quit")

    def capture_frame(self):
        """
        Grab one frame from the Lepton and return an 8-bit grayscale ndarray.
        """
        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Lepton frame grab failed")

        # Some setups return a flat 1×(H*W*3) array
        if frame.ndim == 2 and frame.shape[0] == 1:
            try:
                frame = frame.reshape((self.height, self.width, 3))
            except Exception:
                pass

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return gray

    def display_frame(self, frame):
        """
        Apply autoscale or fixed min/max, colormap, zoom & pan,
        then display in the window. Return last key pressed.
        """
        # Auto-contrast
        if self.auto_scale:
            self.min_val = int(np.percentile(frame, 2))
            self.max_val = int(np.percentile(frame, 98))
        span = max(self.max_val - self.min_val, 1)
        scaled = np.clip((frame - self.min_val) * 255.0 / span, 0, 255).astype(np.uint8)

        # Colormap
        colored = cv2.applyColorMap(scaled, self.colormaps[self.cmap_idx])

        # Zoom & pan
        h, w = colored.shape[:2]
        zoom_w, zoom_h = int(w / self.zoom_level), int(h / self.zoom_level)
        cx = w // 2 + self.pan_x
        cy = h // 2 + self.pan_y
        x1 = np.clip(cx - zoom_w // 2, 0, w - zoom_w)
        y1 = np.clip(cy - zoom_h // 2, 0, h - zoom_h)
        crop = colored[y1:y1 + zoom_h, x1:x1 + zoom_w]
        disp = cv2.resize(crop, self.display_size, interpolation=cv2.INTER_LINEAR)

        cv2.imshow(self.window_name, disp)
        key = cv2.waitKey(1) & 0xFF

        # Handle controls
        if key == ord('c'):
            self.cmap_idx = (self.cmap_idx + 1) % len(self.colormaps)
        elif key == ord('+') and self.zoom_level < 4:
            self.zoom_level += 1
        elif key == ord('-') and self.zoom_level > 1:
            self.zoom_level -= 1
        elif key == ord('a'):
            self.auto_scale = not self.auto_scale
        elif key == 81:   # left arrow
            self.pan_x -= 10
        elif key == 83:   # right arrow
            self.pan_x += 10
        elif key == 82:   # up arrow
            self.pan_y -= 10
        elif key == 84:   # down arrow
            self.pan_y += 10

        return key

    def save_frame(self, frame, save_dir="data"):
        """
        Save raw gray and colored images with UTC timestamp.
        Returns (raw_path, color_path).
        """
        os.makedirs(save_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        raw_path = os.path.join(save_dir, f"thermal_raw_{ts}.png")
        cv2.imwrite(raw_path, frame)

        # Regenerate colored image
        span = max(self.max_val - self.min_val, 1)
        scaled = np.clip((frame - self.min_val) * 255.0 / span, 0, 255).astype(np.uint8)
        color = cv2.applyColorMap(scaled, self.colormaps[self.cmap_idx])
        color_path = os.path.join(save_dir, f"thermal_color_{ts}.png")
        cv2.imwrite(color_path, color)

        return raw_path, color_path

    def close(self):
        """
        Release resources and close windows.
        """
        self.cap.release()
        cv2.destroyAllWindows()
