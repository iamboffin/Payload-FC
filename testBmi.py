# Improved BME280 Test Program for Raspberry Pi Pico
# Tests temperature, pressure, and altitude readings with robust error handling

import time
from machine import Pin, I2C
# Import the BME280 class
# Note: Save the fixed module as bme280.py on your Pico
from bme280 import BME280

# Define I2C pins (use the default I2C0 on the Pico)
i2c_sda = Pin(18)  # GP0 - Pin 1
i2c_scl = Pin(19)  # GP1 - Pin 2

# Initialize I2C with a reasonable frequency
i2c = I2C(1, sda=i2c_sda, scl=i2c_scl, freq=100000)

# Check for available I2C devices
print("\n=== BME280 Test Program ===")
print("Scanning I2C bus...")
devices = i2c.scan()
if devices:
    print(f"Found {len(devices)} I2C device(s):")
    for device in devices:
        print(f"  - Device address: 0x{device:02x}")
else:
    print("No I2C devices found. Check your connections!")

# Try to initialize the BME280 sensor
try:
    print("\nInitializing BME280 sensor...")
    # Enable debug mode for the first reading to help diagnose any issues
    bme = BME280(i2c, debug=True)
    print("BME280 initialized successfully!")
    
    # First read to verify all functions work
    print("\nTesting initial readings:")
    data = bme.read_all()
    if data["temperature"] is not None:
        print(f"✓ Temperature: {data['temperature']}°C")
    else:
        print("✗ Temperature reading failed")
        
    if data["pressure"] is not None:
        print(f"✓ Pressure: {data['pressure']} hPa")
    else:
        print("✗ Pressure reading failed")
        
    if data["altitude"] is not None:
        print(f"✓ Altitude: {data['altitude']} m (uncalibrated)")
    else:
        print("✗ Altitude calculation failed")
    
    # If initial readings successful, continue with calibration
    if data["temperature"] is not None or data["pressure"] is not None:
        # Calibrate the sensor for ground level altitude
        print("\nCalibrating ground level...")
        calibration_success = bme.calibrate_ground_level(samples=3, delay=1.0)
        if calibration_success:
            print("Ground level calibration completed successfully")
        else:
            print("Ground level calibration failed, using sea level as reference")
        
        # Optional: If you have a known reference temperature, you can recalibrate
        # For example, if you know the current temperature is 23.5°C:
        # print("\nPerforming temperature recalibration...")
        # bme.recalibrate_temperature_offset(23.5)
        
        # Main measurement loop
        print("\nStarting continuous measurements (Press Ctrl+C to stop)...")
        print("-" * 50)
        print("Temperature(°C) | Pressure(hPa) | Altitude(m)")
        print("-" * 50)
        
        sample_count = 0
        error_count = 0
        
        # Turn off debug mode for continuous readings
        bme.debug = False
        
        try:
            while True:
                # Read sensor data
                sample_count += 1
                data = bme.read_all()
                
                # Format and display readings
                if None not in (data["temperature"], data["pressure"], data["altitude"]):
                    print(f"{data['temperature']:13.2f} | {data['pressure']:12.2f} | {data['altitude']:10.2f}")
                    error_count = 0  # Reset error count when successful
                else:
                    print("Error reading sensor data:")
                    if data["temperature"] is None:
                        print("- Temperature reading failed")
                    if data["pressure"] is None:
                        print("- Pressure reading failed")
                    if data["altitude"] is None:
                        print("- Altitude calculation failed")
                    
                    error_count += 1
                    
                    # If we have multiple consecutive errors, turn debug back on
                    if error_count >= 3:
                        bme.debug = True
                        print("Enabling debug mode due to repeated errors")
                        print("Stats:", bme.get_altitude_stats())
                
                # Wait before next reading
                time.sleep(2)
                
                # Every 10 samples, print a status message
                if sample_count % 10 == 0:
                    print(f"Completed {sample_count} readings")
                    
        except KeyboardInterrupt:
            print("\nStopped by user")
    else:
        print("Initial sensor readings failed. Check connections and try again.")
        
except Exception as e:
    print(f"Setup Error: {str(e)}")
