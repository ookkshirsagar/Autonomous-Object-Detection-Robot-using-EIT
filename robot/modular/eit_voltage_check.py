import os
import serial
import time
import struct
import paho.mqtt.client as mqtt

class EITVoltageCheck:
    MSG_LEN = 9
    CMD_SET_FREQ_HZ = 0xA1
    CMD_GET_FREQ_HZ = 0xB1
    CMD_SET_CURRENT_UA = 0xA2
    CMD_GET_CURRENT_UA = 0xB2
    CMD_SET_MEASURE_DURATION = 0xA3
    CMD_GET_MEASURE_DURATION = 0xB3
    CMD_START_MEASUREMENT = 0xA4
    CMD_GET_IMPEDANCE = 0xB4

    NUM_SAMPLES = 50  # Number of samples for better averaging
    RETRY_LIMIT = 3  # Number of retries for each sample in case of failure

    MQTT_BROKER = os.environ.get("MQTT_BROKER", "")  # Replace with your MQTT broker address
    MQTT_PORT = 8883  # Default MQTT port for TLS
    MQTT_TOPIC = "getdata"  # MQTT topic to publish to
    MQTT_USERNAME = os.environ.get("MQTT_USERNAME", "")
    MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "")

    def __init__(self, serial_port='/dev/ttyUSB0', baudrate=115200, timeout=1):
        self.ser = self.open_serial_connection(serial_port, baudrate, timeout)
        if self.ser is None:
            raise Exception("Failed to open serial connection.")

        self.mqtt_client = mqtt.Client(client_id="")
        self.mqtt_client.username_pw_set(self.MQTT_USERNAME, self.MQTT_PASSWORD)
        self.mqtt_client.tls_set()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.connect(self.MQTT_BROKER, self.MQTT_PORT)
        self.mqtt_client.loop_start()
        print("Connecting to MQTT broker...")
        while not self.mqtt_client.is_connected():
            time.sleep(0.1)

    def open_serial_connection(self, port, baudrate, timeout):
        try:
            ser = serial.Serial(port, baudrate, timeout=timeout, inter_byte_timeout=0.5)
            time.sleep(1)  # Wait for the device to initialize
            return ser
        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")
            return None

    def send_command(self, command, value1=0, value2=0):
        message = bytearray([command])
        message.extend(value1.to_bytes(4, 'big'))
        message.extend(value2.to_bytes(4, 'big'))

        self.ser.reset_output_buffer()
        self.ser.write(message)
        self.ser.reset_input_buffer()
        response = self.ser.read(self.MSG_LEN)

        if len(response) == self.MSG_LEN:
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

    def admm_get(self, command):
        return self.send_command(command)

    def admm_set(self, command, value):
        return self.send_command(command, value)

    def admm_get_impedance(self):
        message = bytearray([self.CMD_GET_IMPEDANCE])
        message.extend((0).to_bytes(4, 'big'))
        message.extend((0).to_bytes(4, 'big'))

        self.ser.reset_output_buffer()
        self.ser.write(message)
        self.ser.reset_input_buffer()
        response = self.ser.read(self.MSG_LEN)

        if len(response) == self.MSG_LEN:
            received_command = response[0]
            received_data1 = struct.unpack('>f', response[1:5])[0]  # Interpret bytes as float
            received_data2 = struct.unpack('>f', response[5:])[0]   # Interpret bytes as float
            return received_command, received_data1, received_data2
        else:
            print(f"Error: Unexpected response length. Length = {len(response)}")
            return None, None, None

    def admm_start_and_get_measurement(self):
        meas_time = self.admm_get(self.CMD_START_MEASUREMENT)[1]
        
        if meas_time > 0:
            print(f"Measuring!!! Please,wait {meas_time} milliseconds.")
            time.sleep(meas_time / 1000)
            
            received_command, abs_impedance, angle_impedance = self.admm_get_impedance()
            return received_command, abs_impedance, angle_impedance
        else:
            print("Error: Measurement time is non-positive.")
            return None, None, None

    def collect_samples(self, num_samples):
        voltage_samples = []
        retries = 0
        i = 0

        while len(voltage_samples) < num_samples and retries < self.RETRY_LIMIT:
            received_command, abs_rms_voltage, angle_cur_vol = self.admm_start_and_get_measurement(self.ser)
            if received_command is not None:
                voltage_samples.append(abs_rms_voltage)
                print(f"Sample {len(voltage_samples)}: Voltage = {abs_rms_voltage}")
                retries = 0  # Reset retries after a successful read
            else:
                retries += 1
                print(f"Retry {retries} for sample {i+1}")
            i += 1

        if retries == self.RETRY_LIMIT:
            print("Exceeded maximum retries. Check your connection and device.")
        
        return voltage_samples

    def filter_outliers(self, samples, threshold=2):
        median = sorted(samples)[len(samples) // 2]
        filtered_samples = [s for s in samples if abs(s - median) <= threshold * median]
        return filtered_samples

    def publish_to_mqtt(self, topic, message):
        self.mqtt_client.publish(topic, message)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker.")
        else:
            print(f"Failed to connect, return code {rc}")

    def run(self):
        print("Set Frequency: ", self.admm_set(self.CMD_SET_FREQ_HZ, 200)[1])
        print("Set Current: ", self.admm_set(self.CMD_SET_CURRENT_UA, 150)[1])

        # Collect samples and calculate the average
        voltage_samples = self.collect_samples(self.NUM_SAMPLES)

        if voltage_samples:
            filtered_samples = self.filter_outliers(voltage_samples)
            average_voltage = sum(filtered_samples) / len(filtered_samples)
            print(f"Average Voltage: {average_voltage}")
            self.publish_to_mqtt(self.MQTT_TOPIC, str(average_voltage))
        else:
            print("No valid samples collected.")
        
        time.sleep(1)

    def cleanup(self):
        self.ser.close()
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
