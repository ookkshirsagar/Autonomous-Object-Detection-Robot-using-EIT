import time
import board
import busio
import adafruit_vl53l0x
import digitalio

# Define the XSHUT pins for each sensor
XSHUT_PINS = {
    'sensor_front': board.D5,
    'sensor_left': board.D6,
    'sensor_right': board.D7
}

# New addresses for each sensor
NEW_ADDRESSES = {
    'sensor_front': 0x30,
    'sensor_left': 0x31,
    'sensor_right': 0x32
}

# Initialize I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Dictionary to hold sensor objects
sensors = {}

# Function to initialize VL53L0X sensor
def initialize_sensor(i2c, xshut_pin, new_address):
    try:
        xshut = digitalio.DigitalInOut(xshut_pin)
        xshut.direction = digitalio.Direction.OUTPUT
        xshut.value = False  # Keep the sensor in reset state

        time.sleep(0.1)
        xshut.value = True  # Bring the sensor out of reset

        # Initialize sensor at the default address
        sensor = adafruit_vl53l0x.VL53L0X(i2c)
        
        # Attempt to change the sensor address
        sensor.set_address(new_address)
        print(f"VL53L0X sensor initialized and set to address {hex(new_address)}.")

        return sensor

    except Exception as e:
        print(f"Error initializing VL53L0X sensor: {e}")
        return None

# Function to check if sensor is already initialized at new address
def check_sensor(i2c, address):
    try:
        sensor = adafruit_vl53l0x.VL53L0X(i2c, address=address)
        # Perform a read to confirm sensor is responsive
        sensor.range
        return True
    except Exception:
        return False

# Initialize sensors with new addresses
for key, xshut_pin in XSHUT_PINS.items():
    if key in NEW_ADDRESSES:
        try:
            if not check_sensor(i2c, NEW_ADDRESSES[key]):
                sensors[key] = initialize_sensor(i2c, xshut_pin, NEW_ADDRESSES[key])
                if sensors[key]:
                    print(f"Sensor {key} initialized at address {hex(NEW_ADDRESSES[key])}")
                else:
                    print(f"Failed to initialize sensor {key} at address {hex(NEW_ADDRESSES[key])}")
            else:
                sensors[key] = adafruit_vl53l0x.VL53L0X(i2c, address=NEW_ADDRESSES[key])
                print(f"VL53L0X sensor already initialized at address {hex(NEW_ADDRESSES[key])}")
        except Exception as e:
            print(f"Failed to initialize sensor {key}: {e}")
    else:
        print(f"No address defined for sensor {key}")

# Example usage: read range from sensors
try:
    while True:
        for key, sensor in sensors.items():
            try:
                range_mm = sensor.range
                print(f"Sensor {key} range: {range_mm} mm")
            except Exception as e:
                print(f"Error reading sensor {key}: {e}")
        
        time.sleep(1)  # Adjust as needed for desired sampling interval

except KeyboardInterrupt:
    print("\nExiting program.")

finally:
    for key, sensor in sensors.items():
        sensor.close()  # Close sensor objects
