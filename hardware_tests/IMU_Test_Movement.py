import RPi.GPIO as GPIO
import time
from mpu6050 import mpu6050

# Motor Driver 1 Pins (Left Motors)
left_front_in1 = 23
left_front_in2 = 24
left_front_en = 18
left_rear_in1 = 25
left_rear_in2 = 8
left_rear_en = 12

# Motor Driver 2 Pins (Right Motors)
right_front_in1 = 16
right_front_in2 = 20
right_front_en = 13
right_rear_in1 = 21
right_rear_in2 = 26
right_rear_en = 19

# MPU6050 sensor address
sensor_address = 0x68  # Check your MPU6050 address

# Create MPU6050 instance
sensor = mpu6050(sensor_address)

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Set up Left Motors (Motor Driver 1)
GPIO.setup(left_front_in1, GPIO.OUT)
GPIO.setup(left_front_in2, GPIO.OUT)
GPIO.setup(left_front_en, GPIO.OUT)
GPIO.setup(left_rear_in1, GPIO.OUT)
GPIO.setup(left_rear_in2, GPIO.OUT)
GPIO.setup(left_rear_en, GPIO.OUT)

# Set up Right Motors (Motor Driver 2)
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

# Function to move motors forward
def move_forward():
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
    
    set_motor_speed(pwm_left_front, 100)
    set_motor_speed(pwm_left_rear, 100)
    set_motor_speed(pwm_right_front, 100)
    set_motor_speed(pwm_right_rear, 100)

# Function to stop all motors
def stop_motors():
    GPIO.output(left_front_in1, GPIO.LOW)
    GPIO.output(left_front_in2, GPIO.LOW)
    GPIO.output(left_rear_in1, GPIO.LOW)
    GPIO.output(left_rear_in2, GPIO.LOW)
    GPIO.output(right_front_in1, GPIO.LOW)
    GPIO.output(right_front_in2, GPIO.LOW)
    GPIO.output(right_rear_in1, GPIO.LOW)
    GPIO.output(right_rear_in2, GPIO.LOW)
    set_motor_speed(pwm_left_front, 0)
    set_motor_speed(pwm_left_rear, 0)
    set_motor_speed(pwm_right_front, 0)
    set_motor_speed(pwm_right_rear, 0)

# Function to get calibrated accelerometer data
def get_calibrated_accel_data(sensor):
    """Retrieve and calibrate accelerometer data."""
    raw_data = sensor.get_accel_data()
    accel_calib_factors = {
        'x': 1 / 10.20,
        'y': 1 / 9.85,
        'z': 1 / 8.25
    }
    calibrated_data = {
        'x': raw_data['x'] * accel_calib_factors['x'],
        'y': raw_data['y'] * accel_calib_factors['y'],
        'z': raw_data['z'] * accel_calib_factors['z']
    }
    return calibrated_data

# Function to get calibrated gyroscope data
def get_calibrated_gyro_data(sensor):
    """Retrieve and calibrate gyroscope data."""
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

def turn_left(sensor):
    desired_angle = 83.0  # Desired angle to turn
    kp = 5.0  # Adjusted proportional gain for smoother correction
    max_speed = 60.0  # Reduced maximum speed for more precise control
    min_speed = 20.0  # Minimum speed adjusted for smooth operation
    dt = 0.005  # Sample time

    current_angle = 0.0
    gyro_integrated_angle = 0.0

    while current_angle < desired_angle:
        start_time = time.time()

        # Retrieve calibrated gyro data
        calibrated_gyro = get_calibrated_gyro_data(sensor)
        gyro_z = calibrated_gyro['z']

        # Calculate angular change since last iteration
        angle_z = gyro_z * dt
        gyro_integrated_angle += angle_z

        # Compute error and correction
        error = desired_angle - gyro_integrated_angle
        correction = kp * error

        # Adjust motor speeds
        left_speed = max(min_speed, max_speed - correction)
        right_speed = max(min_speed, max_speed + correction)

        # Ensure speed is within valid range (0 to 100)
        left_speed = min(max(left_speed, 0), 100)
        right_speed = min(max(right_speed, 0), 100)

        # Control motor direction and speed
        GPIO.output(left_front_in1, GPIO.LOW)
        GPIO.output(left_front_in2, GPIO.HIGH)
        GPIO.output(left_rear_in1, GPIO.HIGH)
        GPIO.output(left_rear_in2, GPIO.LOW)

        GPIO.output(right_front_in1, GPIO.LOW)
        GPIO.output(right_front_in2, GPIO.HIGH)
        GPIO.output(right_rear_in1, GPIO.HIGH)
        GPIO.output(right_rear_in2, GPIO.LOW)

        set_motor_speed(pwm_left_front, left_speed)
        set_motor_speed(pwm_left_rear, left_speed)
        set_motor_speed(pwm_right_front, right_speed)
        set_motor_speed(pwm_right_rear, right_speed)

        # Update current angle
        current_angle = gyro_integrated_angle

        # Print for debugging (optional)
        print(f"Current Angle: {current_angle:.2f} deg")

        # Ensure loop executes at consistent interval
        elapsed_time = time.time() - start_time
        if elapsed_time < dt:
            time.sleep(dt - elapsed_time)
        else:
            print("Warning: Loop iteration took longer than dt")

    # Stop motors after completing the turn
    stop_motors()


try:
    while True:
        # Move forward for 2 seconds (adjust as needed)
        move_forward()
        print("Moving forward...")
        time.sleep(2)

        # Stop motors and wait 1 second
        stop_motors()
        time.sleep(1)

        # Turn left using closed-loop control with MPU6050
        turn_left(sensor)

        # Stop motors and wait 1 second
        stop_motors()
        time.sleep(1)

except KeyboardInterrupt:
    print("\nExiting program.")

finally:
    # Clean up GPIO resources
    pwm_left_front.stop()
    pwm_left_rear.stop()
    pwm_right_front.stop()
    pwm_right_rear.stop()
    GPIO.cleanup()
