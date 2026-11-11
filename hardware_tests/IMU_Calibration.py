from mpu6050 import mpu6050
from time import sleep

# Constants for MPU6050 sensor
SENSOR_ADDRESS = 0x68

# Calibration constants for accelerometer (adjust according to your calibration)
ACCEL_CALIB_FACTOR_X = 1 / 10.20
ACCEL_CALIB_FACTOR_Y = 1 / 9.85
ACCEL_CALIB_FACTOR_Z = 1 / 8.25

# Calibration offsets for gyroscope (adjust according to your calibration)
GYRO_OFFSET_X = -0.40
GYRO_OFFSET_Y = 0.50
GYRO_OFFSET_Z = -1.45

def initialize_sensor(address):
    """Initialize MPU6050 sensor with given I2C address."""
    sensor = mpu6050(address)
    return sensor

def get_calibrated_accel_data(sensor):
    """Retrieve and calibrate accelerometer data."""
    raw_data = sensor.get_accel_data()
    calibrated_data = {
        'x': raw_data['x'] * ACCEL_CALIB_FACTOR_X,
        'y': raw_data['y'] * ACCEL_CALIB_FACTOR_Y,
        'z': raw_data['z'] * ACCEL_CALIB_FACTOR_Z
    }
    return calibrated_data

def get_calibrated_gyro_data(sensor):
    """Retrieve and calibrate gyroscope data."""
    raw_data = sensor.get_gyro_data()
    calibrated_data = {
        'x': raw_data['x'] - GYRO_OFFSET_X,
        'y': raw_data['y'] - GYRO_OFFSET_Y,
        'z': raw_data['z'] - GYRO_OFFSET_Z
    }
    return calibrated_data

def main():
    """Main function to run the sensor data collection and printing."""
    # Initialize sensor
    sensor = initialize_sensor(SENSOR_ADDRESS)

    while True:
        # Get raw sensor data
        accel_data = sensor.get_accel_data()
        gyro_data = sensor.get_gyro_data()
        temp = sensor.get_temp()

        # Get calibrated acceleration data
        calibrated_accel_data = get_calibrated_accel_data(sensor)

        # Get calibrated gyroscope data
        calibrated_gyro_data = get_calibrated_gyro_data(sensor)

        # Print sensor data
        print("Calibrated Accelerometer data")
        print(f"x: {calibrated_accel_data['x']:.2f} y: {calibrated_accel_data['y']:.2f} z: {calibrated_accel_data['z']:.2f}")

        print("Calibrated Gyroscope data")
        print(f"x: {calibrated_gyro_data['x']:.2f} y: {calibrated_gyro_data['y']:.2f} z: {calibrated_gyro_data['z']:.2f}")

        print(f"Temp: {temp:.1f} C")
        
        sleep(0.5)  # Sleep for 0.5 seconds

if __name__ == "__main__":
    main()
