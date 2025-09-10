import os
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from mpl_toolkits.mplot3d import Axes3D
from scipy import signal
import plotly.graph_objs as go
import plotly.io as pio

class CanSatDataAnalyzer:
    def __init__(self, data_file, events_file, output_dir=None):
        """
        Initialize the CanSat data analyzer
        
        Args:
            data_file (str): Path to the data CSV file
            events_file (str): Path to the events CSV file
            output_dir (str, optional): Directory to save visualizations
        """
        # Load data
        self.data = pd.read_csv(data_file)
        self.events = pd.read_csv(events_file)
        
        # Convert timestamp to datetime
        self.data['timestamp'] = pd.to_datetime(self.data['timestamp'], unit='s')
        self.events['timestamp'] = pd.to_datetime(self.events['timestamp'], unit='s')
        
        # Set timestamp as index
        self.data.set_index('timestamp', inplace=True)
        self.events.set_index('timestamp', inplace=True)
        
        # Create output directory
        self.output_dir = output_dir or f"cansat_analysis_{self.data.index[0].strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Prepare visualization styles
        plt.style.use('default')
        
    def clean_data(self):
        """
        Clean and preprocess the data
        
        Returns:
            pandas.DataFrame: Cleaned data
        """
        # Remove rows with all NaN values
        self.data.dropna(how='all', inplace=True)
        
        # Fill missing values with interpolation
        numeric_columns = ['temperature', 'pressure', 'altitude', 
                           'ax', 'ay', 'az', 'gx', 'gy', 'gz']
        self.data[numeric_columns] = self.data[numeric_columns].interpolate()
        
        return self.data
    
    def calculate_derived_metrics(self):
        """
        Calculate additional metrics from raw sensor data
        
        Returns:
            pandas.DataFrame: Data with derived metrics
        """
        # Total acceleration magnitude
        self.data['total_accel'] = np.sqrt(
            self.data['ax']**2 + 
            self.data['ay']**2 + 
            self.data['az']**2
        )
        
        # Total gyroscope rotation magnitude
        self.data['total_gyro'] = np.sqrt(
            self.data['gx']**2 + 
            self.data['gy']**2 + 
            self.data['gz']**2
        )
        
        # Vertical velocity (simple derivative of altitude)
        self.data['vertical_velocity'] = self.data['altitude'].diff() / 0.1  # Assuming 10Hz sampling
        
        return self.data
    
    def plot_3d_trajectory(self):
        """
        Create a 3D trajectory plot using acceleration and altitude
        """
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # Plot 3D trajectory
        scatter = ax.scatter(
            self.data['ax'], 
            self.data['ay'], 
            self.data['az'], 
            c=self.data['altitude'], 
            cmap='viridis'
        )
        
        ax.set_xlabel('Acceleration X')
        ax.set_ylabel('Acceleration Y')
        ax.set_zlabel('Acceleration Z')
        ax.set_title('3D Trajectory of CanSat Flight')
        
        plt.colorbar(scatter, label='Altitude')
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, '3d_trajectory.png'))
        plt.close()
    
    def plot_sensor_overview(self):
        """
        Create comprehensive sensor data overview
        """
        fig, axs = plt.subplots(3, 2, figsize=(15, 12))
        fig.suptitle('CanSat Sensor Data Overview')
        
        # Altitude plot
        axs[0, 0].plot(self.data.index, self.data['altitude'])
        axs[0, 0].set_title('Altitude')
        axs[0, 0].set_ylabel('Meters')
        
        # Temperature plot
        axs[0, 1].plot(self.data.index, self.data['temperature'], color='red')
        axs[0, 1].set_title('Temperature')
        axs[0, 1].set_ylabel('°C')
        
        # Acceleration plots
        axs[1, 0].plot(self.data.index, self.data['ax'], label='X')
        axs[1, 0].plot(self.data.index, self.data['ay'], label='Y')
        axs[1, 0].plot(self.data.index, self.data['az'], label='Z')
        axs[1, 0].set_title('Acceleration')
        axs[1, 0].legend()
        
        # Gyroscope plots
        axs[1, 1].plot(self.data.index, self.data['gx'], label='X')
        axs[1, 1].plot(self.data.index, self.data['gy'], label='Y')
        axs[1, 1].plot(self.data.index, self.data['gz'], label='Z')
        axs[1, 1].set_title('Gyroscope')
        axs[1, 1].legend()
        
        # Pressure plot
        axs[2, 0].plot(self.data.index, self.data['pressure'])
        axs[2, 0].set_title('Pressure')
        axs[2, 0].set_ylabel('hPa')
        
        # GPS plot (if available)
        if 'latitude' in self.data.columns and 'longitude' in self.data.columns:
            axs[2, 1].plot(self.data['longitude'], self.data['latitude'])
            axs[2, 1].set_title('GPS Trajectory')
            axs[2, 1].set_xlabel('Longitude')
            axs[2, 1].set_ylabel('Latitude')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'sensor_overview.png'))
        plt.close()
    
    def plot_interactive_trajectory(self):
        """
        Create an interactive 3D trajectory plot using Plotly
        """
        trace = go.Scatter3d(
            x=self.data['ax'],
            y=self.data['ay'],
            z=self.data['az'],
            mode='lines',
            line=dict(
                color=self.data['altitude'],
                colorscale='Viridis',
                width=5
            )
        )
        
        layout = go.Layout(
            title='Interactive 3D CanSat Trajectory',
            scene=dict(
                xaxis_title='Acceleration X',
                yaxis_title='Acceleration Y',
                zaxis_title='Acceleration Z'
            )
        )
        
        fig = go.Figure(data=[trace], layout=layout)
        pio.write_html(fig, file=os.path.join(self.output_dir, 'interactive_trajectory.html'))
    
    def save_summary_report(self):
        """
        Generate a summary report of flight data
        """
        with open(os.path.join(self.output_dir, 'flight_summary.txt'), 'w') as f:
            f.write("CanSat Flight Summary\n")
            f.write("====================\n\n")
            
            # Flight duration
            duration = (self.data.index[-1] - self.data.index[0]).total_seconds()
            f.write(f"Flight Duration: {duration:.2f} seconds\n\n")
            
            # Key metrics
            f.write("Key Metrics:\n")
            f.write(f"Max Altitude: {self.data['altitude'].max():.2f} m\n")
            f.write(f"Min Altitude: {self.data['altitude'].min():.2f} m\n")
            f.write(f"Max Temperature: {self.data['temperature'].max():.2f} °C\n")
            f.write(f"Min Temperature: {self.data['temperature'].min():.2f} °C\n")
            
            # Events summary
            f.write("\nFlight Events:\n")
            for idx, event in self.events.iterrows():
                f.write(f"{idx}: {event['event']} - {event['details']}\n")
    
    def analyze(self):
        """
        Perform complete analysis and generate visualizations
        """
        # Clean data
        self.clean_data()
        
        # Calculate derived metrics
        self.calculate_derived_metrics()
        
        # Generate visualizations
        self.plot_3d_trajectory()
        self.plot_sensor_overview()
        self.plot_interactive_trajectory()
        
        # Generate summary report
        self.save_summary_report()
        
        print(f"Analysis complete. Results saved in {self.output_dir}")

def main():
    parser = argparse.ArgumentParser(description='CanSat Post-Flight Data Analysis')
    parser.add_argument('data_file', help='Path to data CSV file')
    parser.add_argument('events_file', help='Path to events CSV file')
    parser.add_argument('--output_dir', help='Output directory for analysis', default=None)
    
    args = parser.parse_args()
    
    analyzer = CanSatDataAnalyzer(
        args.data_file, 
        args.events_file, 
        args.output_dir
    )
    analyzer.analyze()

if __name__ == "__main__":
    main()