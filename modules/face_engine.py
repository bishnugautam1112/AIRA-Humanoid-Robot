# modules/face_engine.py
import pygame
import random
import math
import time
import config


class RobotFace:
    def __init__(self):
        pygame.init()
        flags = pygame.FULLSCREEN if config.FULLSCREEN else pygame.RESIZABLE
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), flags)
        pygame.display.set_caption("AIRA Visual System")

        # State
        self.current_state = "SLEEPING"

        # Animation Vars
        self.eyelid_pos = 1.0
        self.current_color = list(config.COLOR_EYE_SLEEP)

        self.pupil_x = 0
        self.pupil_y = 0

        self.mouth_height = config.MOUTH_THICKNESS
        self.talk_timer = 0
        self.breathing_phase = 0

        # Blink Timers
        self.next_blink = time.time() + 2
        self.is_blinking = False

    def lerp(self, start, end, speed, dt):
        return start + (end - start) * speed * dt

    def update(self, dt, state, emotion, face_offset=None):
        """
        face_offset: Tuple (x, y) from Vision module, or None
        """
        self.current_state = state

        # --- 1. MOUTH ANIMATION (FIXED) ---
        target_mouth = config.MOUTH_THICKNESS

        if state == "TALKING":
            # Sine Wave Logic (Smooth, Robotic Speech)
            self.talk_timer += dt * 15  # Speed of talking

            # Calculate wave: Goes from 0 to 1
            wave = (math.sin(self.talk_timer) + 1) / 2

            # Map to Height: Minimum 10px, Maximum 50px (Not too wide!)
            target_mouth = 10 + (wave * 40)

            # Occasional "pause" to look natural
            if random.random() < 0.1:
                target_mouth = 10

        elif emotion == "HAPPY":
            target_mouth = 20

        self.mouth_height = self.lerp(self.mouth_height, target_mouth, 20, dt)

        # --- 2. PUPIL ANIMATION (FIXED GAZE) ---
        target_pupil_x = 0
        target_pupil_y = 0

        if state == "SLEEPING":
            target_pupil_y = 30  # Look down
        else:
            # If we see a face, LOCK ON to it
            if face_offset is not None:
                # face_offset is -1.0 to 1.0
                # Multiply by 60 to move pupil 60 pixels max
                target_pupil_x = face_offset[0] * 60
                target_pupil_y = face_offset[1] * 40
            else:
                # No face detected
                if state == "IDLE":
                    # Look straight, occasional random glance
                    if random.random() < 0.01:
                        # Very small movement
                        target_pupil_x = random.uniform(-20, 20)
                        target_pupil_y = random.uniform(-10, 10)
                elif state == "LISTENING" or state == "TALKING":
                    # Look mostly forward/attentive if no specific face found
                    target_pupil_x = 0
                    target_pupil_y = 0

        # Smooth Movement
        self.pupil_x = self.lerp(self.pupil_x, target_pupil_x, 8, dt)
        self.pupil_y = self.lerp(self.pupil_y, target_pupil_y, 8, dt)

        # --- 3. COLORS & BLINKING (Standard) ---
        # (Same logic as before to keep consistency)
        target_c = config.COLOR_EYE_IDLE
        target_lid = 0.0

        if state == "SLEEPING":
            target_c = config.COLOR_EYE_SLEEP
            target_lid = 1.0
        elif state == "LISTENING":
            target_c = config.COLOR_EYE_LISTEN
        elif state == "ERROR":
            target_c = config.COLOR_EYE_ERROR

        # Blinking
        if state != "SLEEPING":
            if time.time() > self.next_blink:
                self.is_blinking = True
                self.next_blink = time.time() + random.uniform(3, 6)
                self.blink_timer = 0.15
            if self.is_blinking:
                self.blink_timer -= dt
                if self.blink_timer > 0:
                    target_lid = 1.0
                else:
                    self.is_blinking = False

        self.eyelid_pos = self.lerp(self.eyelid_pos, target_lid, 15, dt)

        for i in range(3):
            self.current_color[i] += (target_c[i] - self.current_color[i]) * 5 * dt

        self.breathing_phase += dt * 2

    def draw(self):
        self.screen.fill(config.COLOR_BG)
        cx, cy = config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2

        # Draw Eyes
        for i in [-1, 1]:
            eye_x = cx + (i * config.EYE_SPACING // 2)
            eye_y = cy - 40

            # Sclera
            color = tuple(map(int, self.current_color))
            pygame.draw.ellipse(self.screen, color,
                                (eye_x - config.EYE_WIDTH // 2, eye_y - config.EYE_HEIGHT // 2, config.EYE_WIDTH,
                                 config.EYE_HEIGHT))

            # Pupil
            px = eye_x + self.pupil_x
            py = eye_y + self.pupil_y
            px = max(eye_x - 30, min(eye_x + 30, px))
            py = max(eye_y - 30, min(eye_y + 30, py))

            s = int(config.PUPIL_SIZE + math.sin(self.breathing_phase) * 2)
            pygame.draw.circle(self.screen, config.COLOR_BLACK, (int(px), int(py)), s)

            # Lids
            lid_h = (config.EYE_HEIGHT / 2) * self.eyelid_pos
            pygame.draw.rect(self.screen, config.COLOR_BG,
                             (eye_x - config.EYE_WIDTH // 2 - 5, eye_y - config.EYE_HEIGHT // 2, config.EYE_WIDTH + 10,
                              lid_h))
            pygame.draw.rect(self.screen, config.COLOR_BG,
                             (eye_x - config.EYE_WIDTH // 2 - 5, eye_y + config.EYE_HEIGHT // 2 - lid_h,
                              config.EYE_WIDTH + 10, lid_h))

        # Draw Mouth
        # Centered mouth
        mouth_rect = pygame.Rect(cx - config.MOUTH_WIDTH // 2, cy + 100 - self.mouth_height // 2, config.MOUTH_WIDTH,
                                 self.mouth_height)
        pygame.draw.rect(self.screen, tuple(map(int, self.current_color)), mouth_rect, border_radius=10)

        pygame.display.flip()