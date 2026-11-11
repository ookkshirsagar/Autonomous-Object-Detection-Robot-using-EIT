import RPi.GPIO as GPIO
import time
from mpu6050 import mpu6050

class RobotMovement:
    def __init__(self):
        # Motor Driver Pins (Left Motors)
        self.left_front_in1 = 23
        self.left_front_in2 = 24
        self.left_front_en = 18
        self.left_rear_in1 = 25
        self.left_rear_in2 = 8
        self.left_rear_en = 12

        # Motor Driver Pins (Right Motors)
        self.right_front_in1 = 16
        self.right_front_in2 = 20
        self.right_front_en = 13
        self.right_rear_in1 = 21
        self.right_rear_in2 = 26
        self.right_rear_en = 19

        # MPU6050 sensor address
        sensor_address = 0x68  # Check your MPU6050 address
        self.sensor = mpu6050(sensor_address)

        # GPIO setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Set up Left Motors
        GPIO.setup(self.left_front_in1, GPIO.OUT)
        GPIO.setup(self.left_front_in2, GPIO.OUT)
        GPIO.setup(self.left_front_en, GPIO.OUT)
        GPIO.setup(self.left_rear_in1, GPIO.OUT)
        GPIO.setup(self.left_rear_in2, GPIO.OUT)
        GPIO.setup(self.left_rear_en, GPIO.OUT)

        # Set up Right Motors
        GPIO.setup(self.right_front_in1, GPIO.OUT)
        GPIO.setup(self.right_front_in2, GPIO.OUT)
        GPIO.setup(self.right_front_en, GPIO.OUT)
        GPIO.setup(self.right_rear_in1, GPIO.OUT)
        GPIO.setup(self.right_rear_in2, GPIO.OUT)
        GPIO.setup(self.right_rear_en, GPIO.OUT)

        # Set up PWM for motor speed control
        self.pwm_left_front = GPIO.PWM(self.left_front_en, 100)
        self.pwm_left_rear = GPIO.PWM(self.left_rear_en, 100)
        self.pwm_right_front = GPIO.PWM(self.right_front_en, 100)
        self.pwm_right_rear = GPIO.PWM(self.right_rear_en, 100)

        # Start PWM with a duty cycle of 0 (motors off)
        self.pwm_left_front.start(0)
        self.pwm_left_rear.start(0)
        self.pwm_right_front.start(0)
        self.pwm_right_rear.start(0)

    def set_motor_speed(self, pwm, speed):
        if speed < 0:
            speed = 0
        elif speed > 100:
            speed = 100
        pwm.ChangeDutyCycle(speed)

    def stop_motors(self):
        self.set_motor_speed(self.pwm_left_front, 0)
        self.set_motor_speed(self.pwm_left_rear, 0)
        self.set_motor_speed(self.pwm_right_front, 0)
        self.set_motor_speed(self.pwm_right_rear, 0)

        GPIO.output(self.left_front_in1, GPIO.LOW)
        GPIO.output(self.left_front_in2, GPIO.LOW)
        GPIO.output(self.left_rear_in1, GPIO.LOW)
        GPIO.output(self.left_rear_in2, GPIO.LOW)
        GPIO.output(self.right_front_in1, GPIO.LOW)
        GPIO.output(self.right_front_in2, GPIO.LOW)
        GPIO.output(self.right_rear_in1, GPIO.LOW)
        GPIO.output(self.right_rear_in2, GPIO.LOW)

    def move_forward(self, speed=50):
        # Left motors move forward
        GPIO.output(self.left_front_in1, GPIO.HIGH)
        GPIO.output(self.left_front_in2, GPIO.LOW)
        GPIO.output(self.left_rear_in1, GPIO.LOW)
        GPIO.output(self.left_rear_in2, GPIO.HIGH)

        # Right motors move forward
        GPIO.output(self.right_front_in1, GPIO.LOW)
        GPIO.output(self.right_front_in2, GPIO.HIGH)
        GPIO.output(self.right_rear_in1, GPIO.HIGH)
        GPIO.output(self.right_rear_in2, GPIO.LOW)

        self.set_motor_speed(self.pwm_left_front, speed)
        self.set_motor_speed(self.pwm_left_rear, speed)
        self.set_motor_speed(self.pwm_right_front, speed)
        self.set_motor_speed(self.pwm_right_rear, speed)

    def move_backward(self, speed=50):
        # Left motors move backward
        GPIO.output(self.left_front_in1, GPIO.LOW)
        GPIO.output(self.left_front_in2, GPIO.HIGH)
        GPIO.output(self.left_rear_in1, GPIO.HIGH)
        GPIO.output(self.left_rear_in2, GPIO.LOW)

        # Right motors move backward
        GPIO.output(self.right_front_in1, GPIO.HIGH)
        GPIO.output(self.right_front_in2, GPIO.LOW)
        GPIO.output(self.right_rear_in1, GPIO.LOW)
        GPIO.output(self.right_rear_in2, GPIO.HIGH)

        self.set_motor_speed(self.pwm_left_front, speed)
        self.set_motor_speed(self.pwm_left_rear, speed)
        self.set_motor_speed(self.pwm_right_front, speed)
        self.set_motor_speed(self.pwm_right_rear, speed)

    def turn_left(self, angle=82.0, speed=100):
        kp = 1.0
        current_angle = 0.0
        dt = 0.005

        while current_angle < angle:
            start_time = time.time()

            calibrated_gyro = self.get_calibrated_gyro_data()
            gyro_z = calibrated_gyro['z']
            angle_z = gyro_z * dt
            current_angle += angle_z

            correction = kp * (angle - current_angle)
            turn_speed = min(max(speed + correction, 30), 100)

            # Left motors backward
            GPIO.output(self.left_front_in1, GPIO.LOW)
            GPIO.output(self.left_front_in2, GPIO.HIGH)
            GPIO.output(self.left_rear_in1, GPIO.HIGH)
            GPIO.output(self.left_rear_in2, GPIO.LOW)

            # Right motors forward
            GPIO.output(self.right_front_in1, GPIO.LOW)
            GPIO.output(self.right_front_in2, GPIO.HIGH)
            GPIO.output(self.right_rear_in1, GPIO.HIGH)
            GPIO.output(self.right_rear_in2, GPIO.LOW)

            self.set_motor_speed(self.pwm_left_front, turn_speed)
            self.set_motor_speed(self.pwm_left_rear, turn_speed)
            self.set_motor_speed(self.pwm_right_front, turn_speed)
            self.set_motor_speed(self.pwm_right_rear, turn_speed)

            elapsed_time = time.time() - start_time
            if elapsed_time < dt:
                time.sleep(dt - elapsed_time)

        self.stop_motors()

    def turn_right(self, angle=86.0, speed=100):
        kp = 1.0
        current_angle = 0.0
        dt = 0.005

        # Convert angle to negative for clockwise turn
        angle = -abs(angle)

        while current_angle > angle:  # We use > because angle is negative
            start_time = time.time()

            calibrated_gyro = self.get_calibrated_gyro_data()
            gyro_z = calibrated_gyro['z']
            angle_z = gyro_z * dt
            current_angle += angle_z

            correction = kp * (angle - current_angle)
            turn_speed = min(max(speed + correction, 70), 100)

            # Left motors forward
            GPIO.output(self.left_front_in1, GPIO.HIGH)
            GPIO.output(self.left_front_in2, GPIO.LOW)
            GPIO.output(self.left_rear_in1, GPIO.LOW)
            GPIO.output(self.left_rear_in2, GPIO.HIGH)

            # Right motors backward
            GPIO.output(self.right_front_in1, GPIO.HIGH)
            GPIO.output(self.right_front_in2, GPIO.LOW)
            GPIO.output(self.right_rear_in1, GPIO.LOW)
            GPIO.output(self.right_rear_in2, GPIO.HIGH)

            self.set_motor_speed(self.pwm_left_front, turn_speed)
            self.set_motor_speed(self.pwm_left_rear, turn_speed)
            self.set_motor_speed(self.pwm_right_front, turn_speed)
            self.set_motor_speed(self.pwm_right_rear, turn_speed)

            elapsed_time = time.time() - start_time
            if elapsed_time < dt:
                time.sleep(dt - elapsed_time)

        self.stop_motors()

    def get_calibrated_gyro_data(self):
        gyro_offsets = {
            'x': -0.40,
            'y': 0.50,
            'z': -1.45
        }
        raw_data = self.sensor.get_gyro_data()
        calibrated_data = {
            'x': raw_data['x'] - gyro_offsets['x'],
            'y': raw_data['y'] - gyro_offsets['y'],
            'z': raw_data['z'] - gyro_offsets['z']
        }
        return calibrated_data

    def cleanup(self):
        self.pwm_left_front.stop()
        self.pwm_left_rear.stop()
        self.pwm_right_front.stop()
        self.pwm_right_rear.stop()
        GPIO.cleanup()
