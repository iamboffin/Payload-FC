# Pioneer Flight Computer

A comprehensive flight computer system for CanSat missions, built on the Raspberry Pi Pico platform. This system provides robust sensor integration, data logging, and automated flight event detection capabilities.

## Features

- Multi-state flight management system
- Comprehensive sensor integration (MPU6050, BME280, NEO-6M GPS)
- Automatic flight event detection (launch, apogee, landing)
- Redundant data storage with buffering
- LED status indication system
- Button-based control interface
- Extensive error handling and logging
- Safe shutdown capabilities

## Hardware Requirements

### Core Components
- Raspberry Pi Pico
- MPU6050 (Accelerometer/Gyroscope)
- BME280 (Temperature/Pressure/Humidity)
- NEO-6M GPS Module
- 2x LEDs (Green and Red)
- Push Button
- Power Supply (3.3V)

### Pin Configuration

| Component | Pin(s)           | Configuration |
|-----------|------------------|---------------|
| MPU6050   | SDA=20, SCL=21  | I2C0         |
| BME280    | SDA=18, SCL=19  | I2C1         |
| GPS       | TX=8, RX=9      | UART1        |
| Button    | GPIO 22         | Pull-up      |
| Green LED | GPIO 2          | Output       |
| Red LED   | GPIO 3          | Output       |

## System States

The flight computer operates through the following states:

1. **WAITING_START** (-1)
   - Initial state after power-on
   - Waiting for sensor initialization
   - Red LED slow blinking

2. **IDLE** (0)
   - System initialized
   - Waiting for operations
   - LEDs off

3. **PREFLIGHT** (1)
   - System checks in progress
   - Sensor verification

4. **CALIBRATION** (2)
   - Sensor calibration state
   - LED indicators active

5. **READY** (3)
   - Ready for flight operations
   - Solid green LED

6. **ASCENT** (4)
   - Active data collection
   - Flight in progress
   - Green LED toggling

7. **DESCENT** (5)
   - Descent phase detected
   - Alternating LED patterns

8. **LANDED** (6)
   - Landing detected
   - Quick green LED pulses

9. **SHUTDOWN** (7)
   - Safe system shutdown
   - LEDs powered down

## Data Collection

### Sensor Data
The system collects and logs the following data:
- Timestamp
- Temperature (°C)
- Pressure (hPa)
- Altitude (m)
- Acceleration (x, y, z)
- Gyroscope readings (x, y, z)
- GPS coordinates (latitude, longitude)

### Data Files
Two main file types are generated:
1. **Data File** (`data_[timestamp].csv`)
   - Contains all sensor readings
   - Comma-separated format
   - Headers included

2. **Event File** (`events_[timestamp].csv`)
   - Logs system events and state changes
   - Includes timestamps and details
   - Records flight milestones

## Usage Instructions

### Initial Setup
1. Connect all sensors according to the pin configuration
2. Power up the system
3. Wait for initial LED sequence

### Flight Operation
1. Press button to initialize sensors (WAITING_START → READY)
2. Press again to start data collection (READY → ASCENT)
3. System automatically detects and logs flight events
4. Hold button for 3 seconds to trigger safe shutdown

### Data Retrieval
- Data files are saved continuously during flight
- Files can be accessed after landing
- Both sensor data and event logs available

## Error Handling

The system includes comprehensive error handling:
- Sensor initialization failures
- Data storage errors
- Runtime exceptions
- LED error indicators
- Event logging of all errors

## Development Notes

### Dependencies
The system requires the following custom modules:
- `mpu6050.py` - MPU6050 sensor interface
- `bme280.py` - BME280 sensor interface
- `neo6m.py` - NEO-6M GPS interface
- `kalman.py` - Kalman filter implementation

### Key Methods
- `init_sensors()` - Initializes all sensor hardware
- `_collect_sensor_data()` - Gathers sensor readings
- `_check_flight_events()` - Monitors for state changes
- `main_loop()` - Primary program execution
- `_safe_shutdown()` - Handles system shutdown

## Contributing

Please follow these guidelines when contributing:
1. Fork the repository
2. Create a feature branch
3. Submit pull requests with detailed descriptions
4. Ensure all tests pass
5. Update documentation as needed


## Safety Notes

- Always verify power supply connections
- Handle components with ESD protection
- Ensure proper sensor calibration
- Follow local regulations for launches
- Maintain backup power systems

## Troubleshooting

### Common Issues
1. **LEDs Not Responding**
   - Check pin connections
   - Verify power supply
   - Review error logs

