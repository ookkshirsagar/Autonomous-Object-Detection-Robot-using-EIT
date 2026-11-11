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

def main():
    ser = open_serial_connection('COM5', 115200, timeout=1)
    if ser is None:
        return

    try:
        print("Set Frequency: ", admm_set(ser, CMD_SET_FREQ_HZ, 200)[1])
        print("Set Current: ", admm_set(ser, CMD_SET_CURRENT_UA, 330)[1])
        
        # Way 1 to get impedance:
        received_command, abs_rms_voltage, angle_cur_vol = admm_start_and_get_measurement(ser)
        if received_command is not None:
            print("Voltage: ", abs_rms_voltage)
            print("Phase:", angle_cur_vol)
        else:
            print("Failed to get measurement.")
        
        # Way 2 to get impedance (if needed):
        # meas_time = admm_get(ser, CMD_START_MEASUREMENT)
        # print("Start Measurement and wait ", meas_time[1], " milliseconds.")
        # time.sleep(meas_time[1]/1000)
        # received_command, abs_impedance, angle_impedance = admm_get_impedance(ser)
        # print("Impedance: ", abs_impedance)
        # print("Phase:", angle_impedance)
        
        time.sleep(1)
    finally:
        ser.close()

if __name__ == "__main__":
    main()