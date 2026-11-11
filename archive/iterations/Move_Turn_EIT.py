import os
import RPi.GPIO as GPIO
import time
from mpu6050 import mpu6050
import board
import busio
import adafruit_vl53l0x
import digitalio
import serial
import struct
import paho.mqtt.client as mqtt
import threading

# Constants and global variables for the servo control
servo_pin_1 = 17
servo_pin_2 = 27
servo_pin_3 = 22
servo_pin_4 = 4

pwm_1 = None
pwm_2 = None
pwm_3 = None
pwm_4 = None

# Constants and global variables for the voltage measurement
MSG_LEN = 9
CMD_SET_FREQ_HZ = 0xA1
CMD_GET_FREQ_HZ = 0xB1
CMD_SET_CURRENT_UA = 0xA2
CMD_GET_CURRENT_UA = 0xB2
CMD_SET_MEASURE_DURATION = 0xA3
CMD_GET_MEASURE_DURATION = 0xB3
CMD_START_MEASUREMENT = 0xA4
CMD_GET_IMPEDANCE = 0xB4

NUM_SAMPLES = 50
RETRY_LIMIT = 3

MQTT_BROKER = os.environ.get("MQTT_BROKER", "")
MQTT_PORT = 8883
MQTT_TOPIC = "getdata"
MQTT_USERNAME = os.environ.get("MQTT_USERNAME", "")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "")

mqtt_client = mqtt.Client(client_id="")
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
mqtt_client.tls_set()

def publish_to_mqtt(client, topic, message):
    client.publish(topic, message)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker.")
    else:
        print(f"Failed to connect, return code {rc}")


mqtt_client.on_connect = on_connect
mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
mqtt_client.loop_start()
            
print("Connecting to MQTT broker...")
while not mqtt_client.is_connected():
    time.sleep(0.1)

def open_serial_connection(port, baudrate, timeout):
    try:
        ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1, inter_byte_timeout=0.5)
        time.sleep(1)
        return ser
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        return None
    
ser = open_serial_connection('/dev/ttyUSB0', 115200, timeout=1)

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

# MPU6050 sensor address (verify your sensor's address)
sensor_address = 0x68
sensor = mpu6050(sensor_address)  # Ensure mpu6050 is correctly imported

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

# Number of samples to average for stability
NUM_SAMPLES = 20

# Offset adjustment based on calibration (if needed)
OFFSET = 20

# Define the XSHUT pins for each sensor
XSHUT_PINS = {
    'sensorFRONT': board.D5,
    'sensorLEFT': board.D6,
    'sensorRIGHT': board.D7
}

# New addresses for each sensor
NEW_ADDRESSES = {
    'sensorFRONT': 0x30,
    'sensorLEFT': 0x31,
    'sensorRIGHT': 0x32
}

# Exponential Moving Average (EMA) alpha
EMA_ALPHA = 1.0


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

# Function to stop all motors
def stop_motors_for_8sec():
    stop_motors()
    time.sleep(1)
    move_servos_down_and_publish_voltage(ser, mqtt_client)
    time.sleep(1)
    move_servos_up()
    
# Function to read Initial Voltage
def read_initial_voltage():
    time.sleep(1)
    move_servos_down_and_publish_voltage(ser, mqtt_client)
    time.sleep(1)
    move_servos_up()

# Function to move forward for 1 second
def move_forward_for_1_second(speed=20):
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
    stop_motors_for_8sec()

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

def initialize_sensor(i2c, xshut_pin, new_address):
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

def check_sensor(i2c, address):
    try:
        sensor = adafruit_vl53l0x.VL53L0X(i2c, address=address)
        # Perform a read to confirm sensor is responsive
        sensor.range
        return True
    except Exception:
        return False

def apply_ema_filter(ema, new_value, alpha=EMA_ALPHA):
    if ema is None:
        return new_value
    return alpha * new_value + (1 - alpha) * ema

