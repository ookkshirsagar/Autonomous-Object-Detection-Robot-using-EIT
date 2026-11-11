import RPi.GPIO as GPIO
import time
from mpu6050 import mpu6050

# Motor Driver Pins (Left Motors)
left_front_in1 = 23
left_front_in2 = 24
left_front_en = 18
left_rear_in1 = 25
left_rear_in2 = 8
left_rear_en = 12

# Motor Driver Pins (Right Motors)
right_front_in1 = 16
right_front_in2 = 20
right_front_en = 13
right_rear_in1 = 21
right_rear_in2 = 26
right_rear_en = 19

# MPU6050 sensor address
sensor_address = 0x68  # Check your MPU6050 address
sensor = mpu6050(sensor_address)

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Set up Left Motors
GPIO.setup(left_front_in1, GPIO.OUT)
GPIO.setup(left_front_in2, GPIO.OUT)
GPIO.setup(left_front_en, GPIO.OUT)
GPIO.setup(left_rear_in1, GPIO.OUT)
GPIO.setup(left_rear_in2, GPIO.OUT)
GPIO.setup(left_rear_en, GPIO.OUT)

# Set up Right Motors
GPIO.setup(right_front_in1, GPIO.OUT)
GPIO.setup(right_front_in2, GPIO.OUT)
GPIO.setup(right_front_en, GPIO.OUT)
GPIO.setup(right_rear_in1, GPIO.OUT)
GPIO.setup(right_rear_in2, GPIO.OUT)
GPIO.setup(right_rear_en, GPIO.OUT)

# Set up PWM for motor speed control
pwm_left_front = GPIO.PWM(left_front_en, 100)
pwm_left_rear = GPIO.PWM(left_rear_en, 100)
pwm_right_front = GPIO.PWM(right_front_en, 100)
pwm_right_rear = GPIO.PWM(right_rear_en, 100)

# Start PWM with a duty cycle of 0 (motors off)
pwm_left_front.start(0)
pwm_left_rear.start(0)
pwm_right_front.start(0)
pwm_right_rear.start(0)

# Function to set motor speed
def set_motor_speed(pwm, speed):
    if speed < 0:
        speed = 0
    elif speed > 100:
        speed = 100
    pwm.ChangeDutyCycle(speed)

# Function to stop all motors
def stop_motors():
    set_motor_speed(pwm_left_front, 0)
    set_motor_speed(pwm_left_rear, 0)
    set_motor_speed(pwm_right_front, 0)
    set_motor_speed(pwm_right_rear, 0)

    GPIO.output(left_front_in1, GPIO.LOW)
    GPIO.output(left_front_in2, GPIO.LOW)
    GPIO.output(left_rear_in1, GPIO.LOW)
    GPIO.output(left_rear_in2, GPIO.LOW)
    GPIO.output(right_front_in1, GPIO.LOW)
    GPIO.output(right_front_in2, GPIO.LOW)
    GPIO.output(right_rear_in1, GPIO.LOW)
    GPIO.output(right_rear_in2, GPIO.LOW)

# Function to move forward for 1 second
def move_forward_for_1_second(speed=100):
    # Left motors move forward
    GPIO.output(left_front_in1, GPIO.HIGH)
    GPIO.output(left_front_in2, GPIO.LOW)
    GPIO.output(left_rear_in1, GPIO.LOW)
    GPIO.output(left_rear_in2, GPIO.HIGH)

    # Right motors move forward
    GPIO.output(right_front_in1, GPIO.LOW)
    GPIO.output(right_front_in2, GPIO.HIGH)
    GPIO.output(right_rear_in1, GPIO.HIGH)
    GPIO.output(right_rear_in2, GPIO.LOW)

    set_motor_speed(pwm_left_front, speed)
    set_motor_speed(pwm_left_rear, speed)
    set_motor_speed(pwm_right_front, speed)
    set_motor_speed(pwm_right_rear, speed)

    time.sleep(1)  # Move forward for 1 second
    stop_motors()

