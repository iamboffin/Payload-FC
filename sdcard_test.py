from machine import SPI, Pin
import machine
import sdcard
import uos
import random
from time import sleep

# Assign chip select (CS) pin (and start it high)
cs = machine.Pin(13, machine.Pin.OUT)

# Initialize SPI peripheral (start with 1 MHz)
spi = machine.SPI(1,
                  baudrate=1000000,
                  polarity=0,
                  phase=0,
                  bits=8,
                  firstbit=machine.SPI.MSB,
                  sck=machine.Pin(10),
                  mosi=machine.Pin(11),
                  miso=machine.Pin(12))

# Initialize SD card
sd = sdcard.SDCard(spi, cs)

# Mount filesystem
vfs = uos.VfsFat(sd)
uos.mount(vfs, "/sd")

while True:
    # Generate random data
    temperature = random.uniform(20.0, 30.0)  # Random temperature between 20-30°C
    humidity = random.uniform(40.0, 60.0)     # Random humidity between 40-60%
    pressure = random.uniform(980.0, 1020.0)  # Random pressure between 980-1020 hPa
    light = random.randint(0, 1000)          # Random light level between 0-1000

    # Create a file in the SD card root directory and write data
    with open("/sd/sensor_data.csv", "a") as file:
        # Format data with 2 decimal places for floating point values
        data_str = "{:.2f},{:.2f},{:.2f},{}\n".format(
            temperature,
            humidity,
            pressure,
            light
        )
        file.write(data_str)

    # Read and print the contents of the file
    with open("/sd/sensor_data.csv", "r") as file:
        data = file.read()
        print(data)
    
    sleep(1)  # Wait for 1 second before next reading