2. **Sensor Failures**
   - Verify I2C connections
   - Check voltage levels
   - Review initialization logs

3. **Data Collection Issues**
   - Check storage space
   - Verify file permissions
   - Monitor system logs

### LED Status Reference

| Pattern | Meaning |
|---------|---------|
| **Red Slow Blink** | Waiting for initialization |
| **Solid Green**| System ready |
| **Green Toggle** | Data collection active |
| **Both Alternating** | Descent phase |
| **Quick Green Pulse** | Landed state |

#### Buzzer Event Patterns

| Event Type | Pattern | Description |
|------------|---------|-------------|
| **STARTUP** | 3 short beeps | System initialization |
| **SENSORS_READY** | 2 medium beeps | Sensors successfully initialized |
| **FLIGHT_START** | 3 medium beeps | Data collection initiated |
| **APOGEE** | 4 quick beeps | Maximum altitude reached |
| **LANDING** | 3 long beeps | Landing detected |
| **ERROR** | 5 rapid short beeps | System error or critical issue |
| **SHUTDOWN** | Descending tones | Safe system shutdown |

---

### CanSat Post-Flight Analysis Script
#### Overview
This script provides comprehensive post-flight analysis for CanSat flight data, generating detailed visualizations and summary reports.

#### Dependencies
- pandas
- numpy
- matplotlib
- seaborn
- scipy
- plotly

### Installation
```bash
pip install pandas numpy matplotlib seaborn scipy plotly
```

##### Usage
```bash
python cansat_analysis.py <data_file_path> <events_file_path> [--output_dir <optional_output_directory>]
```

##### Example
```bash
python cansat_analysis.py data_20240101.csv events_20240101.csv --output_dir my_flight_analysis
```

#### Outputs
The script generates:
- 3D trajectory plot
- Sensor overview plot
- Interactive 3D trajectory HTML
- Flight summary report
- Saved in specified or auto-generated output directory

#### Customization
Modify the `CanSatDataAnalyzer` class to add or adjust analysis methods as needed.

---

## Version History

Current Version: 5.0
- Enhanced error handling
- Improved flight event detection
- Added data buffering
- Expanded logging capabilities

---

## Launch Site Operations Guide

### Pre-Launch Checklist

#### Equipment Checklist
- [ ] CanSat Flight Computer
- [ ] Spare battery pack
- [ ] Model rocket and engine
- [ ] Launch pad and controller
- [ ] Laptop with data backup capability
- [ ] Basic tools (screwdrivers, pliers)
- [ ] First aid kit
- [ ] Weather monitoring equipment
- [ ] Recovery equipment (gloves, flags)
- [ ] Spare LEDs and button
- [ ] Multimeter
- [ ] Cable ties and tape

#### Ground Station Setup
1. Establish mission control area
   - Set up weather monitoring
   - Prepare data logging station
   - Establish communication protocols
   - Mark launch area perimeter

2. Weather Verification
   - Wind speed < 20 mph
   - No precipitation
   - Clear visibility
   - Temperature within operational range (-10°C to 45°C)

#### CanSat Preparation (T-60 minutes)
1. Physical Inspection
   - [ ] Check all sensor mounts
   - [ ] Verify antenna positioning
   - [ ] Inspect structural integrity
   - [ ] Check parachute attachment points
   - [ ] Verify battery secure

2. Power-Up Sequence (T-45 minutes)
   - [ ] Install fresh battery
   - [ ] Verify voltage readings
   - [ ] Power up system
   - [ ] Observe LED startup sequence
   - [ ] Wait for initialization complete

3. Sensor Verification (T-30 minutes)
   - [ ] Check MPU6050 readings
     * Verify acceleration values
     * Check gyroscope response
   - [ ] Verify BME280 data
     * Compare temperature with ground station
     * Verify pressure readings
     * Check altitude calculations
   - [ ] Confirm GPS lock
     * Wait for position fix
     * Record ground coordinates

4. Data System Check (T-20 minutes)
   - [ ] Start test data collection
   - [ ] Verify data file creation
   - [ ] Check event logging
   - [ ] Confirm data format

#### Rocket Integration (T-15 minutes)
1. Final CanSat Preparation
   - [ ] Reset flight computer
   - [ ] Verify 'READY' state
   - [ ] Secure all cables
   - [ ] Apply cable ties
   - [ ] Take photos for documentation

2. Payload Integration
   - [ ] Inspect rocket payload bay
   - [ ] Check parachute packing
   - [ ] Install CanSat in payload bay
   - [ ] Verify orientation marks
   - [ ] Secure payload bay door
   - [ ] Check ejection charge

