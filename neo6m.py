from machine import UART, Pin
import time

class NEO6M:
    """
    NEO6M GPS module driver for Raspberry Pi Pico
    Handles NMEA sentence parsing and GPS data extraction
    """
    
    def __init__(self, uart_id=0, tx_pin=0, rx_pin=1, baud_rate=9600):
        """
        Initialize NEO6M GPS module
        
        Args:
            uart_id (int): UART bus number (0 or 1)
            tx_pin (int): TX pin number
            rx_pin (int): RX pin number
            baud_rate (int): UART baud rate (default 9600)
        """
        self.uart = UART(uart_id, baudrate=baud_rate)
        self.uart.init(baudrate=baud_rate, tx=Pin(tx_pin), rx=Pin(rx_pin))
        
        self.latitude = None
        self.longitude = None
        self.altitude = None
        self.speed = None
        self.satellites = None
        self.time = None
        self.date = None
        self.fix_status = 0
        self._last_update = 0
        
        # Buffer for incoming data
        self.buffer = ""
        
    def _parse_gga(self, gga_data):
        """Parse GPGGA sentence (Global Positioning System Fix Data)"""
        try:
            parts = gga_data.split(',')
            if len(parts) >= 10:
                # Check if we have a GPS fix
                if parts[6] != '0':
                    # Parse latitude
                    if parts[2] and parts[3]:
                        lat_deg = float(parts[2][:2])
                        lat_min = float(parts[2][2:])
                        lat_dec = lat_deg + (lat_min / 60.0)
                        if parts[3] == 'S':
                            lat_dec = -lat_dec
                        self.latitude = round(lat_dec, 6)
                    
                    # Parse longitude
                    if parts[4] and parts[5]:
                        lon_deg = float(parts[4][:3])
                        lon_min = float(parts[4][3:])
                        lon_dec = lon_deg + (lon_min / 60.0)
                        if parts[5] == 'W':
                            lon_dec = -lon_dec
                        self.longitude = round(lon_dec, 6)
                    
                    # Parse altitude
                    if parts[9]:
                        self.altitude = float(parts[9])
                    
                    # Parse number of satellites
                    if parts[7]:
                        self.satellites = int(parts[7])
                    
                    self.fix_status = int(parts[6])
                    return True
            return False
        except:
            return False
            
    def _parse_rmc(self, rmc_data):
        """Parse GPRMC sentence (Recommended Minimum Navigation Information)"""
        try:
            parts = rmc_data.split(',')
            if len(parts) >= 10:
                # Parse time
                if parts[1]:
                    time_str = parts[1]
                    if len(time_str) >= 6:
                        hours = int(time_str[0:2])
                        minutes = int(time_str[2:4])
                        seconds = int(time_str[4:6])
                        self.time = (hours, minutes, seconds)
                
                # Parse date
                if parts[9]:
                    date_str = parts[9]
                    if len(date_str) >= 6:
                        day = int(date_str[0:2])
                        month = int(date_str[2:4])
                        year = 2000 + int(date_str[4:6])
                        self.date = (day, month, year)
                
                # Parse speed (in knots, convert to km/h)
                if parts[7]:
                    self.speed = float(parts[7]) * 1.852  # Convert knots to km/h
                    
                return True
            return False
        except:
            return False
    
    def update(self):
        """
        Update GPS data by reading and parsing NMEA sentences
        Returns True if new data was successfully parsed
        """
        if (time.time() - self._last_update) < 1:  # Limit update rate to 1Hz
            return False
            
        while self.uart.any():
            char = self.uart.read(1).decode('ascii', 'ignore')
            if char == '\n':
                sentence = self.buffer.strip()
                self.buffer = ""
                
                if sentence.startswith('$'):
                    try:
                        # Verify checksum
                        asterisk_index = sentence.rfind('*')
                        if asterisk_index != -1:
                            checksum = int(sentence[asterisk_index + 1:], 16)
                            calc_checksum = 0
                            for c in sentence[1:asterisk_index]:
                                calc_checksum ^= ord(c)
                            
                            if checksum == calc_checksum:
                                # Parse different NMEA sentences
                                if sentence.startswith('$GPGGA'):
                                    self._parse_gga(sentence)
                                elif sentence.startswith('$GPRMC'):
                                    self._parse_rmc(sentence)
                    except:
                        pass
            else:
                self.buffer += char
        
        self._last_update = time.time()
        return True
    
    def get_position(self):
        """
        Get current latitude and longitude
        Returns tuple (latitude, longitude) or None if no fix
        """
        self.update()
        if self.latitude is not None and self.longitude is not None:
            return (self.latitude, self.longitude)
        return None
    
    def get_altitude(self):
        """Get current altitude in meters or None if not available"""
        self.update()
        return self.altitude
    
    def get_speed(self):
        """Get current speed in km/h or None if not available"""
        self.update()
        return self.speed
    
    def get_datetime(self):
        """
        Get current date and time from GPS
        Returns tuple ((year, month, day), (hours, minutes, seconds)) or None
        """
        self.update()
        if self.date and self.time:
            return (self.date, self.time)
        return None
    
    def get_satellites(self):
        """Get number of satellites in view or None if not available"""
        self.update()
        return self.satellites
    
    def has_fix(self):
        """Check if GPS has a valid fix"""
        self.update()
        return self.fix_status > 0