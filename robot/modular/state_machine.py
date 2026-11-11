import time
import signal
import sys
import RPi.GPIO as GPIO
from robot_movement import RobotMovement
from servo_control import ServoControl
from eit_voltage_check import EITVoltageCheck
from tof_control import TOFControl

class MainControl:
    def __init__(self):
        print("Initializing MainControl...")
        self.robot = RobotMovement()
        self.servo = ServoControl()
        self.eit = EITVoltageCheck()
        self.tof = TOFControl()

    def initialize_components(self):
        print("Initializing components...")
        # Initialize all components and wait for stabilization
        self.servo.move_to_initial_positions()
        print("Components initialized.")

    def move_servos_upward(self):
        print("Moving servos upward...")
        # Move servo motors to initial angles
        self.servo.move_servos_upward()
        time.sleep(1)  # Allow time for servo motors to move
        print("Servos moved upward.")

    def move_forward_and_stop(self):
        print("Moving forward for 1 second...")
        # Move forward for 1 second and then stop for 20 seconds
        self.robot.move_forward()
        time.sleep(1)
        self.robot.stop_motors()
        print("Stopping for 20 seconds...")
        time.sleep(20)
        print("Stop completed.")

    def perform_voltage_check(self):
        print("Performing voltage check...")
        # Perform an EIT voltage check
        self.eit.run()
        print("Voltage check completed.")

    def move_servos_downward(self):
        print("Moving servos downward...")
        # Immediately move servo motors downward
        self.servo.move_servos_downward()
        time.sleep(15)  # Wait for 15 seconds
        print("Servos moved downward.")

    def handle_distance_detection(self):
        print("Handling distance detection...")
        # Handle distance detection using ToF sensors
        while True:
            front_distance = self.tof.get_distance('sensor_front')
            side_distance_left = self.tof.get_distance('sensor_left')
            side_distance_right = self.tof.get_distance('sensor_right')
            print(f"Front Distance: {front_distance}, Left Distance: {side_distance_left}, Right Distance: {side_distance_right}")

            if front_distance <= 100 and side_distance_left <= 50 and side_distance_right <= 50:
                # Detected conditions met, stop motors
                print("Detected close distances. Stopping motors...")
                self.robot.stop_motors()
                break

            # Interrupt mechanism
            if front_distance <= 100:
                print("Close distance detected by front ToF sensor. Handling left turn...")
                # On detection of close distance by front ToF sensor
                self.handle_left_turn()

    def handle_left_turn(self):
        print("Taking a left turn...")
        # Take a left turn and continue forward
        self.robot.turn_left()
        time.sleep(0.2)
        self.robot.stop_motors()
        self.robot.turn_left()
        self.robot.move_forward()
        print("Left turn completed.")

    def run(self):
        try:
            print("Starting MainControl run...")


            while True:
                self.initialize_components()
                self.servo.move_servos_upward()
                self.move_forward_and_stop()
                self.move_servos_downward()
                self.perform_voltage_check()
                self.servo.move_servos_upward()

                self.handle_distance_detection()

                # Ensure cleanup on exit
                signal.signal(signal.SIGINT, self.signal_handler)
                signal.pause()

        except KeyboardInterrupt:
            print("\nProgram interrupted. Cleaning up...")
            self.cleanup()

    def signal_handler(self, signal, frame):
        print("Signal received. Cleaning up...")
        self.cleanup()
        sys.exit(0)

    def cleanup(self):
        print("Cleaning up resources...")
        self.robot.cleanup()
        self.servo.cleanup()
        self.eit.cleanup()
        GPIO.cleanup()
        sys.exit(0)

if __name__ == "__main__":
    main_control = MainControl()
    main_control.run()
