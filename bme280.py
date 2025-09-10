"""
Enhanced BME280 MicroPython driver for RP2040 with improved accuracy and error handling.
"""
from machine import Pin, I2C
import time
import math

class BME280:
    # BME280 default address
    BME280_I2CADDR = 0x76
    BME280_ALT_ADDR = 0x77  # Alternate address for some modules

    # Operating Modes
    SLEEP_MODE = 0b00
    FORCED_MODE = 0b01
    NORMAL_MODE = 0b11

    # Oversample settings
    OVERSAMPLE_SKIP = 0b000
    OVERSAMPLE_X1 = 0b001
    OVERSAMPLE_X2 = 0b010
    OVERSAMPLE_X4 = 0b011
    OVERSAMPLE_X8 = 0b100
    OVERSAMPLE_X16 = 0b101

    def __init__(self, i2c, address=None, sea_level_pressure=1013.25, debug=False):
        """
        Initialize BME280 sensor with advanced calibration and error handling.
        
        Args:
            i2c: Initialized I2C object
            address: I2C address (default is to auto-detect)
            sea_level_pressure: Standard sea level pressure in hPa
            debug: Enable verbose debug output
        """
        self.i2c = i2c
        self.debug = debug
        self.sea_level_pressure = sea_level_pressure
        
        # Auto-detect address if not provided
        if address is None:
            devices = i2c.scan()
            if self.BME280_I2CADDR in devices:
                self.address = self.BME280_I2CADDR
            elif self.BME280_ALT_ADDR in devices:
                self.address = self.BME280_ALT_ADDR
            else:
                raise RuntimeError("BME280 not found on I2C bus")
        else:
            self.address = address
        
        if self.debug:
            print(f"Using BME280 at address 0x{self.address:02x}")
        
        # Initialize calibration values
        self.ground_pressure = None
        self.ground_altitude = None
        self.ground_altitude_offset = 0
        self.t_fine = 0
        
        # Store multiple ground level readings for more accurate calibration
        self._ground_pressure_readings = []
        self._ground_altitude_readings = []
        
        # Validate device presence and ID
        try:
            chip_id = self._safe_read_byte(0xD0)
            if chip_id != 0x60:
                raise RuntimeError(f'Invalid BME280 Chip ID: 0x{chip_id:02x}')
            print(f"BME280 found with chip ID: 0x{chip_id:02x}")
        except Exception as e:
            raise RuntimeError(f"BME280 Initialization Error: {str(e)}")
        
        # Reset the device
        self._soft_reset()
        time.sleep(0.1)  # Wait for reset to complete
        
        # Load calibration data
        self._load_calibration()
        
        # Configure sensor with optimal settings
        self._configure_sensor()
        
        # Wait for first measurement to complete
        time.sleep(0.1)

    def _soft_reset(self):
        """Perform soft reset of the device"""
        try:
            self.i2c.writeto_mem(self.address, 0xE0, b'\xB6')
            time.sleep(0.2)  # Wait for reset to complete
        except Exception as e:
            raise RuntimeError(f"Soft reset failed: {str(e)}")

    def _safe_read_byte(self, register, retries=3):
        """Safe byte reading with error handling and retries"""
        for attempt in range(retries):
            try:
                return self.i2c.readfrom_mem(self.address, register, 1)[0]
            except Exception as e:
                if attempt == retries - 1:
                    raise RuntimeError(f"Failed to read register 0x{register:02x}: {str(e)}")
                time.sleep(0.1)

    def _load_calibration(self):
        """Load sensor calibration data with comprehensive error handling"""
        try:
            # Temperature compensation
            self.dig_T1 = self._read_word_unsigned(0x88)
            self.dig_T2 = self._read_word_signed(0x8A)
            self.dig_T3 = self._read_word_signed(0x8C)

            # Pressure compensation
            self.dig_P1 = self._read_word_unsigned(0x8E)
            self.dig_P2 = self._read_word_signed(0x90)
            self.dig_P3 = self._read_word_signed(0x92)
            self.dig_P4 = self._read_word_signed(0x94)
            self.dig_P5 = self._read_word_signed(0x96)
            self.dig_P6 = self._read_word_signed(0x98)
            self.dig_P7 = self._read_word_signed(0x9A)
            self.dig_P8 = self._read_word_signed(0x9C)
            self.dig_P9 = self._read_word_signed(0x9E)

            if self.debug:
                print("Calibration data:")
                print(f"T1={self.dig_T1}, T2={self.dig_T2}, T3={self.dig_T3}")
                print(f"P1={self.dig_P1}, P2={self.dig_P2}, P3={self.dig_P3}")
                print(f"P4={self.dig_P4}, P5={self.dig_P5}, P6={self.dig_P6}")
                print(f"P7={self.dig_P7}, P8={self.dig_P8}, P9={self.dig_P9}")

            # Check for valid calibration data - these are typical ranges
            if not (0 < self.dig_T1 < 65535 and -32768 < self.dig_T2 < 32767 and -32768 < self.dig_T3 < 32767):
                print("WARNING: Temperature calibration values out of expected range!")
                print(f"T1={self.dig_T1}, T2={self.dig_T2}, T3={self.dig_T3}")
                
                # Apply fallback calibration values - these are typical values
                self.dig_T1 = 27504
                self.dig_T2 = 26435
                self.dig_T3 = -1000
                print("Applied fallback temperature calibration values")

            if not (0 < self.dig_P1 < 65535):
                print("WARNING: Pressure calibration values out of expected range!")
                
                # Apply fallback calibration values - these are typical values
                self.dig_P1 = 36477
                self.dig_P2 = -10685
                self.dig_P3 = 3024
                self.dig_P4 = 2855
                self.dig_P5 = 140
                self.dig_P6 = -7
                self.dig_P7 = 15500
                self.dig_P8 = -14600
                self.dig_P9 = 6000
                print("Applied fallback pressure calibration values")

            print("Calibration data loaded successfully")
        except Exception as e:
            raise RuntimeError(f"Failed to load calibration data: {str(e)}")

    def _configure_sensor(self):
        """Configure sensor with optimal settings for flight data"""
        try:
            # Set the config register
            config = 0
            config |= 0b001 << 5  # Set standby time to 62.5ms
            config |= 0b100 << 2  # Set filter coefficient to 16
            self.i2c.writeto_mem(self.address, 0xF5, bytes([config]))

            # Set ctrl_meas register
            ctrl_meas = 0
            ctrl_meas |= self.OVERSAMPLE_X2 << 5  # Temperature oversampling x2
            ctrl_meas |= self.OVERSAMPLE_X16 << 2  # Pressure oversampling x16
            ctrl_meas |= self.NORMAL_MODE  # Set normal mode
            self.i2c.writeto_mem(self.address, 0xF4, bytes([ctrl_meas]))

            print("Sensor configured for optimal data collection")
        except Exception as e:
            raise RuntimeError(f"Sensor configuration failed: {str(e)}")

    def calibrate_ground_level(self, samples=10, delay=0.1):
        """
        Calibrate ground level pressure and establish baseline altitude with multiple samples.
        
        Args:
            samples: Number of pressure readings to average
            delay: Delay between readings in seconds
        """
        print("Starting ground level calibration...")
        self._ground_pressure_readings = []
        total_altitude = 0
        valid_samples = 0
        
        for i in range(samples):
            try:
                pressure = self.read_pressure()
                if pressure is not None:
                    pressure_hpa = pressure / 100.0  # Convert to hPa
                    
                    # Validate pressure reading
                    if 800 <= pressure_hpa <= 1200:  # Valid pressure range
                        self._ground_pressure_readings.append(pressure_hpa)
                        
                        # Calculate absolute altitude from sea level
                        abs_altitude = self._calculate_altitude(pressure_hpa, self.sea_level_pressure)
                        total_altitude += abs_altitude
                        
                        valid_samples += 1
                        print(f"Calibration sample {valid_samples}/{samples}: "
                              f"Pressure={pressure_hpa:.1f}hPa, "
                              f"Abs. Altitude={abs_altitude:.1f}m")
                    else:
                        print(f"Invalid pressure reading ignored: {pressure_hpa:.1f} hPa")
                
                time.sleep(delay)
            except Exception as e:
                print(f"Error during calibration sample {i+1}: {str(e)}")
        
        if valid_samples >= 3:  # At least 3 valid readings
            # Calculate average ground pressure
            self.ground_pressure = sum(self._ground_pressure_readings) / len(self._ground_pressure_readings)
            
            # Calculate and store ground altitude offset
            self.ground_altitude_offset = total_altitude / valid_samples
            
            print(f"Ground calibration successful:")
            print(f"Ground Pressure: {self.ground_pressure:.1f} hPa")
            print(f"Ground Altitude Offset: {self.ground_altitude_offset:.1f}m")
            return True
        else:
            print("Ground calibration failed - using sea level as reference")
            self.ground_pressure = self.sea_level_pressure
            self.ground_altitude_offset = 0
            return False

    def read_raw_temp(self):
        """Read raw temperature data from registers with improved error handling"""
        try:
            # Read temperature registers with proper bit manipulation
            msb = self._safe_read_byte(0xFA)  # Temperature MSB
            lsb = self._safe_read_byte(0xFB)  # Temperature LSB
            xlsb = self._safe_read_byte(0xFC)  # Temperature XLSB
            
            # Correct bit shifting for 20-bit temperature value
            raw_temp = ((msb << 16) | (lsb << 8) | xlsb) >> 4
            
            if self.debug:
                print(f"Raw temperature registers: MSB=0x{msb:02x}, LSB=0x{lsb:02x}, XLSB=0x{xlsb:02x}")
                print(f"Raw temperature value: {raw_temp}")
                
            return raw_temp
        except Exception as e:
            print(f"Error reading raw temperature: {str(e)}")
            return None

    def read_temperature(self, debug=False):
        """
        Read temperature with enhanced accuracy and error handling.
        
        Args:
            debug: If True, print detailed calibration and calculation steps
        
        Returns temperature in degrees Celsius.
        """
        try:
            raw_temp = self.read_raw_temp()
            if raw_temp is None:
                return None

            # First conversion attempt using BME280 datasheet algorithm
            var1 = ((raw_temp / 16384.0) - (self.dig_T1 / 1024.0)) * self.dig_T2
            var2 = (((raw_temp / 131072.0) - (self.dig_T1 / 8192.0)) * 
                   ((raw_temp / 131072.0) - (self.dig_T1 / 8192.0)) * self.dig_T3)
            
            # Store t_fine for pressure compensation
            self.t_fine = int(var1 + var2)
            
            # Calculate temperature
            temp = (var1 + var2) / 5120.0
            
            if debug or self.debug:
                print(f"Raw temp: {raw_temp}")
                print(f"var1: {var1}, var2: {var2}, t_fine: {self.t_fine}")
                print(f"Calculated temp: {temp}°C")

            # Validate temperature is within reasonable range
            if -40 <= temp <= 85:
                return round(temp, 2)
            else:
                # Retry with an alternative calculation method
                print(f"Warning: Temperature {temp}°C outside valid range, trying fallback calculation")
                
                # Simpler alternative calculation
                var1 = (raw_temp / 16384.0 - self.dig_T1 / 1024.0) * self.dig_T2
                var2 = raw_temp / 131072.0 - self.dig_T1 / 8192.0
                var2 = var2 * var2 * self.dig_T3
                self.t_fine = int(var1 + var2)
                temp = (self.t_fine) / 5120.0
                
                if -40 <= temp <= 85:
                    print(f"Fallback temperature calculation successful: {temp}°C")
                    return round(temp, 2)
                else:
                    print(f"Fallback temperature still invalid: {temp}°C")
                    return None
                
        except Exception as e:
            print(f"Temperature reading error: {str(e)}")
            return None

    def read_raw_pressure(self):
        """Read raw pressure value from the sensor"""
        try:
            # Read pressure registers
            msb = self._safe_read_byte(0xF7)
            lsb = self._safe_read_byte(0xF8)
            xlsb = self._safe_read_byte(0xF9)
            
            # Combine readings into a 20-bit value
            raw_pressure = ((msb << 16) | (lsb << 8) | xlsb) >> 4
            
            if self.debug:
                print(f"Raw pressure registers: MSB=0x{msb:02x}, LSB=0x{lsb:02x}, XLSB=0x{xlsb:02x}")
                print(f"Raw pressure value: {raw_pressure}")
                
            return raw_pressure
        except Exception as e:
            print(f"Error reading raw pressure: {str(e)}")
            return None
        
    def read_pressure(self):
        """Read pressure with high-precision compensation"""
        try:
            # Update t_fine value - only if temperature read fails, we try with default t_fine
            temp = self.read_temperature()
            if temp is None:
                # Use a default t_fine value if temperature read fails
                self.t_fine = 100000  # A moderate value that should allow pressure calculation
                print("Warning: Using default t_fine value for pressure calculation")
            
            # Read raw pressure
            raw_pressure = self.read_raw_pressure()
            if raw_pressure is None:
                return None

            # Pressure compensation (datasheet algorithm)
            var1 = self.t_fine / 2.0 - 64000.0
            var2 = var1 * var1 * self.dig_P6 / 32768.0
            var2 = var2 + var1 * self.dig_P5 * 2.0
            var2 = var2 / 4.0 + self.dig_P4 * 65536.0
            var1 = (self.dig_P3 * var1 * var1 / 524288.0 + self.dig_P2 * var1) / 524288.0
            var1 = (1.0 + var1 / 32768.0) * self.dig_P1
            
            if var1 == 0:
                return None  # Avoid division by zero
            
            pressure = 1048576.0 - raw_pressure
            pressure = ((pressure - var2 / 4096.0) * 6250.0) / var1
            var1 = self.dig_P9 * pressure * pressure / 2147483648.0
            var2 = pressure * self.dig_P8 / 32768.0
            pressure = pressure + (var1 + var2 + self.dig_P7) / 16.0
            
            # Validate pressure is within reasonable range
            if 30000 <= pressure <= 120000:  # 300-1200 hPa
                return round(pressure, 2)  # Return pressure in Pa
            else:
                print(f"Warning: Pressure {pressure/100:.2f} hPa outside valid range")
                return None
                
        except Exception as e:
            print(f"Pressure reading error: {str(e)}")
            return None

    def read_altitude(self):
        """
        Calculate altitude relative to calibrated ground level.
        Returns relative altitude in meters from ground calibration point.
        """
        try:
            pressure = self.read_pressure()
            if pressure is None or pressure <= 0:
                return None
                
            current_pressure = pressure / 100.0  # Convert Pa to hPa
            
            # Calculate absolute altitude using current pressure
            if self.ground_pressure is None or self.ground_pressure <= 0:
                # If not calibrated, use sea level as reference
                absolute_altitude = self._calculate_altitude(current_pressure, self.sea_level_pressure)
                relative_altitude = absolute_altitude  # No offset if not calibrated
                if self.debug:
                    print("Using uncalibrated altitude (from sea level)")
            else:
                # Calculate altitude relative to ground pressure
                absolute_altitude = self._calculate_altitude(current_pressure, self.sea_level_pressure)
                relative_altitude = absolute_altitude - self.ground_altitude_offset
                
            return round(relative_altitude, 2)
            
        except Exception as e:
            print(f"Altitude calculation error: {str(e)}")
            return None
        
    def _calculate_altitude(self, current_pressure, reference_pressure):
        """
        Calculate altitude using the international barometric formula.
        
        Args:
            current_pressure: Current atmospheric pressure in hPa
            reference_pressure: Reference pressure in hPa
        
        Returns:
            Altitude in meters
        """
        if current_pressure <= 0 or reference_pressure <= 0:
            raise ValueError("Invalid pressure values")
            
        return 44330.0 * (1.0 - pow(current_pressure / reference_pressure, 0.1903))

    def get_altitude_stats(self):
        """
        Get current altitude calculation parameters for debugging.
        """
        return {
            "ground_pressure": self.ground_pressure,
            "ground_altitude_offset": self.ground_altitude_offset,
            "sea_level_pressure": self.sea_level_pressure,
            "t_fine": self.t_fine
        }
        
    def read_all(self):
        """
        Read all sensors and return values in a dictionary.
        """
        temp = self.read_temperature()
        pressure_pa = self.read_pressure()
        altitude = self.read_altitude()
        
        if pressure_pa is not None:
            pressure_hpa = pressure_pa / 100.0
        else:
            pressure_hpa = None
            
        return {
            "temperature": temp,
            "pressure": pressure_hpa,
            "altitude": altitude
        }

    def _read_word_unsigned(self, register):
        """Read unsigned 16-bit word"""
        try:
            high = self._safe_read_byte(register)
            low = self._safe_read_byte(register + 1)
            return (high << 8) + low
        except Exception as e:
            print(f"Error reading unsigned word at 0x{register:02x}: {str(e)}")
            return 0

    def _read_word_signed(self, register):
        """Read signed 16-bit word"""
        try:
            value = self._read_word_unsigned(register)
            if value >= 0x8000:
                value -= 0x10000
            return value
        except Exception as e:
            print(f"Error reading signed word at 0x{register:02x}: {str(e)}")
            return 0