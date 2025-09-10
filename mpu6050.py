"""
MPU6050 MicroPython driver for the RP2040.
Handles acceleration, gyroscope and temperature measurements.
"""
from machine import Pin, I2C
import struct
import time

class MPU6050:
    # Device I2C Address
    MPU6050_ADDR = 0x68
    
    # Register Addresses
    SELF_TEST_X = 0x0D
    SELF_TEST_Y = 0x0E
    SELF_TEST_Z = 0x0F
    SELF_TEST_A = 0x10
    SMPLRT_DIV = 0x19
    CONFIG = 0x1A
    GYRO_CONFIG = 0x1B
    ACCEL_CONFIG = 0x1C
    FIFO_EN = 0x23
    INT_ENABLE = 0x38
    ACCEL_XOUT_H = 0x3B
    ACCEL_XOUT_L = 0x3C
    ACCEL_YOUT_H = 0x3D
    ACCEL_YOUT_L = 0x3E
    ACCEL_ZOUT_H = 0x3F
    ACCEL_ZOUT_L = 0x40
    TEMP_OUT_H = 0x41
    TEMP_OUT_L = 0x42
    GYRO_XOUT_H = 0x43
    GYRO_XOUT_L = 0x44
    GYRO_YOUT_H = 0x45
    GYRO_YOUT_L = 0x46
    GYRO_ZOUT_H = 0x47
    GYRO_ZOUT_L = 0x48
    PWR_MGMT_1 = 0x6B
    PWR_MGMT_2 = 0x6C
    WHO_AM_I = 0x75

    # Configuration Constants
    ACCEL_FS_SEL_2G = 0x00
    ACCEL_FS_SEL_4G = 0x08
    ACCEL_FS_SEL_8G = 0x10
    ACCEL_FS_SEL_16G = 0x18
    
    GYRO_FS_SEL_250 = 0x00
    GYRO_FS_SEL_500 = 0x08
    GYRO_FS_SEL_1000 = 0x10
    GYRO_FS_SEL_2000 = 0x18
    
    ACCEL_SCALE_MODIFIER_2G = 16384.0
    ACCEL_SCALE_MODIFIER_4G = 8192.0
    ACCEL_SCALE_MODIFIER_8G = 4096.0
    ACCEL_SCALE_MODIFIER_16G = 2048.0
    
    GYRO_SCALE_MODIFIER_250DEG = 131.0
    GYRO_SCALE_MODIFIER_500DEG = 65.5
    GYRO_SCALE_MODIFIER_1000DEG = 32.8
    GYRO_SCALE_MODIFIER_2000DEG = 16.4

    def __init__(self, i2c, address=MPU6050_ADDR):
        """Initialize the MPU6050.
        
        Args:
            i2c: initialized I2C object
            address: I2C address of the device (default 0x68)
        """
        self.i2c = i2c
        self.address = address
        
        # Wake up the MPU6050 and verify it's responding
        self._verify_device()
        self._wake_up()
        self._configure()
        
        # Set default ranges
        self.accel_range = self.ACCEL_FS_SEL_2G
        self.gyro_range = self.GYRO_FS_SEL_250
        self._set_accel_range(self.accel_range)
        self._set_gyro_range(self.gyro_range)

    def _verify_device(self):
        """Verify the device is an MPU6050."""
        if self._read_byte(self.WHO_AM_I) != 0x68:
            raise RuntimeError("MPU6050 not found at address 0x%x" % self.address)

    def _wake_up(self):
        """Wake up the device."""
        self._write_byte(self.PWR_MGMT_1, 0x00)
        time.sleep_ms(100)

    def _configure(self):
        """Configure the device."""
        # Set sample rate divider
        self._write_byte(self.SMPLRT_DIV, 0x07)
        # Disable FSYNC, set accel and gyro bandwidth to 44 and 42 Hz
        self._write_byte(self.CONFIG, 0x00)
        # Disable all interrupts
        self._write_byte(self.INT_ENABLE, 0x00)
        # Disable FIFO
        self._write_byte(self.FIFO_EN, 0x00)

    def _read_byte(self, reg):
        """Read a single byte from the device."""
        return self.i2c.readfrom_mem(self.address, reg, 1)[0]

    def _read_word(self, reg):
        """Read a word (2 bytes) from the device."""
        data = self.i2c.readfrom_mem(self.address, reg, 2)
        return struct.unpack('>h', data)[0]

    def _write_byte(self, reg, val):
        """Write a byte to the device."""
        self.i2c.writeto_mem(self.address, reg, bytes([val]))

    def _set_accel_range(self, accel_range):
        """Set the accelerometer range."""
        self._write_byte(self.ACCEL_CONFIG, accel_range)
        self.accel_range = accel_range

    def _set_gyro_range(self, gyro_range):
        """Set the gyroscope range."""
        self._write_byte(self.GYRO_CONFIG, gyro_range)
        self.gyro_range = gyro_range

    def get_acceleration(self):
        """Read acceleration data.
        
        Returns:
            Tuple of (x, y, z) acceleration values in g's
        """
        x = self._read_word(self.ACCEL_XOUT_H)
        y = self._read_word(self.ACCEL_YOUT_H)
        z = self._read_word(self.ACCEL_ZOUT_H)
        
        scale_modifier = None
        if self.accel_range == self.ACCEL_FS_SEL_2G:
            scale_modifier = self.ACCEL_SCALE_MODIFIER_2G
        elif self.accel_range == self.ACCEL_FS_SEL_4G:
            scale_modifier = self.ACCEL_SCALE_MODIFIER_4G
        elif self.accel_range == self.ACCEL_FS_SEL_8G:
            scale_modifier = self.ACCEL_SCALE_MODIFIER_8G
        elif self.accel_range == self.ACCEL_FS_SEL_16G:
            scale_modifier = self.ACCEL_SCALE_MODIFIER_16G
            
        x = x / scale_modifier
        y = y / scale_modifier
        z = z / scale_modifier
        
        return (x, y, z)

    def get_rotation(self):
        """Read gyroscope data.
        
        Returns:
            Tuple of (x, y, z) rotation values in degrees/second
        """
        x = self._read_word(self.GYRO_XOUT_H)
        y = self._read_word(self.GYRO_YOUT_H)
        z = self._read_word(self.GYRO_ZOUT_H)
        
        scale_modifier = None
        if self.gyro_range == self.GYRO_FS_SEL_250:
            scale_modifier = self.GYRO_SCALE_MODIFIER_250DEG
        elif self.gyro_range == self.GYRO_FS_SEL_500:
            scale_modifier = self.GYRO_SCALE_MODIFIER_500DEG
        elif self.gyro_range == self.GYRO_FS_SEL_1000:
            scale_modifier = self.GYRO_SCALE_MODIFIER_1000DEG
        elif self.gyro_range == self.GYRO_FS_SEL_2000:
            scale_modifier = self.GYRO_SCALE_MODIFIER_2000DEG
            
        x = x / scale_modifier
        y = y / scale_modifier
        z = z / scale_modifier
        
        return (x, y, z)

    def get_temperature(self):
        """Read temperature data.
        
        Returns:
            Temperature in degrees Celsius
        """
        raw_temp = self._read_word(self.TEMP_OUT_H)
        temp_celsius = (raw_temp / 340.0) + 36.53
        return temp_celsius

    def test(self):
        """Perform a basic test of the sensor.
        
        Returns:
            True if all tests pass, False otherwise
        """
        try:
            # Test communication
            self._verify_device()
            
            # Test acceleration reading
            accel = self.get_acceleration()
            if None in accel:
                return False
                
            # Test gyroscope reading
            gyro = self.get_rotation()
            if None in gyro:
                return False
                
            # Test temperature reading
            temp = self.get_temperature()
            if temp is None:
                return False
                
            return True
            
        except Exception as e:
            print(f"Test failed: {str(e)}")
            return False