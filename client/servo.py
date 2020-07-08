import RPi.GPIO as GPIO
import time


class Servo:
    PWM_FREQUENCY = 50
    
    def __init__(self, pin, min_duty_cycle, max_duty_cycle):
        self.pin = pin
        self.min_duty_cycle = float(min_duty_cycle)
        self.max_duty_cycle = float(max_duty_cycle)

    def instantiate_pwm_channel(self):
        # Create PWM channel on the servo pin with frequency 50Hz
        self.pwm_channel = GPIO.PWM(self.pin, self.PWM_FREQUENCY)
        
    def setup(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)

    def pos_to_duty_cycle(self, pos):
        return self.min_duty_cycle * (1 - pos) + self.max_duty_cycle * pos

    # initialize the servo with the given position or duty cycle
    def start(self, pos=0, duty_cycle=None):
        self.setup()
        self.instantiate_pwm_channel()
        if duty_cycle is None:
            duty_cycle = self.pos_to_duty_cycle(pos)
        self.pwm_channel.start(duty_cycle)

    def stop(self):
        self.pwm_channel.stop()
        GPIO.cleanup(self.pin)

    def pause(self):
        self.pwm_channel.ChangeDutyCycle(0)

    def scan(self, num_steps=10, total_time=10, limits=(0, 1)):
        start_pos = self.pos_to_duty_cycle(limits[0])
        self.start(pos=start_pos)
        step_time = total_time / num_steps
        for step in range(num_steps):
            t = step / (num_steps - 1)
            pos = limits[0] * (1 - t) + limits[1] * t
            print(pos)
            duty_cycle = self.pos_to_duty_cycle(pos)
            self.pwm_channel.ChangeDutyCycle(duty_cycle)
            time.sleep(step_time)

    def move_to(self, pos):
        duty_cycle = self.pos_to_duty_cycle(pos)
        self.pwm_channel.ChangeDutyCycle(duty_cycle)
        time.sleep(1)
    
