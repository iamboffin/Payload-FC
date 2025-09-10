from machine import Pin, UART
import time

# Configure the UART for GPS communication
gps_input = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9), timeout=1000, timeout_char=50)

# Variables for tracking GPS data
TIMEOUT = False
FIX_STATUS = False
latitude = None
longitude = None
satellites = None
gpsTime = None


# Function to get GPS position data
def getPositionData(gps_input):
    global FIX_STATUS, TIMEOUT, latitude, longitude, satellites, gpsTime
    timeout = time.time() + 8  # Timeout set to 8 seconds
    while time.time() < timeout:
        buff = gps_input.readline()
        if buff is not None:
            try:
                buff = buff.decode('utf-8').strip()  # Decode and clean data
            except:  # Catch any decoding errors
                continue  # Skip invalid lines
            
            parts = buff.split(',')
            print(buff)  # Print raw NMEA sentence for debugging
            
            if parts[0] == "$GNGGA" and len(parts) >= 7:
                if parts[6] == '0':  # No fix
                    print("No GPS fix yet.")
                    continue
                
                # Parse latitude
                latitude = convertToDegree(parts[2])
                if parts[3] == 'S':
                    latitude = -latitude
                
                # Parse longitude
                longitude = convertToDegree(parts[4])
                if parts[5] == 'W':
                    longitude = -longitude
                
                # Parse additional data
                satellites = parts[7]
                gpsTime = parts[1][0:2] + ":" + parts[1][2:4] + ":" + parts[1][4:6]
                
                FIX_STATUS = True
                return
    
    TIMEOUT = True


# Function to convert raw latitude/longitude to degrees
def convertToDegree(raw_value):
    try:
        raw_float = float(raw_value)
        degrees = int(raw_float / 100)  # Extract degrees
        minutes = raw_float - (degrees * 100)  # Extract minutes
        return round(degrees + (minutes / 60.0), 6)  # Convert to decimal degrees
    except ValueError:
        return None


# Main loop
while True:
    getPositionData(gps_input)

    if FIX_STATUS:
        print("GPS Fix Acquired:")
        print(f"Latitude: {latitude}")
        print(f"Longitude: {longitude}")
        print(f"Satellites: {satellites}")
        print(f"Time (UTC): {gpsTime}")
        FIX_STATUS = False

    if TIMEOUT:
        print("Request Timeout: No GPS data received.")
        TIMEOUT = False