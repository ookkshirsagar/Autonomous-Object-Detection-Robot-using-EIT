import RPi.GPIO as GPIO
import time
import board
import busio
import digitalio
from adafruit_vl53l0x import VL53L0X
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

# MPU6050 sensor address
sensor_address = 0x68  # Check your MPU6050 address
sensor = mpu6050(sensor_address)

# ToF Sensor Configuration
NUM_SAMPLES = 20
OFFSET = 20
XSHUT_PINS = {
    'front': board.D5  # Assuming front ToF sensor is connected to D5
}
NEW_ADDRESSES = {
    'front': 0x30  # Replace with your front sensor's new address if changed
}
EMA_ALPHA = 1.0

def initialize_sensor(i2c, xshut_pin, new_address):
    try:
        xshut = digitalio.DigitalInOut(xshut_pin)
        xshut.direction = digitalio.Direction.OUTPUT
        xshut.value = False  # Keep the sensor in reset state

        time.sleep(0.1)
        xshut.value = True  # Bring the sensor out of reset

        # Try to initialize sensor at the default address
        sensor = VL53L0X(i2c)
        
        # Attempt to change the sensor address
        sensor.set_address(new_address)
        print(f"VL53L0X sensor initialized and set to address {hex(new_address)}.")

        return sensor

    except Exception as e:
        print(f"Error initializing VL53L0X sensor: {e}")
        exit()

def check_sensor(i2c, address):
    try:
        sensor = VL53L0X(i2c, address=address)
        # Perform a read to confirm sensor is responsive
        sensor.range
        return True
    except Exception:
        return False

def apply_ema_filter(ema, new_value, alpha=EMA_ALPHA):
    if ema is None:
        return new_value
    return alpha * new_value + (1 - alpha) * ema

def stop_motors():
    # Function to stop all motors
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

def set_motor_speed(pwm, speed):
    if speed < 0:
        speed = 0
    elif speed > 100:
        speed = 100
    pwm.ChangeDutyCycle(speed)

def move_forward_for_1_second(speed=20):
    # Function to move forward for 1 second
    GPIO.output(left_front_in1, GPIO.HIGH)
    GPIO.output(left_front_in2, GPIO.LOW)
    GPIO.output(left_rear_in1, GPIO.LOW)
    GPIO.output(left_rear_in2, GPIO.HIGH)

    GPIO.output(right_front_in1, GPIO.LOW)
    GPIO.output(right_front_in2, GPIO.HIGH)
    GPIO.output(right_rear_in1, GPIO.HIGH)
    GPIO.output(right_rear_in2, GPIO.LOW)

    set_motor_speed(pwm_left_front, speed)
    set_motor_speed(pwm_left_rear, speed)
    set_motor_speed(pwm_right_front, speed)
    set_motor_speed(pwm_right_rear, speed)

    time.sleep(1)
    stop_motors()

def main():

    # Initialize ToF sensors
    i2c = busio.I2C(board.SCL, board.SDA)
    sensors = {}
    ema_distances = {}
    for key, xshut_pin in XSHUT_PINS.items():
        if not check_sensor(i2c, NEW_ADDRESSES[key]):
            sensors[key] = initialize_sensor(i2c, xshut_pin, NEW_ADDRESSES[key])
        else:
            sensors[key] = VL53L0X(i2c, address=NEW_ADDRESSES[key])
            print(f"VL53L0X sensor already initialized at address {hex(NEW_ADDRESSES[key])}")
        ema_distances[key] = None
        time.sleep(1)  # Small delay to ensure the address change takes effect

    try:
        print("Waiting for sensors to initialize...")
        time.sleep(5)  # Wait for sensors to initialize
        
        while True:
            move_forward_for_1_second()

            # Check front ToF sensor during movement
            front_distance = sensors['front'].range - OFFSET
            ema_distances['front'] = apply_ema_filter(ema_distances['front'], front_distance)
            print(f"Front sensor distance: {ema_distances['front']:.2f} mm")

            if ema_distances['front'] <= 100:
                print("Obstacle detected, stopping.")
                stop_motors()
                break

    except KeyboardInterrupt:
        print("\nExiting program.")

    finally:
        # Clean up GPIO and PWM
        GPIO.cleanup()
        for key in sensors:
            sensors[key].deinit()

if __name__ == "__main__":
    main()
