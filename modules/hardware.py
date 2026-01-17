# modules/hardware.py
import time
import config

# Try to import hardware libraries, handle error if running on PC
try:
    # from adafruit_servokit import ServoKit
    # kit = ServoKit(channels=16)
    HARDWARE_AVAILABLE = False  # Set to True when you install libraries
except ImportError:
    HARDWARE_AVAILABLE = False
    print("[INFO] Hardware libraries not found. Running in Simulation Mode.")


class RobotBody:
    def __init__(self):
        self.is_connected = HARDWARE_AVAILABLE

    def move_head(self, x, y):
        """
        x: -1 (Left) to 1 (Right)
        y: -1 (Down) to 1 (Up)
        """
        if not self.is_connected:
            # print(f"[SIM] Moving Head to X:{x}, Y:{y}")
            return

        # Example Servo Logic (Uncomment when hardware arrives)
        # angle_x = 90 + (x * 45)
        # kit.servo[0].angle = angle_x
        pass

    def wake_up_sequence(self):
        """Physical movements when waking up"""
        if not self.is_connected: return
        # Example: Lift head slowly
        pass

    def sleep_sequence(self):
        """Physical movements when sleeping"""
        if not self.is_connected: return
        # Example: Drop head
        pass

    def give_object_gesture(self):
        """The 'Give Chocolate' movement"""
        print("[BODY] Extending arm to give object...")
        # 1. Raise Shoulder
        # 2. Extend Elbow
        # 3. Open Gripper
        time.sleep(2)
        print("[BODY] Motion complete.")