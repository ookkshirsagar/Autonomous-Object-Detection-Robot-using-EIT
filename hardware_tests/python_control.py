import serial
import time
import struct

MSG_LEN = 9
CMD_SET_FREQ_HZ =   0xA1
CMD_GET_FREQ_HZ  =  0xB1
CMD_SET_CURRENT_UA = 0xA2
CMD_GET_CURRENT_UA = 0xB2
CMD_SET_MEASURE_DURATION =  0xA3
CMD_GET_MEASURE_DURATION = 0xB3
CMD_START_MEASUREMENT = 0xA4
CMD_GET_IMPEDANCE = 0xB4

# Open Connection I would keep the connection the whole process
ser = serial.Serial('COM5', 115200, timeout=1, inter_byte_timeout=0.5)
time.sleep(1) # add some delay for the esp to set up

def admm_get(command):
    # Construct message
    message = bytearray([command])
    message.extend((0).to_bytes(4, 'big'))  
    message.extend((0).to_bytes(4, 'big'))
    
    # Send message and receive response
    ser.reset_output_buffer()
    ser.write(message)
    ser.reset_input_buffer()
    response = ser.read(MSG_LEN)

    # Process response
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
        print("Error: Unexpected response length. Length = ", len(response))
        return None, None, None

def admm_set(command, value):
    # Construct message
    message = bytearray([command])
    message.extend(value.to_bytes(4, 'big'))
    message.extend((0).to_bytes(4, 'big'))

    # Send message and receive response
    ser.reset_output_buffer()
    ser.write(message)
    ser.reset_input_buffer()
    response = ser.read(MSG_LEN)

    # Process response
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
        print("Error: Unexpected response length. Length = ", len(response))
        return None, None, None
    
def admm_get_impedance():
    # Create message
    message = bytearray([CMD_GET_IMPEDANCE])
    message.extend((0).to_bytes(4, 'big'))
    message.extend((0).to_bytes(4, 'big'))
    
    ser.reset_output_buffer()
    ser.write(message)
    ser.reset_input_buffer()
    response = ser.read(MSG_LEN)
    
    # Parse response
    if len(response) == MSG_LEN:
        received_command = response[0]
        received_data1 = struct.unpack('>f', response[1:5])[0]  # Interpret bytes as float
        received_data2 = struct.unpack('>f', response[5:])[0]   # Interpret bytes as float
        
        return received_command, received_data1, received_data2
    else:
        print("Error: Unexpected response length. Lenght = ", len(response))        
        return None, None, None 


def admm_start_and_get_measurement():
    # Get measurement duration
    meas_time = admm_get(CMD_START_MEASUREMENT)[1]
    
    if meas_time > 0:
        print("Start Measurement and wait ", meas_time, " milliseconds.")
        time.sleep(meas_time / 1000)
        
        # Retrieve impedance data
        received_command, abs_impedance, angle_impedance = admm_get_impedance()
        return received_command, abs_impedance, angle_impedance
    else:
        return None, None, None

print("Set Frequency: ", admm_set(CMD_SET_FREQ_HZ, 200)[1])
print("Set Current: ", admm_set(CMD_SET_CURRENT_UA, 150)[1])
print("Set Duration: ", admm_set(CMD_SET_MEASURE_DURATION, 2)[1])

# Way 1 to get impedance:
received_command, abs_rms_voltage, angle_cur_vol = admm_start_and_get_measurement()
print("Voltage: ", abs_rms_voltage)
print("Phase:", angle_cur_vol)

# Way 2 to get impedance:
# meas_time = admm_get(CMD_START_MEASUREMENT)
# print("Start Measurement and wait ", meas_time[1], " milliseconds.")
# time.sleep(meas_time[1]/1000)
# received_command, abs_impedance, angle_impedance = admm_get_impedance()
# print("Impedance: ", abs_impedance)
# print("Phase:", angle_impedance)

# Close Connection
time.sleep(1)
ser.close()