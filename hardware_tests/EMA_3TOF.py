#!/home/admm2024/admm/bin/python

import time
import board
import busio
import adafruit_vl53l0x
import digitalio

# Number of samples to average for stability
NUM_SAMPLES = 20

# Offset adjustment based on calibration (if needed)
OFFSET = 20  # Adjust this value based on calibration measurements

# Define the XSHUT pins for each sensor
XSHUT_PINS = {
    'sensor1': board.D5,
    'sensor2': board.D6,
    'sensor3': board.D7
}

# New addresses for each sensor
NEW_ADDRESSES = {
    'sensor1': 0x30,
    'sensor2': 0x31,
    'sensor3': 0x32
}

# Exponential Moving Average (EMA) alpha
EMA_ALPHA = 1.0

def initialize_sensor(i2c, xshut_pin, new_address):
    try:
        xshut = digitalio.DigitalInOut(xshut_pin)
        xshut.direction = digitalio.Direction.OUTPUT
        xshut.value = False  # Keep the sensor in reset state

        time.sleep(0.1)
        xshut.value = True  # Bring the sensor out of reset

        # Try to initialize sensor at the default address
        sensor = adafruit_vl53l0x.VL53L0X(i2c)
        
        # Attempt to change the sensor address
        sensor.set_address(new_address)
        print(f"VL53L0X sensor initialized and set to address {hex(new_address)}.")

        return sensor

    except Exception as e:
        print(f"Error initializing VL53L0X sensor: {e}")
        exit()

def check_sensor(i2c, address):
    try:
        sensor = adafruit_vl53l0x.VL53L0X(i2c, address=address)
        # Perform a read to confirm sensor is responsive
        sensor.range
        return True
    except Exception:
        return False

def apply_ema_filter(ema, new_value, alpha=EMA_ALPHA):
    if ema is None:
        return new_value
    return alpha * new_value + (1 - alpha) * ema

def main():
    i2c = busio.I2C(board.SCL, board.SDA)
    
    # Initialize sensors with new addresses
    sensors = {}
    ema_distances = {}
    for key, xshut_pin in XSHUT_PINS.items():
        if not check_sensor(i2c, NEW_ADDRESSES[key]):
            sensors[key] = initialize_sensor(i2c, xshut_pin, NEW_ADDRESSES[key])
        else:
            sensors[key] = adafruit_vl53l0x.VL53L0X(i2c, address=NEW_ADDRESSES[key])
            print(f"VL53L0X sensor already initialized at address {hex(NEW_ADDRESSES[key])}")
        ema_distances[key] = None
        time.sleep(1)  # Small delay to ensure the address change takes effect

    try:
        while True:
            for key, sensor in sensors.items():
                try:
                    distance_mm = sensor.range
                    # Apply offset adjustment
                    distance_mm -= OFFSET
                    # Apply EMA filter
                    ema_distances[key] = apply_ema_filter(ema_distances[key], distance_mm)
                    print(f"Sensor {key} distance: {ema_distances[key]:.2f} mm")
                except RuntimeError as e:
                    print(f"Error reading distance from {key}: {e}")

            time.sleep(0.5)  # Adjust refresh rate as needed

    except KeyboardInterrupt:
        print("\nExiting program.")

if __name__ == "__main__":
    main()
