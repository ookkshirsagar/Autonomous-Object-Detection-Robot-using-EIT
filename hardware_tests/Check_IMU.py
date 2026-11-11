from mpu6050 import mpu6050
from time import sleep

# Initialize sensor
sensor = mpu6050(0x68)

# Calibration constants for gyroscope (adjust these according to your calibration)
gyro_offset_x = -0.40
gyro_offset_y = 0.50
gyro_offset_z = -1.45

def get_calibrated_accel_data(sensor):
    raw_data = sensor.get_accel_data()
    calibrated_data = {
        'x': raw_data['x'] * (1 / 10.20),
        'y': raw_data['y'] * (1 / 9.85),
        'z': raw_data['z'] * (1 / 8.25)
    }
    return calibrated_data

def get_calibrated_gyro_data(sensor):
    raw_data = sensor.get_gyro_data()
    calibrated_data = {
        'x': raw_data['x'] - gyro_offset_x,
        'y': raw_data['y'] - gyro_offset_y,
        'z': raw_data['z'] - gyro_offset_z
    }
    return calibrated_data

while True:
    # Get raw sensor data
    accel_data = sensor.get_accel_data()
    gyro_data = sensor.get_gyro_data()
    temp = sensor.get_temp()

    # Get calibrated acceleration data
    calibrated_accel_data = get_calibrated_accel_data(sensor)

    # Get calibrated gyroscope data
    calibrated_gyro_data = get_calibrated_gyro_data(sensor)

    print("Raw Accelerometer data")
    print(f"x: {accel_data['x']:.2f} y: {accel_data['y']:.2f} z: {accel_data['z']:.2f}")

    print("Calibrated Accelerometer data")
    print(f"x: {calibrated_accel_data['x']:.2f} y: {calibrated_accel_data['y']:.2f} z: {calibrated_accel_data['z']:.2f}")

    print("Calibrated Gyroscope data")
    print(f"x: {calibrated_gyro_data['x']:.2f} y: {calibrated_gyro_data['y']:.2f} z: {calibrated_gyro_data['z']:.2f}")

    print("Temp: " + str(temp) + " C")
    sleep(0.5)
