#!/home/admm2024/admm/bin/python

import time
import board
import busio
import adafruit_vl53l0x

# Function to initialize and return a VL53L0X sensor instance
def initialize_sensor(i2c):
    sensor = adafruit_vl53l0x.VL53L0X(i2c)
    sensor.measurement_timing_budget = 200000  # Adjust timing budget if needed (in microseconds)
    return sensor

# Initialize I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize all 4 sensors
sensor1 = initialize_sensor(i2c)
sensor2 = initialize_sensor(i2c)
sensor3 = initialize_sensor(i2c)
sensor4 = initialize_sensor(i2c)

sensors = [sensor1, sensor2, sensor3, sensor4]

try:
    while True:
        for index, sensor in enumerate(sensors):
            # Read the distance in millimeters
            distance = sensor.range
            print(f"Sensor {index+1}: Distance: {distance} mm")
        
        # Delay between readings (adjust as needed)
        time.sleep(1)

except KeyboardInterrupt:
    print("\nExiting program.")
finally:
    # Clean up GPIO and I2C resources
    pass
