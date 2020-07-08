import sys

from servo import Servo


# read pin number and target position from command line arguments
pin, pos = int(sys.argv[1]), float(sys.argv[2])
print(pin, pos)


servo = Servo(pin, 2, 12)

servo.start()
servo.move_to(pos)
servo.stop()
