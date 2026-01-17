# config.py
import os

# --- SYSTEM SETTINGS ---
FULLSCREEN = False  # Set to True for running on the Robot Screen
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
FPS = 60

# --- PATHS ---
ASSETS_DIR = "assets"
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")

# --- COLORS (R, G, B) ---
COLOR_BG = (10, 12, 18)           # Deep Sci-Fi Blue/Black
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)

# Eye Colors by State
COLOR_EYE_IDLE = (0, 255, 255)    # Cyan
COLOR_EYE_LISTEN = (0, 255, 100)  # Bright Green
COLOR_EYE_TALK = (0, 200, 255)    # Blue
COLOR_EYE_SLEEP = (20, 30, 50)    # Dim Blue/Grey
COLOR_EYE_ERROR = (255, 50, 50)   # Red
COLOR_EYE_LOVE = (255, 105, 180)  # Hot Pink
COLOR_EYE_HAPPY = (255, 223, 0)   # Golden Yellow

# --- FACE GEOMETRY ---
EYE_WIDTH = 140
EYE_HEIGHT = 180
EYE_SPACING = 240       # Distance between eye centers
PUPIL_SIZE = 45
MOUTH_WIDTH = 200
MOUTH_THICKNESS = 8

# --- ANIMATION SPEEDS ---
BLINK_INTERVAL_MIN = 2.0
BLINK_INTERVAL_MAX = 6.0
LERP_SPEED = 10.0       # How fast eyes move (Higher = Snappier)
BREATH_SPEED = 2.0      # Speed of pupil pulsing