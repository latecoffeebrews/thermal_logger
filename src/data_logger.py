import pandas as pd
from datetime import datetime
import os

class DataLogger:
    def __init__(self, base_dir='data'):
        self.base_dir = base_dir
        self.data_dirs = {
            'thermal': os.path.join(base_dir, 'flir_lepton'),
            'gps': os.path.join(base_dir, 'gps_coord'),
            'time': os.path.join(base_dir, 'time_stamp'),
            'received': os.path.join(base_dir, 'received_data')
        }
        
        # Create directories if they don't exist
        for directory in self.data_dirs.values():
            if not os.path.exists(directory):
                os.makedirs(directory)

    def log_data(self, data_type, data):
        """Log data to appropriate CSV file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if data_type not in self.data_dirs:
            raise ValueError(f"Unknown data type: {data_type}")
            
        filename = os.path.join(self.data_dirs[data_type], f'log_{data_type}.csv')
        
        # Convert data to DataFrame if it's not already
        if not isinstance(data, pd.DataFrame):
            data = pd.DataFrame([data])
            
        # Add timestamp if not present
        if 'timestamp' not in data.columns:
            data['timestamp'] = timestamp
            
        # Append to CSV
        data.to_csv(filename, mode='a', header=not os.path.exists(filename), index=False)
        
        return filename

    def read_data(self, data_type, start_time=None, end_time=None):
        """Read data from CSV files within specified time range"""
        filename = os.path.join(self.data_dirs[data_type], f'log_{data_type}.csv')
        
        if not os.path.exists(filename):
            return pd.DataFrame()
            
        data = pd.read_csv(filename)
        
        if start_time and end_time:
            mask = (data['timestamp'] >= start_time) & (data['timestamp'] <= end_time)
            data = data[mask]
            
        return data
