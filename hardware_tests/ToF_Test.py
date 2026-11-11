#!/home/admm2024/admm/bin/python

import time
import board
import busio
import adafruit_vl53l0x

# Define an optional offset based on your calibration measurements
OFFSET = 10  # Adjust this value based on your calibration measurements

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
        sensor.measurement_timing_budget = 200000  # 200ms
        print("Measurement timing budget set to 200ms.")
        
        # Start continuous mode
        sensor.start_continuous()
        print("Continuous mode started.")
    except Exception as e:
        print(f"Error configuring VL53L0X sensor: {e}")
        exit()

def get_average_distance(sensor, num_samples=10, offset=OFFSET):
    distances = []
    for _ in range(num_samples):
        try:
            distance = sensor.range + offset
            # Add bounds checking for the distance values
            if 30 <= distance <= 1200:
                distances.append(distance)
            else:
                print(f"Out of bounds distance reading: {distance} mm")
        except RuntimeError as e:
            print(f"Error reading distance: {e}")
        time.sleep(0.01)  # Small delay between samples to avoid I2C bus overflow

    if distances:
        return sum(distances) / len(distances)
    else:
        return None

def main():
    sensor = initialize_sensor()
    configure_sensor(sensor)
    
    try:
        while True:
            average_distance = get_average_distance(sensor, num_samples=10)
            if average_distance is not None:
                print(f"Averaged Range: {average_distance:.2f} mm")
            else:
                print("No valid distance readings.")
            time.sleep(1.0)  # Adjust the sleep time as needed for your application

    except KeyboardInterrupt:
        print("\nExiting program.")

    finally:
        sensor.stop_continuous()
        print("Continuous mode stopped.")

if __name__ == "__main__":
    main()