def initialize_gpio():
    global pwm_1, pwm_2, pwm_3, pwm_4

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(servo_pin_1, GPIO.OUT)
    GPIO.setup(servo_pin_2, GPIO.OUT)
    GPIO.setup(servo_pin_3, GPIO.OUT)
    GPIO.setup(servo_pin_4, GPIO.OUT)

    pwm_1 = GPIO.PWM(servo_pin_1, 50)
    pwm_2 = GPIO.PWM(servo_pin_2, 50)
    pwm_3 = GPIO.PWM(servo_pin_3, 50)
    pwm_4 = GPIO.PWM(servo_pin_4, 50)

    pwm_1.start(0)
    pwm_2.start(0)
    pwm_3.start(0)
    pwm_4.start(0)
    

def set_servo_angle(pwm, angle):
    duty_cycle = 2.5 + (angle / 18.0)
    pwm.ChangeDutyCycle(duty_cycle)

def move_servos_to_initial_positions():
    initial_angle_1 = 120
    initial_angle_2 = 50
    initial_angle_3 = 120
    initial_angle_4 = 50

    set_servo_angle(pwm_1, initial_angle_1)
    set_servo_angle(pwm_2, initial_angle_2)
    set_servo_angle(pwm_3, initial_angle_3)
    set_servo_angle(pwm_4, initial_angle_4)
    print("Servos are UP")
    time.sleep(1)

def move_servos_down_and_publish_voltage(ser, mqtt_client):
    
    set_servo_angle(pwm_1, 170)
    set_servo_angle(pwm_2, 0)
    set_servo_angle(pwm_3, 170)
    set_servo_angle(pwm_4, 0)
    print("Servos are down")
    
    time.sleep(2)

    # Create a thread to handle voltage measurement and publishing
    voltage_thread = threading.Thread(target=measure_and_publish_voltage, args=(ser, mqtt_client))
    voltage_thread.start()

    time.sleep(1)

    # Wait for the voltage thread to complete before continuing
    voltage_thread.join()

def measure_and_publish_voltage(ser, mqtt_client):
    # Collect samples and calculate the average voltage
    voltage_samples = collect_samples(ser, NUM_SAMPLES)

    if voltage_samples:
        filtered_samples = filter_outliers(voltage_samples)
        average_voltage = sum(filtered_samples) / len(filtered_samples)
        print(f"Average Voltage: {average_voltage}")
        publish_to_mqtt(mqtt_client, MQTT_TOPIC, str(average_voltage))
    else:
        print("No valid samples collected.")

def move_servos_up():
    set_servo_angle(pwm_1, 120)
    set_servo_angle(pwm_2, 50)
    set_servo_angle(pwm_3, 120)
    set_servo_angle(pwm_4, 50)
    print("Servos are Up again")
    time.sleep(1)

def cleanup():
    pwm_1.stop()
    pwm_2.stop()
    pwm_3.stop()
    pwm_4.stop()
    GPIO.cleanup()



def send_command(ser, command, value1=0, value2=0):
    message = bytearray([command])
    message.extend(value1.to_bytes(4, 'big'))
    message.extend(value2.to_bytes(4, 'big'))

    ser.reset_output_buffer()
    ser.write(message)
    ser.reset_input_buffer()
    response = ser.read(MSG_LEN)

    if len(response) == MSG_LEN:
        if response[0] == 0xFF:
            print("Error: Error Message from ESP")
            return None, None, None
        else:
            received_command = response[0]
            received_data1 = int.from_bytes(response[1:5], byteorder='big')
            received_data2 = int.from_bytes(response[5:], byteorder='big')
            return received_command, received_data1, received_data2
    else:
        print(f"Error: Unexpected response length. Length = {len(response)}")
        return None, None, None

def admm_get(ser, command):
    return send_command(ser, command)

def admm_set(ser, command, value):
    return send_command(ser, command, value)

