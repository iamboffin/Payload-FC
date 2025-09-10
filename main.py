import machine
from machine import Pin, I2C, SPI,PWM
import time
from time import sleep
import math
import os
try:
    import sdcard
    import json
except ImportError:
    pass

try:
    from mpu6050 import MPU6050
    from bme280 import BME280
    from neo6m import NEO6M
    from kalman import KalmanFilter3D
    CUSTOM_MODULES_AVAILABLE = True
except ImportError:
    CUSTOM_MODULES_AVAILABLE = False
# Pin configurations
PIN_CONFIG = {
    'LED': {
        'GREEN': 2,
        'RED': 3
    },
    'BUTTON': 22,
    'I2C0': {
        'SDA': 20,
        'SCL': 21
    },
    'I2C1': {
        'SDA': 18,
        'SCL': 19
    },
    'SPI': {
        'CS': 13,
        'SCK': 10,
        'MOSI': 11,
        'MISO': 12
    },
    'GPS': {
        'TX': 8,
        'RX': 9
    },
    'BUZZER' :27
}
class FlightStates:
    WAITING_START = -1
    IDLE = 0
    PREFLIGHT = 1
    CALIBRATION = 2
    READY = 3
    ASCENT = 4
    DESCENT = 5
    LANDED = 6
    SHUTDOWN = 7

    @staticmethod
    def get_state_name(state):
        states = {
            -1: "WAITING_START",
            0: "IDLE",
            1: "PREFLIGHT",
            2: "CALIBRATION",
            3: "READY",
            4: "ASCENT",
            5: "DESCENT",
            6: "LANDED",
            7: "SHUTDOWN"
        }
        return states.get(state, "UNKNOWN")

