import os
import RPi.GPIO as GPIO
import time
import serial
import struct
import paho.mqtt.client as mqtt
import threading

# Constants and global variables for the servo control
servo_pin_1 = 17
servo_pin_2 = 27
servo_pin_3 = 4
servo_pin_4 = 22

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

    # Create a thread to handle voltage measurement and publishing
    voltage_thread = threading.Thread(target=measure_and_publish_voltage, args=(ser, mqtt_client))
    voltage_thread.start()

    time.sleep(3)

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

def open_serial_connection(port, baudrate, timeout):
    try:
        ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1, inter_byte_timeout=0.5)
        time.sleep(1)
        return ser
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        return None

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

def publish_to_mqtt(client, topic, message):
    client.publish(topic, message)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker.")
    else:
        print(f"Failed to connect, return code {rc}")
    


def main():
    initialize_gpio()
    move_servos_to_initial_positions()


    ser = open_serial_connection('/dev/ttyUSB0', 115200, timeout=1)
    if ser is None:
        return
    print("Set Frequency: ", admm_set(ser, CMD_SET_FREQ_HZ, 200)[1])
    print("Set Current: ", admm_set(ser, CMD_SET_CURRENT_UA, 200)[1])
    
    try:
        # Set Frequency and Current
        print("Set Frequency: ", admm_set(ser, CMD_SET_FREQ_HZ, 200)[1])
        print("Set Current: ", admm_set(ser, CMD_SET_CURRENT_UA, 200)[1])

        mqtt_client = mqtt.Client(client_id="")
        mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        mqtt_client.tls_set()
        mqtt_client.on_connect = on_connect
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
        mqtt_client.loop_start()
        
        print("Connecting to MQTT broker...")
        while not mqtt_client.is_connected():
            time.sleep(0.1)

        while True:
            move_servos_down_and_publish_voltage(ser, mqtt_client)
            move_servos_up()
            time.sleep(1)  # Wait before the next iteration

    except KeyboardInterrupt:
        print("Program stopped by user.")

    finally:
        cleanup()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        ser.close()

if __name__ == "__main__":
    main()
