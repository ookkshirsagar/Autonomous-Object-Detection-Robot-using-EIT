import time
import board
import busio
import adafruit_vl53l0x
import digitalio
import RPi.GPIO as GPIO
from mpu6050 import mpu6050

# Number of samples to average for stability
NUM_SAMPLES = 20

# Offset adjustment based on calibration (if needed)
OFFSET = 20  # Adjust this value based on calibration measurements

# Define the XSHUT pins for each sensor
XSHUT_PINS = {
    'sensor_front': board.D5,
    'sensor_left': board.D6,
    'sensor_right': board.D7
}

# New addresses for each sensor
NEW_ADDRESSES = {
    'sensor_front': 0x30,
    'sensor_left': 0x31,
    'sensor_right': 0x32
}

# Exponential Moving Average (EMA) alpha
EMA_ALPHA = 0.2

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

# Servo Motor Pins
servo_pin_1 = 17
servo_pin_2 = 27
servo_pin_3 = 22
servo_pin_4 = 4

# Initial angles
initial_angle_1 = 170
initial_angle_2 = 0
initial_angle_3 = 170
initial_angle_4 = 0

# Initialize GPIO
print("Initializing GPIO...")
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Set up Left Motors
print("Setting up Left Motors...")
GPIO.setup(left_front_in1, GPIO.OUT)
GPIO.setup(left_front_in2, GPIO.OUT)
GPIO.setup(left_front_en, GPIO.OUT)
GPIO.setup(left_rear_in1, GPIO.OUT)
GPIO.setup(left_rear_in2, GPIO.OUT)
GPIO.setup(left_rear_en, GPIO.OUT)

# Set up Right Motors
print("Setting up Right Motors...")
GPIO.setup(right_front_in1, GPIO.OUT)
GPIO.setup(right_front_in2, GPIO.OUT)
GPIO.setup(right_front_en, GPIO.OUT)
GPIO.setup(right_rear_in1, GPIO.OUT)
GPIO.setup(right_rear_in2, GPIO.OUT)
GPIO.setup(right_rear_en, GPIO.OUT)

# Set up PWM for motor speed control
print("Setting up PWM for motor speed control...")
pwm_left_front = GPIO.PWM(left_front_en, 100)
pwm_left_rear = GPIO.PWM(left_rear_en, 100)
pwm_right_front = GPIO.PWM(right_front_en, 100)
pwm_right_rear = GPIO.PWM(right_rear_en, 100)

# Start PWM with a duty cycle of 0 (motors off)
pwm_left_front.start(0)
pwm_left_rear.start(0)
pwm_right_front.start(0)
pwm_right_rear.start(0)

# Set up Servo Motors
print("Setting up Servo Motors...")
GPIO.setup(servo_pin_1, GPIO.OUT)
GPIO.setup(servo_pin_2, GPIO.OUT)
GPIO.setup(servo_pin_3, GPIO.OUT)
GPIO.setup(servo_pin_4, GPIO.OUT)

# PWM frequency set to 50 Hz for all servos
pwm_1 = GPIO.PWM(servo_pin_1, 50)
pwm_2 = GPIO.PWM(servo_pin_2, 50)
pwm_3 = GPIO.PWM(servo_pin_3, 50)
pwm_4 = GPIO.PWM(servo_pin_4, 50)

# Start PWM with 0% duty cycle
pwm_1.start(0)
pwm_2.start(0)
pwm_3.start(0)
pwm_4.start(0)

# MPU6050 sensor address
sensor_address = 0x68  # Check your MPU6050 address

# Function to set motor speed
def set_motor_speed(pwm, speed):
    if speed < 0:
        speed = 0
    elif speed > 100:
        speed = 100
    pwm.ChangeDutyCycle(speed)

# Function to move forward
def move_forward(speed=20):
    print(f"Moving forward with speed: {speed}")
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

# Function to stop all motors
def stop_motors():
    print("Stopping all motors")
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

# Function to set servo angle
def set_servo_angle(pwm, angle):
    print(f"Setting servo angle to {angle} degrees")
    duty_cycle = 2.5 + (angle / 18.0)
    pwm.ChangeDutyCycle(duty_cycle)

# Function to move servos down and up
def move_servos():
    print("Moving servos down")
    set_servo_angle(pwm_1, 140)
    set_servo_angle(pwm_2, 30)
    set_servo_angle(pwm_3, 140)
    set_servo_angle(pwm_4, 30)
    time.sleep(1)  # Allow time for servos to move down
    print("Waiting for 15 seconds")
    time.sleep(15)
    print("Moving servos up")
    set_servo_angle(pwm_1, 170)
    set_servo_angle(pwm_2, 0)
    set_servo_angle(pwm_3, 170)
    set_servo_angle(pwm_4, 0)
    time.sleep(1)  # Allow time for servos to move up

# Function to move servos up initially
def move_initial_servos():
    print("Moving servos UP ")
    set_servo_angle(pwm_1, 140)
    set_servo_angle(pwm_2, 30)
    set_servo_angle(pwm_3, 140)
    set_servo_angle(pwm_4, 30)


