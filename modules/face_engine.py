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

        # --- STATE VARIABLES ---
        self.current_state = "SLEEPING"
        self.current_emotion = "NEUTRAL"

        # --- ANIMATION PHYSICS ---
        self.eyelid_pos = 1.0
        self.current_color = list(config.COLOR_EYE_SLEEP)

        # Pupils
        self.pupil_x = 0
        self.pupil_y = 0
        self.breathing_phase = 0

        # Mouth
        self.mouth_height = config.MOUTH_THICKNESS
        self.talk_timer = 0

        # Blinking
        self.next_blink = time.time() + 2
        self.is_blinking = False
        self.blink_timer = 0

    def lerp(self, start, end, speed, dt):
        """Standard Linear Interpolation"""
        return start + (end - start) * speed * dt

    def update(self, dt, state, emotion, audio_volume=0.0, face_offset=None):
        self.current_state = state
        self.current_emotion = emotion

        # ==========================
        # 1. MOUTH LOGIC (Instant Stop + Sine Wave)
        # ==========================
        target_mouth = config.MOUTH_THICKNESS

        if state == "TALKING":
            # Sine Wave Logic
            self.talk_timer += dt * 18
            wave = (math.sin(self.talk_timer) + 1) / 2

            # Map: Min 12px, Max 55px
            target_mouth = 12 + (wave * 43)

            # Natural Jitter
            if random.random() < 0.05:
                target_mouth = 12
        else:
            # INSTANT STOP
            self.talk_timer = 0
            # Resting Smile
            if emotion == "HAPPY": target_mouth = 18

        self.mouth_height = self.lerp(self.mouth_height, target_mouth, 25, dt)

        # ==========================
        # 2. EYE TRACKING LOGIC
        # ==========================
        target_px = 0
        target_py = 0

        if state == "SLEEPING":
            target_py = 30
        else:
            if face_offset:
                # Track Face
                target_px = face_offset[0] * 60
                target_py = face_offset[1] * 40
            elif state == "IDLE" and random.random() < 0.01:
                # Random wander
                target_px = random.uniform(-15, 15)
                target_py = random.uniform(-5, 5)

        self.pupil_x = self.lerp(self.pupil_x, target_px, 10, dt)
        self.pupil_y = self.lerp(self.pupil_y, target_py, 10, dt)

        # ==========================
        # 3. BLINK & COLORS
        # ==========================
        target_lid = 0.0
        target_c = config.COLOR_EYE_IDLE

        if state == "SLEEPING":
            target_lid = 1.0
            target_c = config.COLOR_EYE_SLEEP
        elif state == "ERROR":
            target_lid = 0.0
            target_c = config.COLOR_EYE_ERROR
        elif state == "LISTENING":
            target_c = config.COLOR_EYE_LISTEN
        elif emotion == "HAPPY":
            target_c = config.COLOR_EYE_HAPPY
        elif emotion == "LOVE":
            target_c = config.COLOR_EYE_LOVE

        # Blinking
        if state not in ["SLEEPING", "ERROR"]:
            if time.time() > self.next_blink:
                self.is_blinking = True
                self.next_blink = time.time() + random.uniform(3, 7)
                self.blink_timer = 0.15

            if self.is_blinking:
                self.blink_timer -= dt
                if self.blink_timer > 0:
                    target_lid = 1.0
                else:
                    self.is_blinking = False

        self.eyelid_pos = self.lerp(self.eyelid_pos, target_lid, 20, dt)

        for i in range(3):
            self.current_color[i] += (target_c[i] - self.current_color[i]) * 10 * dt

        self.breathing_phase += dt * 2

    def draw_lashes(self, cx, cy, side, lid_y_offset):
        """
        Draws 3 cute lashes on the top outer corner.
        They move down as the eyelid closes (lid_y_offset).
        """
        # Calculate anchor point (Top edge of the eye + current lid position)
        eye_top_y = cy - (config.EYE_HEIGHT // 2)
        anchor_y = eye_top_y + lid_y_offset

        # Anchor X is the outer edge of the eye
        # Left Eye (side -1): Outer edge is Left side
        # Right Eye (side 1): Outer edge is Right side
        eye_center_x = cx + (side * config.EYE_SPACING // 2)

        # Color same as eye
        color = tuple(map(int, self.current_color))

        # Draw 3 lashes
        for i in range(3):
            # Spacing between lashes
            offset_x = (i * 15) * side  # Spreads out left or right

            # Start Point (On the eyelid edge)
            # We shift them slightly towards the outside
            start_x = eye_center_x + (side * (config.EYE_WIDTH // 4)) + (side * (i * 8))
            start_y = anchor_y + (i * 2)  # Slight curve down

            # End Point (Sticking out)
            # Length = 25px
            # Angle: Up and Out
            end_x = start_x + (side * 25) + (side * i * 5)  # Fan out
            end_y = start_y - 25 + (i * 5)

            # Draw Line (Thickness 4 for visibility)
            pygame.draw.line(self.screen, color, (start_x, start_y), (end_x, end_y), 4)

    def draw(self):
        self.screen.fill(config.COLOR_BG)
        cx, cy = config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2

        # 1. DRAW EYES
        for side in [-1, 1]:
            eye_x = cx + (side * config.EYE_SPACING // 2)
            eye_y = cy - 20

            # Sclera
            color = tuple(map(int, self.current_color))
            pygame.draw.ellipse(self.screen, color,
                                (eye_x - config.EYE_WIDTH // 2, eye_y - config.EYE_HEIGHT // 2, config.EYE_WIDTH,
                                 config.EYE_HEIGHT))

            # Pupil
            px = max(eye_x - 35, min(eye_x + 35, eye_x + self.pupil_x))
            py = max(eye_y - 35, min(eye_y + 35, eye_y + self.pupil_y))

            s = int(config.PUPIL_SIZE + math.sin(self.breathing_phase) * 2)
            pygame.draw.circle(self.screen, config.COLOR_BLACK, (int(px), int(py)), s)

            # Calculate Lid Heights
            lid_h = (config.EYE_HEIGHT / 2) * self.eyelid_pos

            # DRAW LASHES (Before drawing the lid rectangle, but using lid position)
            # We want them to appear attached to the top lid
            self.draw_lashes(cx, cy - 20, side, lid_h)

            # Draw Eyelid Rectangles (Covers the eye to blink)
            pygame.draw.rect(self.screen, config.COLOR_BG,
                             (eye_x - config.EYE_WIDTH // 2 - 10, eye_y - config.EYE_HEIGHT // 2, config.EYE_WIDTH + 20,
                              lid_h))
            pygame.draw.rect(self.screen, config.COLOR_BG,
                             (eye_x - config.EYE_WIDTH // 2 - 10, eye_y + config.EYE_HEIGHT // 2 - lid_h,
                              config.EYE_WIDTH + 20, lid_h))

        # 2. DRAW MOUTH
        rect_w = config.MOUTH_WIDTH
        rect_h = self.mouth_height

        mouth_rect = pygame.Rect(cx - rect_w // 2, cy + 120 - rect_h // 2, rect_w, rect_h)
        pygame.draw.rect(self.screen, tuple(map(int, self.current_color)), mouth_rect, border_radius=10)

        pygame.display.flip()