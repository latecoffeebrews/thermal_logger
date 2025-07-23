#!/usr/bin/env python3
import cv2
import numpy as np
import time
import os
from datetime import datetime
from data_logger import DataLogger

class ThermalProcessor:
    def __init__(self):
        """Initialize thermal image processing"""
        self.logger = DataLogger()
        self.current_colormap = cv2.COLORMAP_INFERNO
        self.colormaps = [
            cv2.COLORMAP_JET,
            cv2.COLORMAP_HOT,
            cv2.COLORMAP_INFERNO,
            cv2.COLORMAP_RAINBOW
        ]
        
    def process_frame(self, frame):
        """Process thermal frame with colormap"""
        colored = cv2.applyColorMap(frame, self.current_colormap)
        min_temp = frame.min()
        max_temp = frame.max()
        avg_temp = frame.mean()
        
        # Add temperature info
        text = f"Min: {min_temp:.1f} | Max: {max_temp:.1f} | Avg: {avg_temp:.1f}"
        cv2.putText(colored, text, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return colored
        
    def save_frame(self, frame, colored_frame=None):
        """Save both raw and colored frames"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save raw frame
        raw_path = os.path.join(self.logger.data_dirs['thermal'], 
                               f'thermal_raw_{timestamp}.npy')
        np.save(raw_path, frame)
        
        # Save colored frame if provided
        if colored_frame is not None:
            colored_path = os.path.join(self.logger.data_dirs['thermal'], 
                                      f'thermal_colored_{timestamp}.png')
            cv2.imwrite(colored_path, colored_frame)
            
        return raw_path
        
    def cycle_colormap(self):
        """Cycle through available colormaps"""
        current_idx = self.colormaps.index(self.current_colormap)
        next_idx = (current_idx + 1) % len(self.colormaps)
        self.current_colormap = self.colormaps[next_idx]
        return self.current_colormap
