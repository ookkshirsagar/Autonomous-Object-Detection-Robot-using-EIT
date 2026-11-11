import serial
import time
import struct

MSG_LEN = 9
CMD_SET_FREQ_HZ = 0xA1
CMD_GET_FREQ_HZ = 0xB1
CMD_SET_CURRENT_UA = 0xA2
CMD_GET_CURRENT_UA = 0xB2
CMD_SET_MEASURE_DURATION = 0xA3
CMD_GET_MEASURE_DURATION = 0xB3
CMD_START_MEASUREMENT = 0xA4
CMD_GET_IMPEDANCE = 0xB4

NUM_SAMPLES = 50  # Increase the number of samples for better averaging
RETRY_LIMIT = 3  # Number of retries for each sample in case of failure

def open_serial_connection(port, baudrate, timeout):
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout, inter_byte_timeout=0.5)
        time.sleep(1)  # Wait for the device to initialize
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
        received_data1 = struct.unpack('>f', response[1:5])[0]  # Interpret bytes as float
        received_data2 = struct.unpack('>f', response[5:])[0]   # Interpret bytes as float
        return received_command, received_data1, received_data2
    else:
        print(f"Error: Unexpected response length. Length = {len(response)}")
        return None, None, None

def admm_start_and_get_measurement(ser):
    meas_time = admm_get(ser, CMD_START_MEASUREMENT)[1]
    
    if meas_time > 0:
        print(f"Start Measurement and wait {meas_time} milliseconds.")
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
            retries = 0  # Reset retries after a successful read
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
    ser = open_serial_connection('COM5', 115200, timeout=1)
    if ser is None:
        return

    try:
        print("Set Frequency: ", admm_set(ser, CMD_SET_FREQ_HZ, 200)[1])
        print("Set Current: ", admm_set(ser, CMD_SET_CURRENT_UA, 330)[1])
        
        # Collect samples and calculate the average
        voltage_samples = collect_samples(ser, NUM_SAMPLES)

        if voltage_samples:
            filtered_samples = filter_outliers(voltage_samples)
            average_voltage = sum(filtered_samples) / len(filtered_samples)
            print(f"Average Voltage: {average_voltage}")
        else:
            print("No valid samples collected.")
        
        time.sleep(1)
    finally:
        ser.close()

if __name__ == "__main__":
    main()
