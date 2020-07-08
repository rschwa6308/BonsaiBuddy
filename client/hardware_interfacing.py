import time

# SPI library (for hardware SPI) and MCP3008 (A2D) library.
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import os

from servo import Servo


# Set up MCP interface
SPI_PORT   = 0
SPI_DEVICE = 0
mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))

MOISTURE_SENSOR_CHANNEL = 0
LIGHT_SENSOR_CHANNEL    = 1

# Return the mean of num_samples samples taken over period seconds
# Not thread-safe (runs blocking)
def sample_channel(channel, num_samples=5, period=2):
    sample_period = period / (num_samples - 1)
    total = 0
    for _ in range(num_samples):
        # raw value in range 0 - 1023
        total += mcp.read_adc(channel)
        time.sleep(sample_period)
    return total / num_samples

def read_moisture_sensor():
    # max value of 850 confirmed empirically
    return round(sample_channel(MOISTURE_SENSOR_CHANNEL) / 850, 3)

def read_light_sensor():
    # max value of 1023 confirmed empirically
    return round(sample_channel(LIGHT_SENSOR_CHANNEL) / 1023, 3)



# Native GPIO library
import RPi.GPIO as GPIO

PUMP_PIN  = 4
SERVO_PIN = 18

# set up relay GPIO pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(PUMP_PIN, GPIO.OUT)
GPIO.output(PUMP_PIN, GPIO.LOW)
GPIO.output(PUMP_PIN, GPIO.HIGH)


# Close the relay for duration seconds
def run_pump(duration=5):
    GPIO.output(PUMP_PIN, GPIO.LOW)
    time.sleep(duration)
    GPIO.output(PUMP_PIN, GPIO.HIGH)


# Pump flow rate in ml/s (confirmed empirically (NOTE: depends on head))
PUMP_RATE = 23  # (free flowing)
# PUMP_RATE = 15  # (with ring disperser)

# Max flow rate of the diverter in ml/s
DIVERTER_RATE = 8
DIVERTER_BASE = 6  # base seconds added to account for dribble



# Pump volume milliliters
def pump_volume(volume):
    run_pump(int(volume) / PUMP_RATE)


# Pump volume milliliters to the given diverter target position
# (waits for diverter to finish flowing)
def pump_volume_with_target_pos(volume, target_pos):
    move_servo_to(target_pos)

    start = time.time()
    pump_volume(volume)
    end = time.time()

    # wait long enough for diverter to drain entire volume
    elapsed = end - start
    required = volume / DIVERTER_RATE + DIVERTER_BASE
    time.sleep(max(0, required - elapsed))

    
def move_servo_to(pos):
    command = 'python servo_move_to.py %d %0.3f' % (SERVO_PIN, pos)
    # print(command)
    os.system(command)


def cleanup_io():
    GPIO.cleanup()



if __name__ == '__main__':
    pump_volume_with_target(250, 0.7)
    print('done!')
    
    
##    pump_volume_with_target(50, 0.42)
##    print('done!')
##    pump_volume_with_target(50, 0.7)
##    print('done!')

##    pump_volume(100)


##    servo.start()
##    servo.move_to(0.4)
##    pump_volume(20)
##
##    time.sleep(2)
##
##    servo.move_to(0.65)
##    pump_volume(20)
##    servo.stop()



##    move_arm_to(0.4)
##    # pump_volume(8)
##
##    time.sleep(2)
##
##    move_arm_to(0.65)
##    # pump_volume(8)
    GPIO.cleanup()
    
