import RPi.GPIO as GPIO
import time

def initialize_gpio():
    # Set GPIO numbering mode
    GPIO.setmode(GPIO.BCM)

    # Set GPIO pins for the servos
    global servo_pin_1, servo_pin_2, servo_pin_3, servo_pin_4
    servo_pin_1 = 17  # GPIO pin for the first servo
    servo_pin_2 = 27  # GPIO pin for the second servo
    servo_pin_3 = 22  # GPIO pin for the third servo
    servo_pin_4 = 4   # GPIO pin for the fourth servo

    # Set PWM parameters
    GPIO.setup(servo_pin_1, GPIO.OUT)
    GPIO.setup(servo_pin_2, GPIO.OUT)
    GPIO.setup(servo_pin_3, GPIO.OUT)
    GPIO.setup(servo_pin_4, GPIO.OUT)

    # Initialize PWM for each servo
    global pwm_1, pwm_2, pwm_3, pwm_4
    pwm_1 = GPIO.PWM(servo_pin_1, 50)  # PWM frequency set to 50 Hz
    pwm_2 = GPIO.PWM(servo_pin_2, 50)
    pwm_3 = GPIO.PWM(servo_pin_3, 50)
    pwm_4 = GPIO.PWM(servo_pin_4, 50)

    # Start PWM with 0% duty cycle
    pwm_1.start(0)
    pwm_2.start(0)
    pwm_3.start(0)
    pwm_4.start(0)

def set_servo_angle(pwm, angle):
    duty_cycle = 2.5 + (angle / 18.0)  # Adjust the duty cycle calculation if needed
    pwm.ChangeDutyCycle(duty_cycle)

def move_servos_to_initial_positions():
    # Initial angles
    initial_angle_1 = 140
    initial_angle_2 = 30
    initial_angle_3 = 140
    initial_angle_4 = 30

    # Set the initial positions for the servos
    set_servo_angle(pwm_1, initial_angle_1)
    set_servo_angle(pwm_2, initial_angle_2)
    set_servo_angle(pwm_3, initial_angle_3)
    set_servo_angle(pwm_4, initial_angle_4)
    print("Servo are UP")
    time.sleep(5)  # Give time for servos to reach the initial positions

def move_servos_down():

    # Move the first servo from 180 to 160 degrees and the second from 0 to 20 degrees
    set_servo_angle(pwm_1, 170)
    set_servo_angle(pwm_2, 0)
    set_servo_angle(pwm_3, 170)
    set_servo_angle(pwm_4, 0)
    print("Servo are down")
    time.sleep(15)  # Adjust delay as necessary for servos to reach position


def move_servos_up():

    # Move the first servo from 160 to 180 degrees and the second from 20 to 0 degrees
    set_servo_angle(pwm_1, 140)
    set_servo_angle(pwm_2, 30)
    set_servo_angle(pwm_3, 140)
    set_servo_angle(pwm_4, 30)
    print("Servo are Up again")
    time.sleep(1)  # Adjust delay as necessary for servos to reach position



def cleanup():
    pwm_1.stop()
    pwm_2.stop()
    pwm_3.stop()
    pwm_4.stop()
    GPIO.cleanup()

if __name__ == "__main__":
    initialize_gpio()
    move_servos_to_initial_positions()
    move_servos_down()
    move_servos_up()