def admm_get_impedance(ser):
    message = bytearray([CMD_GET_IMPEDANCE])
    message.extend((0).to_bytes(4, 'big'))
    message.extend((0).to_bytes(4, 'big'))

    ser.reset_output_buffer()
    ser.write(message)
    ser.reset_input_buffer()
    response = ser.read(MSG_LEN)

    if len(response) == MSG_LEN:
        received_command = response[0]
        received_data1 = struct.unpack('>f', response[1:5])[0]
        received_data2 = struct.unpack('>f', response[5:])[0]
        return received_command, received_data1, received_data2
    else:
        print(f"Error: Unexpected response length. Length = {len(response)}")
        return None, None, None

def admm_start_and_get_measurement(ser):
    meas_time = admm_get(ser, CMD_START_MEASUREMENT)[1]
    
    if meas_time > 0:
        print(f"Measuring!!! Please wait {meas_time} milliseconds.")
        time.sleep(meas_time / 1000)
        
        received_command, abs_impedance, angle_impedance = admm_get_impedance(ser)
        return received_command, abs_impedance, angle_impedance
    else:
        print("Error: Measurement time is non-positive.")
        return None, None, None

def collect_samples(ser, num_samples):
    voltage_samples = []
    retries = 0
    i = 0

    while len(voltage_samples) < num_samples and retries < RETRY_LIMIT:
        received_command, abs_rms_voltage, angle_cur_vol = admm_start_and_get_measurement(ser)
        if received_command is not None:
            voltage_samples.append(abs_rms_voltage)
            print(f"Sample {len(voltage_samples)}: Voltage = {abs_rms_voltage}")
            retries = 0
        else:
            retries += 1
            print(f"Retry {retries} for sample {i+1}")
        i += 1

    if retries == RETRY_LIMIT:
        print("Exceeded maximum retries. Check your connection and device.")
    
    return voltage_samples

def filter_outliers(samples, threshold=2):
    median = sorted(samples)[len(samples) // 2]
    filtered_samples = [s for s in samples if abs(s - median) <= threshold * median]
    return filtered_samples

def main():
    i2c = busio.I2C(board.SCL, board.SDA)
    initialize_gpio()
    move_servos_to_initial_positions()
    read_initial_voltage()

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

    try:
        while True:
            # Move forward while checking the distance
            move_forward_for_1_second()
            distance_mm = sensors['sensorFRONT'].range - OFFSET
            ema_distances['sensorFRONT'] = apply_ema_filter(ema_distances['sensorFRONT'], distance_mm)
            print(f"Front sensor distance: {ema_distances['sensorFRONT']:.2f} mm")

            if ema_distances['sensorFRONT'] <= 100:
                print("Obstacle detected, stopping.")
                stop_motors()
                
                # Check left and right sensors
                distance_left_mm = sensors['sensorLEFT'].range - OFFSET
                ema_distances['sensorLEFT'] = apply_ema_filter(ema_distances['sensorLEFT'], distance_left_mm)
                print(f"Left sensor distance: {ema_distances['sensorLEFT']:.2f} mm")

                distance_right_mm = sensors['sensorRIGHT'].range - OFFSET
                ema_distances['sensorRIGHT'] = apply_ema_filter(ema_distances['sensorRIGHT'], distance_right_mm)
                print(f"Right sensor distance: {ema_distances['sensorRIGHT']:.2f} mm")

                # Decide the direction to turn
                if ema_distances['sensorLEFT'] > ema_distances['sensorRIGHT']:
                    print("Turning left.")
                    turn_left(sensor)
                else:
                    print("Turning right.")
                    turn_right(sensor)

            time.sleep(0.1)  # Adjust refresh rate as needed

    except KeyboardInterrupt:
        print("\nExiting program.")
    
    finally:
        pwm_left_front.stop()
        pwm_left_rear.stop()
        pwm_right_front.stop()
        pwm_right_rear.stop()
        GPIO.cleanup()
        cleanup()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        ser.close()

if __name__ == "__main__":
    main()
