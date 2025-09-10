class KalmanFilter3D:
    """
    3D Kalman filter implementation for sensor fusion
    Handles x, y, z measurements independently with the same filter parameters
    """
    def __init__(self, process_variance, measurement_variance, error_variance):
        # Initialize filter parameters for each axis
        self.process_variance = process_variance
        self.measurement_variance = measurement_variance
        self.error_variance = error_variance
        
        # State variables for each axis (x, y, z)
        self.state_estimate = [0.0, 0.0, 0.0]
        self.error_estimate = [error_variance, error_variance, error_variance]
        
    def update(self, measurement):
        """
        Update the state estimate using a new measurement
        
        Args:
            measurement: List of [x, y, z] measurements
            
        Returns:
            List of filtered [x, y, z] values
        """
        filtered_values = []
        
        for i in range(3):  # Process each axis
            # Prediction step
            # State prediction (unchanged as we assume constant state between updates)
            predicted_state = self.state_estimate[i]
            # Error prediction
            predicted_error = self.error_estimate[i] + self.process_variance
            
            # Update step
            # Kalman gain
            kalman_gain = predicted_error / (predicted_error + self.measurement_variance)
            
            # State update
            self.state_estimate[i] = predicted_state + kalman_gain * (measurement[i] - predicted_state)
            
            # Error update
            self.error_estimate[i] = (1 - kalman_gain) * predicted_error
            
            filtered_values.append(self.state_estimate[i])
            
        return filtered_values
    
    def reset(self):
        """Reset the filter to initial conditions"""
        self.state_estimate = [0.0, 0.0, 0.0]
        self.error_estimate = [self.error_variance, self.error_variance, self.error_variance]