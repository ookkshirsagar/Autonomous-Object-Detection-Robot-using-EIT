#!/home/admm2024/admm/bin/python

import time
import board
import busio
import adafruit_vl53l0x

# Number of samples to average
NUM_SAMPLES = 20

# Offset adjustment based on calibration (if needed)
OFFSET = 20        # Adjust this value based on calibration measurements

def initialize_sensor():
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        sensor = adafruit_vl53l0x.VL53L0X(i2c)
        print("VL53L0X sensor initialized.")
        return sensor
    except Exception as e:
        print(f"Error initializing VL53L0X sensor: {e}")
        exit()

def configure_sensor(sensor):
    try:
        # Set timing budget (higher values are more accurate but slower)
        sensor.measurement_timing_budget = 50000  # 33ms
        print("Measurement timing budget set to 33ms.")
    except Exception as e:
        print(f"Error configuring VL53L0X sensor: {e}")
        exit()

def get_average_distance(sensor, num_samples=NUM_SAMPLES):
    distances = []
    for _ in range(num_samples):
        try:
            sensor.do_range_measurement()
            distance = sensor.range
            distances.append(distance)
        except RuntimeError as e:
            print(f"Error reading distance: {e}")
        time.sleep(0.01)  # Small delay between samples to avoid I2C bus overflow

    if distances:
        # Use a simple moving average to smooth the readings
        average_distance = sum(distances) / len(distances)
        return average_distance
    else:
        return None

def main():
    sensor = initialize_sensor()
    configure_sensor(sensor)
    
    try:
        while True:
            average_distance = get_average_distance(sensor)
            if average_distance is not None:
                # Apply offset adjustment
                adjusted_distance = average_distance - OFFSET
                print(f"Averaged Range: {adjusted_distance:.2f} mm")
            else:
                print("No valid distance readings.")
            time.sleep(0.01)  # Adjust the sleep time as needed for your application

    except KeyboardInterrupt:
        print("\nExiting program.")

if __name__ == "__main__":
    main()
