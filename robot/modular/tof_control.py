import time
import board
import busio
import adafruit_vl53l0x
import digitalio

class TOFControl:
    def __init__(self):
        # Define the XSHUT pins for each sensor
        self.XSHUT_PINS = {
            'sensor_front': board.D5,
            'sensor_left': board.D6,
            'sensor_right': board.D7
        }

        # New addresses for each sensor
        self.NEW_ADDRESSES = {
            'sensor_front': 0x30,
            'sensor_left': 0x31,
            'sensor_right': 0x32
        }

        # Initialize I2C bus
        self.i2c = busio.I2C(board.SCL, board.SDA)

        # Dictionary to hold sensor objects
        self.sensors = {}

        # Initialize sensors with new addresses
        self.initialize_sensors()

    def initialize_sensor(self, xshut_pin, new_address):
        try:
            xshut = digitalio.DigitalInOut(xshut_pin)
            xshut.direction = digitalio.Direction.OUTPUT
            xshut.value = False  # Keep the sensor in reset state

            time.sleep(0.1)
            xshut.value = True  # Bring the sensor out of reset

            # Initialize sensor at the default address
            sensor = adafruit_vl53l0x.VL53L0X(self.i2c)
            
            # Attempt to change the sensor address
            sensor.set_address(new_address)
            print(f"VL53L0X sensor initialized and set to address {hex(new_address)}.")

            return sensor

        except Exception as e:
            print(f"Error initializing VL53L0X sensor: {e}")
            return None

    def check_sensor(self, address):
        try:
            sensor = adafruit_vl53l0x.VL53L0X(self.i2c, address=address)
            # Perform a read to confirm sensor is responsive
            sensor.range
            return True
        except Exception:
            return False

    def initialize_sensors(self):
        for key, xshut_pin in self.XSHUT_PINS.items():
            if key in self.NEW_ADDRESSES:
                try:
                    if not self.check_sensor(self.NEW_ADDRESSES[key]):
                        self.sensors[key] = self.initialize_sensor(xshut_pin, self.NEW_ADDRESSES[key])
                        if self.sensors[key]:
                            print(f"Sensor {key} initialized at address {hex(self.NEW_ADDRESSES[key])}")
                        else:
                            print(f"Failed to initialize sensor {key} at address {hex(self.NEW_ADDRESSES[key])}")
                    else:
                        self.sensors[key] = adafruit_vl53l0x.VL53L0X(self.i2c, address=self.NEW_ADDRESSES[key])
                        print(f"VL53L0X sensor already initialized at address {hex(self.NEW_ADDRESSES[key])}")
                except Exception as e:
                    print(f"Failed to initialize sensor {key}: {e}")
            else:
                print(f"No address defined for sensor {key}")

    def read_sensor_data(self):
        try:
            while True:
                for key, sensor in self.sensors.items():
                    try:
                        range_mm = sensor.range
                        print(f"Sensor {key} range: {range_mm} mm")
                    except Exception as e:
                        print(f"Error reading sensor {key}: {e}")
            
                time.sleep(1)  # Adjust as needed for desired sampling interval

        except KeyboardInterrupt:
            print("\nExiting program.")

        finally:
            self.cleanup()

    def cleanup(self):
        for key, sensor in self.sensors.items():
            sensor.close()  # Close sensor objects