# Function to turn left with gyro control
def turn_left(sensor, angle=82.0, speed=100):
    kp = 1.0
    current_angle = 0.0
    dt = 0.005

    while current_angle < angle:
        start_time = time.time()

        calibrated_gyro = get_calibrated_gyro_data(sensor)
        gyro_z = calibrated_gyro['z']
        angle_z = gyro_z * dt
        current_angle += angle_z

        correction = kp * (angle - current_angle)
        turn_speed = min(max(speed + correction, 30), 100)

        # Left motors backward
        GPIO.output(left_front_in1, GPIO.LOW)
        GPIO.output(left_front_in2, GPIO.HIGH)
        GPIO.output(left_rear_in1, GPIO.HIGH)
        GPIO.output(left_rear_in2, GPIO.LOW)

        # Right motors forward
        GPIO.output(right_front_in1, GPIO.LOW)
        GPIO.output(right_front_in2, GPIO.HIGH)
        GPIO.output(right_rear_in1, GPIO.HIGH)
        GPIO.output(right_rear_in2, GPIO.LOW)

        set_motor_speed(pwm_left_front, turn_speed)
        set_motor_speed(pwm_left_rear, turn_speed)
        set_motor_speed(pwm_right_front, turn_speed)
        set_motor_speed(pwm_right_rear, turn_speed)

        elapsed_time = time.time() - start_time
        if elapsed_time < dt:
            time.sleep(dt - elapsed_time)

    stop_motors()


# Function to turn right with gyro control
def turn_right(sensor, angle=86.0, speed=100):
    kp = 1.0
    current_angle = 0.0
    dt = 0.005

    # Convert angle to negative for clockwise turn
    angle = -abs(angle)

    while current_angle > angle:  # We use > because angle is negative
        start_time = time.time()

        calibrated_gyro = get_calibrated_gyro_data(sensor)
        gyro_z = calibrated_gyro['z']
        angle_z = gyro_z * dt
        current_angle += angle_z

        correction = kp * (angle - current_angle)
        turn_speed = min(max(speed + correction, 70), 100)

        # Left motors forward
        GPIO.output(left_front_in1, GPIO.HIGH)
        GPIO.output(left_front_in2, GPIO.LOW)
        GPIO.output(left_rear_in1, GPIO.LOW)
        GPIO.output(left_rear_in2, GPIO.HIGH)

        # Right motors backward
        GPIO.output(right_front_in1, GPIO.HIGH)
        GPIO.output(right_front_in2, GPIO.LOW)
        GPIO.output(right_rear_in1, GPIO.LOW)
        GPIO.output(right_rear_in2, GPIO.HIGH)

        set_motor_speed(pwm_left_front, turn_speed)
        set_motor_speed(pwm_left_rear, turn_speed)
        set_motor_speed(pwm_right_front, turn_speed)
        set_motor_speed(pwm_right_rear, turn_speed)

        elapsed_time = time.time() - start_time
        if elapsed_time < dt:
            time.sleep(dt - elapsed_time)

    stop_motors()


# Function to get calibrated gyroscope data
def get_calibrated_gyro_data(sensor):
    gyro_offsets = {
        'x': -0.40,
        'y': 0.50,
        'z': -1.45
    }
    raw_data = sensor.get_gyro_data()
    calibrated_data = {
        'x': raw_data['x'] - gyro_offsets['x'],
        'y': raw_data['y'] - gyro_offsets['y'],
        'z': raw_data['z'] - gyro_offsets['z']
    }
    return calibrated_data

try:
    while True:
        move_forward_for_1_second()
        print("Moving forward...")
        time.sleep(2)

        stop_motors()
        time.sleep(1)

        print("Turning left...")
        turn_left(sensor)

        stop_motors()
        time.sleep(1)
        
        move_forward_for_1_second()
        print("Moving forward...")
        time.sleep(2)

        stop_motors()
        time.sleep(1)

        print("Turning right...")
        turn_right(sensor)

        stop_motors()
        time.sleep(1)

except KeyboardInterrupt:
    print("\nExiting program.")

finally:
    pwm_left_front.stop()
    pwm_left_rear.stop()
    pwm_right_front.stop()
    pwm_right_rear.stop()
    GPIO.cleanup()