3. Launch Pad Setup (T-5 minutes)
   - [ ] Mount rocket on launch rod
   - [ ] Verify vertical alignment
   - [ ] Check wind direction
   - [ ] Clear launch area
   - [ ] Final communication check

### Error Handling Guide

#### Pre-Launch Errors

| Error Condition | LED Pattern | Immediate Action | Resolution Steps |
|----------------|-------------|------------------|------------------|
| MPU6050 Fail | Red Fast Blink | Abort integration | 1. Check I2C connections<br>2. Power cycle<br>3. Replace if persistent |
| BME280 Fail | Red-Green Alt. | Hold integration | 1. Verify I2C address<br>2. Check voltage<br>3. Calibrate sensor |
| GPS No Lock | Red Double Blink | Delay integration | 1. Check antenna<br>2. Move to open area<br>3. Wait 5 minutes |
| Battery Low | Both LEDs Dim | Stop procedure | 1. Measure voltage<br>2. Replace battery<br>3. Verify connections |

#### Launch Sequence Errors

| Stage | Error Sign | Action | Recovery |
|-------|------------|--------|-----------|
| Power-Up | No LED | Abort | 1. Check power<br>2. Verify connections<br>3. Replace unit |
| Initialization | Red Steady | Hold | 1. Power cycle<br>2. Check sensors<br>3. Reset system |
| Ready State | Green Flicker | Warning | 1. Check voltage<br>2. Verify sensors<br>3. Monitor status |
| Data Collection | No Toggle | Decision Point | 1. Verify storage<br>2. Check processing<br>3. Reset if needed |

#### Emergency Procedures

1. **Launch Abort Required**
   - Call "ABORT" clearly on radio
   - Log abort time and reason
   - Secure launch area
   - Wait 5 minutes before approach
   - Document all conditions

2. **Recovery System Failure**
   - Mark last known coordinates
   - Deploy backup recovery team
   - Use tracking equipment
   - Document impact area
   - Collect all debris

3. **Data System Failure**
   - Note failure timestamp
   - Record visible conditions
   - Maintain launch log
   - Preserve error state
   - Document LED patterns

### Post-Flight Operations

#### Recovery Procedure
1. Wait for confirmed landing
2. Note landing coordinates
3. Deploy recovery team
4. Photograph landing site
5. Document CanSat condition
6. Careful payload extraction
7. Verify data collection

#### Data Recovery
1. **Immediate Actions**
   - Power down sequence
   - Remove from payload bay
   - Check physical condition
   - Document LED status
   - Secure all components

2. **Data Extraction**
   - Connect to ground station
   - Copy all data files
   - Verify file integrity
   - Create backup copy
   - Begin preliminary analysis

3. **System Analysis**
   - Check sensor readings
   - Verify flight events
   - Document anomalies
   - Compare with visual data
   - Prepare initial report

#### Post-Flight Checklist
- [ ] Photograph recovery site
- [ ] Record landing coordinates
- [ ] Check structural integrity
- [ ] Verify all components secure
- [ ] Document battery voltage
- [ ] Backup flight data
- [ ] Complete flight log
- [ ] Pack equipment
- [ ] Site cleanup
- [ ] Team debrief

### Safety Protocol

1. **General Safety**
   - Maintain safe distances
   - Wear appropriate PPE
   - Follow range safety rules
   - Keep first aid kit ready
   - Monitor weather conditions

2. **Emergency Contacts**
   - Range Safety Officer
   - Emergency Services
   - Team Lead
   - Technical Support
   - Medical Response

3. **Communication Protocol**
   - Use clear language
   - Confirm all critical messages
   - Document all communications
   - Maintain radio discipline
   - Use standard calls

[Previous sections continue as before...]

## Appendix A: Quick Reference Cards

### Launch Day Timeline
```
T-60: Equipment check
T-45: Power up
T-30: Sensor verification
T-20: Data system check
T-15: Integration
T-5:  Launch pad setup
T-0:  Launch
T+:   Track and recover
```

### Emergency Response Card
```
1. Call "ABORT" if needed
2. Secure launch area
3. Document conditions
4. Assess situation
5. Follow RSO instructions
6. Log all actions
```

### Troubleshooting Quick Reference
```
No Power: Check battery → connections → switch
No Data: Verify sensors → storage → processing
No GPS: Check antenna → view → wait 5 min
Bad Readings: Calibrate → power cycle → replace
```


