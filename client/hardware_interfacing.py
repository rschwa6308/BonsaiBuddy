import time

# SPI library (for hardware SPI) and MCP3008 (A2D) library.
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008


# Set up MCP interface
SPI_PORT   = 0
SPI_DEVICE = 0
mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))


MOISTURE_SENSOR_CHANNEL = 0

# Return the mean of num_samples samples taken over period seconds
# Not necessarily thread-safe (runs blocking)
def read_moisture_sensor(num_samples=3, period=1):
    sample_period = period / (num_samples - 1)
    total = 0
    for _ in range(num_samples):
        # raw value in range 0 - 850 (confirmed empirically)
        total += mcp.read_adc(MOISTURE_SENSOR_CHANNEL) / 850
        time.sleep(sample_period)
    return total / num_samples



# Native GPIO library
import RPi.GPIO as GPIO

PUMP_PIN = 7

# set up relay GPIO pins
GPIO.setmode(GPIO.BOARD) # Broadcom pin-numbering scheme
GPIO.setup(PUMP_PIN, GPIO.OUT)
GPIO.output(PUMP_PIN, GPIO.LOW)
GPIO.output(PUMP_PIN, GPIO.HIGH)


# Close the relay for duration seconds
def run_pump(duration=5):
    GPIO.output(PUMP_PIN, GPIO.LOW)
    time.sleep(duration)
    GPIO.output(PUMP_PIN, GPIO.HIGH)