# Function to turn left with gyro control
def turn_left(sensor, angle=82.0, speed=100):
    print(f"Turning left by {angle} degrees")
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
def turn_right(sensor, angle=86, speed=100):
    print(f"Turning right by {angle} degrees")
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
        turn_speed = min(max(speed + correction, 30), 100)

        # Left motors forward
        GPIO.output(left_front_in1, GPIO.HIGH)
        GPIO.output(left_front_in2, GPIO.LOW)
        GPIO.output(left_rear_in1, GPIO.LOW)
        GPIO.output(left_rear_in2, GPIO.HIGH)

        # Right motors backward
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

# Function to move forward for a specified duration
def move_forward_for_duration(duration, speed=20):
    print(f"Moving forward for {duration} seconds with speed: {speed}")
    move_forward(speed)
    time.sleep(duration)
    stop_motors()

# Get calibrated gyro data
def get_calibrated_gyro_data(sensor):
    print("Getting calibrated gyro data")
    gyro_data = sensor.get_gyro_data()
    calibration = sensor.get_calibration()
    calibrated_data = {
        'x': gyro_data['x'] - calibration['gyro_offset']['x'],
        'y': gyro_data['y'] - calibration['gyro_offset']['y'],
        'z': gyro_data['z'] - calibration['gyro_offset']['z']
    }
    return calibrated_data

# Apply Exponential Moving Average (EMA) filter
def apply_ema_filter(ema, new_value, alpha=EMA_ALPHA):
    print(f"Applying EMA filter with alpha={alpha}")
    if ema is None:
        return new_value
    return alpha * new_value + (1 - alpha) * ema

# Check if sensor is initialized
def check_sensor(i2c, address):
    print(f"Checking sensor at address {hex(address)}")
    try:
        sensor = adafruit_vl53l0x.VL53L0X(i2c, address=address)
        # Perform a read to confirm sensor is responsive
        sensor.range
        return True
    except Exception:
        return False

# Initialize sensor with XSHUT pin and new address
def initialize_sensor(i2c, xshut_pin, new_address):
    print(f"Initializing sensor with XSHUT pin {xshut_pin} and new address {hex(new_address)}")
    try:
        xshut = digitalio.DigitalInOut(xshut_pin)
        xshut.direction = digitalio.Direction.OUTPUT
        xshut.value = False  # Keep the sensor in reset state

        time.sleep(0.1)
        xshut.value = True  # Bring the sensor out of reset

        # Try to initialize sensor at the default address
        sensor = adafruit_vl53l0x.VL53L0X(i2c)
        
        # Attempt to change the sensor address
        sensor.set_address(new_address)
        print(f"VL53L0X sensor initialized and set to address {hex(new_address)}.")

        return sensor

    except Exception as e:
        print(f"Error initializing VL53L0X sensor: {e}")
        exit()

# Main function
def main():
    print("Starting main program...")
    
    i2c = busio.I2C(board.SCL, board.SDA)
    
    # Set initial angles for servos
    set_servo_angle(pwm_1, initial_angle_1)
    set_servo_angle(pwm_2, initial_angle_2)
    set_servo_angle(pwm_3, initial_angle_3)
    set_servo_angle(pwm_4, initial_angle_4)

    # Initialize sensors with new addresses
    sensors = {}
    ema_distances = {}
    for key, xshut_pin in XSHUT_PINS.items():
        if not check_sensor(i2c, NEW_ADDRESSES[key]):
            sensors[key] = initialize_sensor(i2c, xshut_pin, NEW_ADDRESSES[key])
        else:
            sensors[key] = adafruit_vl53l0x.VL53L0X(i2c, address=NEW_ADDRESSES[key])
            print(f"VL53L0X sensor already initialized at address {hex(NEW_ADDRESSES[key])}")
        ema_distances[key] = None
        time.sleep(1)  # Small delay to ensure the address change takes effect

    sensor = mpu6050(sensor_address)
    
    try:
        while True:
            print("Looping in main program...")
            # Move servos up initially.
            move_initial_servos()

            # Move forward for 2 seconds, then stop for 20 seconds
            move_forward_for_duration(1)
            stop_motors()
            
            # Move servos during the 20-second stop period
            move_servos()
            time.sleep(1)

            # Check TOF sensor readings
            front_distance = sensors['sensor_front'].range
            left_distance = sensors['sensor_left'].range
            right_distance = sensors['sensor_right'].range

            print(f"TOF Sensor Readings - Front: {front_distance}, Left: {left_distance}, Right: {right_distance}")

            # Apply EMA filter to sensor readings
            ema_distances['sensor_front'] = apply_ema_filter(ema_distances['sensor_front'], front_distance)
            ema_distances['sensor_left'] = apply_ema_filter(ema_distances['sensor_left'], left_distance)
            ema_distances['sensor_right'] = apply_ema_filter(ema_distances['sensor_right'], right_distance)

            if ema_distances['sensor_front'] <= 100:
                if ema_distances['sensor_left'] <= 60:
                    turn_right(sensor)
                else:
                    turn_left(sensor)

            move_forward_for_duration(1)
            stop_motors()

            # Move servos during the 20-second stop period
            move_servos()
            time.sleep(20)
            

            if ema_distances['sensor_right'] >= 200:
                turn_left(sensor)
    
    except KeyboardInterrupt:
        print("\nExiting program.")
        
    finally:
        pwm_1.stop()
        pwm_2.stop()
        pwm_3.stop()
        pwm_4.stop()
        GPIO.cleanup()

if __name__ == "__main__":
    main()