class CanSat:
    def __init__(self):
        self._debug_messages = []
        self.state = FlightStates.WAITING_START
        self.data_buffer = []
        self.last_save_time = time.time()
        self.save_interval = 5
        self.current_file = None
        self.event_file = None
        self.last_altitude = None
        self.descent_detected = False
        self.baseline_pressure = None
        self.initial_altitude = 0
        
        try:
            self.led_red = Pin(PIN_CONFIG['LED']['RED'], Pin.OUT)
            self.led_green = Pin(PIN_CONFIG['LED']['GREEN'], Pin.OUT)
            self.button = Pin(PIN_CONFIG['BUTTON'], Pin.IN, Pin.PULL_UP)
            
            self.led_red.off()
            self.led_green.off()
            
            self._log("Basic hardware initialized")
            self._blink_pattern(self.led_green, [0.2, 0.2, 0.2])
            
        except Exception as e:
            print(f"Critical Error during initialization: {str(e)}")
            self._fatal_error(f"Hardware initialization failed: {str(e)}")

        self.status = {
            "mpu": {"working": False, "error": None},
            "bme": {"working": False, "error": None},
            "gps": {"working": False, "error": None},
            "sd": {"working": False, "error": None},
            "system_ready": False
        }
        
        try:
            self._init_buzzer()  # Add buzzer initialization
        except Exception as e:
            self._log(f"Buzzer initialization failed: {str(e)}", "ERROR")
        
        self._init_data_storage()

    def _init_data_storage(self):
        try:
            timestamp = time.time()
            self.current_file = f"data_{timestamp}.csv"
            with open(self.current_file, 'w') as f:
                f.write("timestamp,temperature,pressure,altitude,ax,ay,az,gx,gy,gz,latitude,longitude\n")
            
            self.event_file = f"events_{timestamp}.csv"
            with open(self.event_file, 'w') as f:
                f.write("timestamp,event,state,altitude,details\n")
            
            self._log(f"Created data files: {self.current_file} and {self.event_file}")
            self._log_event("System Initialization", "System startup completed")
            
        except Exception as e:
            self._log(f"Error creating data files: {str(e)}", "ERROR")
            self._fatal_error(f"Could not initialize data storage: {str(e)}")

    def _log_event(self, event, details=""):
        """Log flight events with current sensor data"""
        try:
            if self.event_file:
                timestamp = time.time()
                state_name = FlightStates.get_state_name(self.state)
                altitude = "None"
                
                # Try to get current altitude if BME is working
                if self.status["bme"]["working"]:
                    try:
                        altitude = str(self.bme.read_altitude())
                    except:
                        pass
                
                with open(self.event_file, 'a') as f:
                    f.write(f"{timestamp},{event},{state_name},{altitude},{details}\n")
                
                self._log(f"Event logged: {event} - {details}")
        except Exception as e:
            self._log(f"Error logging event: {str(e)}", "ERROR")
            
    def _init_buzzer(self):
        """Initialize passive buzzer pin with PWM"""
        try:
            # Use PWM for passive buzzer
            self.buzzer = PWM(Pin(PIN_CONFIG['BUZZER'], Pin.OUT))
            
            # Set a frequency that provides good volume (around 2000-4000 Hz is typically loud)
            self.buzzer.freq(2000)  # 2.5 kHz is generally loud and piercing
            
            # Initially set duty cycle to 0 (off)
            self.buzzer.duty_u16(0)
            
            self._log("Passive Buzzer initialized with PWM")
        except Exception as e:
            self._log(f"Passive Buzzer initialization failed: {str(e)}", "ERROR")

    
    def _buzz_pattern(self, pattern):
        """
        Play a buzzer pattern for passive buzzer
        pattern is a list of (duration_on, duration_off) tuples
        """
        try:
            for on_time, off_time in pattern:
                # Turn on buzzer with 50% duty cycle
                self.buzzer.duty_u16(32768)  # 50% duty cycle for 16-bit PWM
                sleep(on_time)
                
                # Turn off buzzer
                self.buzzer.duty_u16(0)
                sleep(off_time)
        except Exception as e:
            self._log(f"Buzzer error: {str(e)}", "ERROR")
            
    def _event_buzzer_patterns(self, event_type):
        """
        Play specific buzzer patterns for different events
        """
        patterns = {
            "STARTUP": [(0.2, 0.1), (0.2, 0.1), (0.2, 0)],  # Three short beeps
            "SENSORS_READY": [(0.5, 0.2), (0.5, 0)],  # Two medium beeps
            "FLIGHT_START": [(0.5, 0.1), (0.5, 0.1), (0.5, 0)],  # Three medium beeps
            "APOGEE": [(0.3, 0.1), (0.3, 0.1), (0.3, 0.1), (0.3, 0)],  # Four quick beeps
            "LANDING": [(1.0, 0.2), (1.0, 0.2), (1.0, 0)],  # Three long beeps
            "ERROR": [(0.1, 0.1)] * 5,  # Rapid short beeps
            "SHUTDOWN": [(0.5, 0.2), (0.5, 0.2), (0.5, 0)]      # Descending tones
        }
        
        pattern = patterns.get(event_type, [(0.1, 0.1)])  # Default to short beep if event not found
        self._buzz_pattern(pattern)

    def init_sensors(self):
        self._log("Starting sensor initialization...")

        try:
            self.i2c0 = I2C(0, 
                        sda=Pin(PIN_CONFIG['I2C0']['SDA']), 
                        scl=Pin(PIN_CONFIG['I2C0']['SCL']), 
                        freq=400000)
            
            self.i2c1 = I2C(1, 
                        sda=Pin(PIN_CONFIG['I2C1']['SDA']), 
                        scl=PIN_CONFIG['I2C1']['SCL'], 
                        freq=400000)
            
        except Exception as e:
            self._log(f"I2C initialization failed: {str(e)}", "ERROR")
            return False

        if CUSTOM_MODULES_AVAILABLE:
            # Initialize BME280 with ground level calibration
            try:
                self.bme = BME280(i2c=self.i2c1, sea_level_pressure=1013.25)
                
                # Perform ground level calibration
                self.bme.calibrate_ground_level()
                
                # Set baseline pressure and initial altitude
                self.baseline_pressure = self.bme.ground_pressure
                self.initial_altitude = self.bme.ground_altitude
                
                self.status["bme"]["working"] = True
                
                self._log(f"Ground zero pressure calibrated: {self.baseline_pressure} hPa")
                self._log(f"Initial ground altitude set to: {self.initial_altitude} m")
            except Exception as e:
                self.status["bme"]["error"] = str(e)
                self._log(f"BME280 error: {str(e)}", "ERROR")

            # Initialize MPU6050
            try:
                self.mpu = MPU6050(self.i2c0)
                self.status["mpu"]["working"] = True
                self._log("MPU6050 initialized")
            except Exception as e:
                self.status["mpu"]["error"] = str(e)
                self._log(f"MPU6050 error: {str(e)}", "ERROR")

            # Initialize GPS
            try:
                self.gps = NEO6M(uart_id=1, tx_pin=PIN_CONFIG['GPS']['TX'], rx_pin=PIN_CONFIG['GPS']['RX'])
                self.status["gps"]["working"] = True
                self._log("GPS initialized")
            except Exception as e:
                self.status["gps"]["error"] = str(e)
                self._log(f"GPS error: {str(e)}", "ERROR")

            if self.status["mpu"]["working"] and self.status["bme"]["working"]:
                self.status["system_ready"] = True
                self._event_buzzer_patterns("SENSORS_READY")
                self._log("System ready with minimum required sensors")
                return True
            else:
                self._log("No required sensors working", "ERROR")
                return False
        else:
            self._log("Custom sensor modules not available", "ERROR")
            return False

    def _collect_sensor_data(self):
        """Collect and format sensor data with improved error handling"""
        data = {
            "timestamp": time.time(),
            "temperature": None,
            "pressure": None,
            "altitude": None,
            "ax": None, "ay": None, "az": None,
            "gx": None, "gy": None, "gz": None,
            "latitude": None, "longitude": None,
            "vertical_velocity": None
        }
        
        try:
            if self.status["mpu"]["working"]:
                accel = self.mpu.get_acceleration()
                gyro = self.mpu.get_rotation()
                data.update({
                    "ax": accel[0], "ay": accel[1], "az": accel[2],
                    "gx": gyro[0], "gy": gyro[1], "gz": gyro[2]
                })
            
                try:
                    if self.status["mpu"]["working"]:
                        accel = self.mpu.get_acceleration()
                        gyro = self.mpu.get_rotation()
                        data.update({
                            "ax": accel[0], "ay": accel[1], "az": accel[2],
                            "gx": gyro[0], "gy": gyro[1], "gz": gyro[2]
                        })
                    
                    if self.status["bme"]["working"]:
                        data["temperature"] = self.bme.read_temperature()
                        data["pressure"] = self.bme.read_pressure() / 100.0  # Convert to hPa
                        altitude = self.bme.read_altitude()
                        
                        if altitude is not None:
                            data["altitude"] = round(altitude, 2)
                            # Calculate vertical velocity if we have previous altitude
                            if hasattr(self, 'last_altitude') and self.last_altitude is not None:
                                data["vertical_velocity"] = (altitude - self.last_altitude) / 0.1  # Assuming 10Hz
                            self._check_flight_events(data["altitude"])
                    
                    if self.status["gps"]["working"]:
                        pos = self.gps.get_position()
                        if pos:
                            data.update({
                                "latitude": pos[0],
                                "longitude": pos[1]
                            })
                            
                except Exception as e:
                    self._log(f"Error collecting sensor data: {str(e)}", "ERROR")

            
            if self.status["gps"]["working"]:
                pos = self.gps.get_position()
                if pos:
                    data.update({
                        "latitude": pos[0],
                        "longitude": pos[1]
                    })
                    
        except Exception as e:
            self._log(f"Error collecting sensor data: {str(e)}", "ERROR")
        
        return data

    def _get_timestamp(self):
        """Create a formatted timestamp string"""
        t = time.localtime()
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            t[0], t[1], t[2], t[3], t[4], t[5]
        )

    def _log(self, message, level="INFO"):
        """Log messages with timestamp and level"""
        # Use simple timestamp since MicroPython time doesn't have strftime
        timestamp = time.time()
        log_message = f"[{timestamp}] {level}: {message}"
        print(log_message)
        self._debug_messages.append(log_message)

    def _fatal_error(self, message):
        """Handle fatal errors"""
        self._event_buzzer_patterns("ERROR")
        self._log(message, "FATAL")
        if hasattr(self, 'led_red'):
            try:
                self.led_red.on()
            except:
                pass
        raise RuntimeError(message)
    def _init_logging(self):
        """Initialize logging system"""
        self._debug_messages = [];
    
    def _safe_shutdown(self):
        """Safely shutdown the system"""
        self._event_buzzer_patterns("SHUTDOWN")
        self._log("Initiating safe shutdown")
        self._log_event("Shutdown", "System shutdown initiated")
        
        # Save any remaining buffered data
        if self.data_buffer:
            for data in self.data_buffer:
                self._save_data(data)
            self.data_buffer = []
        
        # Turn off LEDs
        if hasattr(self, 'led_red'):
            self.led_red.off()
        if hasattr(self, 'led_green'):
            self.led_green.off()
        
        self.state = FlightStates.SHUTDOWN
        
    def _blink_pattern(self, led, pattern):
        """Blink LED in specified pattern"""
        for duration in pattern:
            led.toggle()
            sleep(duration)
        led.off()
        
    def _check_flight_events(self, current_altitude):
        """
        Enhanced flight events detection using altitude changes and acceleration data
        Detects: Apogee, Descent initiation, and Landing impact
        """
        if self.last_altitude is None:
            self.last_altitude = current_altitude
            self.altitude_history = []  # Keep last 10 readings for trend analysis
            self.descent_confidence = 0
            self.landing_confidence = 0
            return

        # Keep a rolling window of altitude measurements
        self.altitude_history.append(current_altitude)
        if len(self.altitude_history) > 10:
            self.altitude_history.pop(0)

        # Calculate vertical velocity (m/s) and acceleration
        time_delta = 0.1  # Assuming 10Hz sampling rate
        velocity = (current_altitude - self.last_altitude) / time_delta
        
        # Get acceleration data if available
        vertical_acceleration = None
        if self.status["mpu"]["working"]:
            try:
                accel = self.mpu.get_acceleration()
                vertical_acceleration = accel[2]  # Z-axis acceleration
            except:
                pass

        # Apogee and Descent Detection
        if self.state == FlightStates.ASCENT and not self.descent_detected:
            # Calculate altitude trend over last 10 readings
            if len(self.altitude_history) >= 5:
                recent_trend = sum(1 for i in range(len(self.altitude_history)-1) 
                                if self.altitude_history[i] > self.altitude_history[i+1])
                
                # Check for consistent downward trend
                if recent_trend >= 4:  # 4 out of 5 readings showing descent
                    self.descent_confidence += 1
                else:
                    self.descent_confidence = max(0, self.descent_confidence - 1)

                # Confirm descent with multiple indicators
                if (velocity < -1.0 and self.descent_confidence >= 3) or \
                (vertical_acceleration is not None and vertical_acceleration < -0.5):
                    self._event_buzzer_patterns("APOGEE")
                    self.state = FlightStates.DESCENT
                    self.descent_detected = True
                    max_altitude = max(self.altitude_history)
                    self._log_event("Apogee Detected", 
                                f"Max altitude: {max_altitude}m, Velocity: {velocity:.2f}m/s")

        # Landing Detection
        elif self.state == FlightStates.DESCENT:
            if current_altitude < 4:  # Below 4 meters
                # Check for impact using acceleration if available
                if vertical_acceleration is not None:
                    if abs(vertical_acceleration) > 3.0:  # Strong impact detected
                        self._event_buzzer_patterns("LANDING")
                        self.state = FlightStates.LANDED
                        self._log_event("Impact Detected", 
                                    f"Final altitude: {current_altitude}m, Impact acceleration: {vertical_acceleration}g")
                        return

                # Backup method: check for stable low altitude
                altitude_variance = 0
                if len(self.altitude_history) >= 5:
                    mean_alt = sum(self.altitude_history[-5:]) / 5
                    altitude_variance = sum((x - mean_alt) ** 2 for x in self.altitude_history[-5:]) / 5

                if altitude_variance < 0.25 and velocity > -0.5:  # Very stable altitude
                    self.landing_confidence += 1
                else:
                    self.landing_confidence = max(0, self.landing_confidence - 1)

                if self.landing_confidence >= 5:  # Require 5 consecutive stable readings
                    self.state = FlightStates.LANDED
                    self._log_event("Landing Detected", 
                                f"Final altitude: {current_altitude}m, Velocity: {velocity:.2f}m/s")

        self.last_altitude = current_altitude

    def _save_data(self, data):
        """Save data to local storage with improved error handling"""
        if not self.current_file:
            return
        
        try:
            # Format data as CSV row
            row = (f"{data['timestamp']},{data['temperature']},{data['pressure']},"
                  f"{data['altitude']},{data['ax']},{data['ay']},{data['az']},"
                  f"{data['gx']},{data['gy']},{data['gz']},{data['latitude']},"
                  f"{data['longitude']}\n")
            
            # Append to file
            with open(self.current_file, 'a') as f:
                f.write(row)
            
            # Print current readings to terminal with proper formatting
            print("\nCurrent Readings:")
            print(f"Temperature: {data['temperature']}°C" if data['temperature'] is not None else "Temperature: No reading")
            print(f"Pressure: {data['pressure']} hPa" if data['pressure'] is not None else "Pressure: No reading")
            print(f"Altitude: {data['altitude']} m" if data['altitude'] is not None else "Altitude: No reading")
            print(f"Acceleration (x,y,z): {data['ax']}, {data['ay']}, {data['az']}")
            if data['latitude'] is not None and data['longitude'] is not None:
                print(f"GPS: {data['latitude']}, {data['longitude']}")
            print("-------------------")
            
        except Exception as e:
            self._log(f"Error saving data: {str(e)}", "ERROR")
            self._log_event("Data Save Error", f"Failed to save data: {str(e)}")

    def main_loop(self):
        """Main program loop with enhanced error handling and state management"""
        self._log("Starting main loop")
        self._log_event("Main Loop", "Program execution started")
        
        last_button_press = 0
        button_hold_start = None
        last_status_print = 0
        status_interval = 10  # Print status every 10 seconds
        
        while True:
            try:
                current_time = time.time()
                
                # Button handling with improved hold detection
                if not self.button.value():
                    if button_hold_start is None:
                        button_hold_start = current_time
                    elif current_time - button_hold_start > 3:  # 3 second hold
                        self._log_event("Button Hold", "3-second shutdown triggered")
                        self._safe_shutdown()
                        break
                else:
                    if button_hold_start is not None:
                        if current_time - last_button_press > 0.5:  # Debounce
                            last_button_press = current_time
                            self._handle_button_press()
                    button_hold_start = None
                
                # Data collection in appropriate states
                if self.state in [FlightStates.ASCENT, FlightStates.DESCENT]:
                    data = self._collect_sensor_data()
                    self.data_buffer.append(data)
                    
                    # Periodic status update
                    if current_time - last_status_print >= status_interval:
                        self._log(f"Current State: {FlightStates.get_state_name(self.state)}")
                        if self.last_altitude is not None:
                            self._log(f"Current Altitude: {self.last_altitude}m")
                        last_status_print = current_time
                    
                    # Save data periodically
                    if current_time - self.last_save_time >= self.save_interval:
                        for buffered_data in self.data_buffer:
                            self._save_data(buffered_data)
                        self.data_buffer = []
                        self.last_save_time = current_time
                
                # Check for landing state transition
                if self.state == FlightStates.DESCENT and self.last_altitude is not None:
                    if self.last_altitude < 10:  # Below 10 meters
                        consecutive_low_readings = getattr(self, '_consecutive_low_readings', 0) + 1
                        if consecutive_low_readings > 5:  # 5 consecutive low readings
                            self.state = FlightStates.LANDED
                            self._log_event("Landing Confirmed", f"Final altitude: {self.last_altitude}m")
                        self._consecutive_low_readings = consecutive_low_readings
                    else:
                        self._consecutive_low_readings = 0
                
                # State indicator
                self._update_leds()
                sleep(0.1)
                
            except Exception as e:
                self._log(f"Error in main loop: {str(e)}", "ERROR")
                self._log_event("Main Loop Error", str(e))
                self._blink_pattern(self.led_red, [0.1, 0.1, 0.1])
                sleep(1)

    def _handle_button_press(self):
        """Handle button press with state transitions and event logging"""
        if self.state == FlightStates.WAITING_START:
            self._log_event("Button Press", "Initializing sensors")
            if self.init_sensors():
                self._event_buzzer_patterns("SENSORS_READY")
                self.state = FlightStates.READY
                self._log_event("State Change", "System ready for flight")
                print("\n=== System Ready ===")
                print("Press button again to start data collection")
                print("===================\n")
            else:
                self._log_event("Error", "Sensor initialization failed")
                
        elif self.state == FlightStates.READY:
            self._event_buzzer_patterns("FLIGHT_START")
            self.state = FlightStates.ASCENT
            self._log_event("Flight Start", "Data collection initiated")
            print("\n=== Data Collection Started ===")
            print("Hold button for 3 seconds to stop and shutdown")
            print("===========================\n")

    def _update_leds(self):
        """Update LED states based on current system state with improved patterns"""
        if self.state == FlightStates.WAITING_START:
            # Slow blink for waiting
            self.led_red.toggle()
            self.led_green.off()
            sleep(0.5)
            
        elif self.state == FlightStates.READY:
            # Solid green for ready
            self.led_green.on()
            self.led_red.off()
            
        elif self.state == FlightStates.ASCENT:
            # Alternating fast blink for ascent
            self.led_green.toggle()
            self.led_red.off()
            sleep(0.2)
            
        elif self.state == FlightStates.DESCENT:
            # Both LEDs alternating for descent
            self.led_green.toggle()
            self.led_red.value(not self.led_green.value())
            sleep(0.2)
            
        elif self.state == FlightStates.LANDED:
            # Quick green pulses for landed
            self.led_green.on()
            sleep(0.1)
            self.led_green.off()
            sleep(0.9)
            self.led_red.off()

def main():
    """Main function with comprehensive error handling and logging"""
    try:
        print("\n=== CanSat Flight Computer ===")
        print("Version: 5.0")
        print("Starting up...")
        print("===========================\n")
        
        cansat = CanSat()
        cansat.main_loop()
        
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
        try:
            cansat._log_event("System Exit", "Program terminated by user")
            cansat._safe_shutdown()
        except:
            pass
        
            
    except Exception as e:
        print(f"Critical error in main: {str(e)}")
        try:
            # Log the critical error
            with open("error_log.txt", "a") as f:
                f.write(f"{time.time()}: Critical error - {str(e)}\n")
            
            # Last resort - basic LED error indication
            error_led = Pin(PIN_CONFIG['LED']['RED'], Pin.OUT)
            while True:
                error_led.toggle()
                sleep(0.2)
        except:
            print("Fatal error - cannot recover")

if __name__ == "__main__":
    main()
    
