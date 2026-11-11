import RPi.GPIO as GPIO
import time

# Set GPIO numbering mode
GPIO.setmode(GPIO.BCM)

# Set GPIO pins for the servos
servo_pin_1 = 17  # GPIO pin for the first servo
servo_pin_2 = 27  # GPIO pin for the second servo
servo_pin_3 = 4 # GPIO pin for the second servo
servo_pin_4 = 22  # GPIO pin for the second servo

# Set PWM parameters
GPIO.setup(servo_pin_1, GPIO.OUT)
GPIO.setup(servo_pin_2, GPIO.OUT)
GPIO.setup(servo_pin_3, GPIO.OUT)
GPIO.setup(servo_pin_4, GPIO.OUT)

#PWM frequency set to 50 Hz for all motors
pwm_1 = GPIO.PWM(servo_pin_1, 50)  
pwm_2 = GPIO.PWM(servo_pin_2, 50) 
pwm_3 = GPIO.PWM(servo_pin_3, 50) 
pwm_4 = GPIO.PWM(servo_pin_4, 50) 

# Start PWM with 0% duty cycle
pwm_1.start(0)
pwm_2.start(0)
pwm_3.start(0)
pwm_4.start(0)

# Function to set servo angle
def set_servo_angle(pwm, angle):
    duty_cycle = 2.5 + (angle / 18.0)  # Adjust the duty cycle calculation if needed
    pwm.ChangeDutyCycle(duty_cycle)
    

# Initial angles
initial_angle_1 = 120
initial_angle_2 = 50
initial_angle_3 = 120
initial_angle_4 = 50

try:
    # Set the initial positions for the servos
    set_servo_angle(pwm_1, initial_angle_1)
    set_servo_angle(pwm_2, initial_angle_2)
    set_servo_angle(pwm_3, initial_angle_3)
    set_servo_angle(pwm_4, initial_angle_4)
    time.sleep(1)  # Give time for servos to reach the initial positions

    while True:
        # Move the first servo from 180 to 160 degrees and the second from 0 to 20 degrees
        set_servo_angle(pwm_1, 170)
        set_servo_angle(pwm_2, 0)
        set_servo_angle(pwm_3, 170)
        set_servo_angle(pwm_4, 0)
        time.sleep(5)  # Adjust delay as necessary for servos to reach position

        # Move the first servo from 160 to 180 degrees and the second from 20 to 0 degrees
        set_servo_angle(pwm_1, 110)
        set_servo_angle(pwm_2, 60)
        set_servo_angle(pwm_3, 110)
        set_servo_angle(pwm_4, 60)
        time.sleep(1)  # Adjust delay as necessary for servos to reach position

except KeyboardInterrupt:
    print("Program stopped by user")

finally:
    pwm_1.stop()
    pwm_2.stop()
    pwm_3.stop()
    pwm_4.stop()
    GPIO.cleanup()
