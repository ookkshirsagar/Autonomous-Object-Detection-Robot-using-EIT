#!/home/admm2024/admm/bin/python

import time
import board
import busio
import adafruit_vl53l0x

# Robot chassis dimensions
chassis_width = 240  # mm
chassis_length = 360  # mm
center_x = chassis_width / 2
center_y = chassis_length / 2

# Initialize I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize TOF sensors
sensor1 = adafruit_vl53l0x.VL53L0X(i2c)
sensor2 = adafruit_vl53l0x.VL53L0X(i2c)
sensor3 = adafruit_vl53l0x.VL53L0X(i2c)
sensor4 = adafruit_vl53l0x.VL53L0X(i2c)

sensors = [sensor1, sensor2, sensor3, sensor4]

# Function to perform calibration of each sensor
def calibrate_sensors():
    for sensor in sensors:
        # Perform calibration procedure (adjust as needed)
        sensor.start_calibration()
        print(f"Calibrating sensor {sensor}")
        time.sleep(2)  # Adjust delay based on sensor requirements
        sensor.stop_calibration()
        print(f"Calibration complete for sensor {sensor}")

# Function to tare (zero) the sensors
def tare_sensors():
    for sensor in sensors:
        # Perform taring procedure (adjust as needed)
        sensor.tare()
        print(f"Taring complete for sensor {sensor}")

# Function to read distance from each sensor
def read_distances():
    distances = []
    for sensor in sensors:
        distances.append(sensor.range)
    return distances

try:
    # Perform initial calibration and taring
    calibrate_sensors()
    tare_sensors()

    while True:
        # Read distances from sensors
        distances = read_distances()

        # Calculate robot's position relative to its center
        robot_x = center_x + (distances[3] - distances[2]) / 2  # Adjust for right and left sensors
        robot_y = center_y + (distances[1] - distances[0]) / 2  # Adjust for front and back sensors

        # Print or use robot's position
        print(f"Robot position: ({robot_x:.2f} mm, {robot_y:.2f} mm)")

        # Delay between readings (adjust as needed)
        time.sleep(1)

except KeyboardInterrupt:
    print("\nExiting program.")
finally:
    # Clean up GPIO and I2C resources
    pass
