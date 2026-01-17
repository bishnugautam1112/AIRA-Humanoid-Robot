# modules/vision.py
import cv2
import time
import numpy as np


class VisionSystem:
    def __init__(self):
        # Initialize Camera
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Load Standard Face Detector (Haar Cascade)
        # This is built-in to OpenCV, no extra downloads usually needed
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        # State
        self.last_frame_time = 0
        self.frame_interval = 0.1  # Check for face 10 times a second (Fast enough for eyes)
        self.current_face_offset = (0, 0)  # (x, y) from -1.0 to 1.0

    def get_frame_bytes(self):
        """For sending to Gemini API (Slow, 1fps)"""
        # (Existing code for Gemini image sending...)
        ret, frame = self.cap.read()
        if not ret: return None
        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
        return buffer.tobytes()

    def track_face(self):
        """
        Returns (x, y) offset of the person's face.
        x: -1.0 (Left) to 1.0 (Right)
        y: -1.0 (Up) to 1.0 (Down)
        Returns None if no face found.
        """
        if time.time() - self.last_frame_time < self.frame_interval:
            return self.current_face_offset

        self.last_frame_time = time.time()
        ret, frame = self.cap.read()
        if not ret: return (0, 0)

        # Convert to grayscale for detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)

        if len(faces) > 0:
            # Find the biggest face (closest person)
            # Face format: (x, y, w, h)
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            (x, y, w, h) = largest_face

            # Calculate Center
            face_cx = x + w // 2
            face_cy = y + h // 2

            # Normalize to -1.0 to 1.0 relative to screen center
            # 320 is half of 640 width, 240 is half of 480 height
            norm_x = (face_cx - 320) / 320.0
            norm_y = (face_cy - 240) / 240.0

            # Invert X because camera is mirrored? Usually needed.
            self.current_face_offset = (-norm_x, norm_y)
        else:
            # If no face, return None to indicate "Lost target"
            self.current_face_offset = None

        return self.current_face_offset

    def release(self):
        self.cap.release()