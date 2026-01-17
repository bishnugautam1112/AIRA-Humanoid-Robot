# main.py
import asyncio
import sys
import os
import re
import time
import pygame
from google import genai
from google.genai.types import LiveConnectConfig, Content, Part
from dotenv import load_dotenv # You might need: pip install python-dotenv

import config
from modules.face_engine import RobotFace
from modules.audio_manager import AudioManager
from modules.vision import VisionSystem
from modules.hardware import RobotBody
load_dotenv() # Loads the .env file
# Get key from secure file
API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_ID = "gemini-2.5-flash-native-audio-preview-12-2025"

SYSTEM_INSTRUCTION = (
    "You are AIRA. "
    "Always start response with [HAPPY], [SAD], [NEUTRAL], [SURPRISED]. "
    "Keep answers short and chatty."
)


class AIRARobot:
    def __init__(self):
        self.face = RobotFace()
        self.audio = AudioManager()
        self.vision = VisionSystem()
        self.body = RobotBody()

        self.state = "SLEEPING"
        self.emotion = "NEUTRAL"
        self.running = True

        # Error Handling Vars
        self.last_error_time = 0
        self.retry_delay = 5.0  # Seconds to wait before retrying

        # Client
        self.client = genai.Client(api_key=API_KEY, http_options={'api_version': 'v1alpha'})
        self.session = None

    async def face_update_loop(self):
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(config.FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # 1. Get Audio Volume (For state triggering)
            bot_vol = self.audio.get_bot_volume()
            user_vol = self.audio.get_user_volume()

            # 2. Get Face Position (For Eye Contact)
            # This is fast now because we handle timing inside vision.py
            face_pos = self.vision.track_face()

            # 3. Determine State
            display_state = self.state

            if self.state == "IDLE" and user_vol > 500:
                display_state = "LISTENING"

            if bot_vol > 0.05:
                display_state = "TALKING"

            # 4. Update Face
            # We pass the face_pos so the eyes can lock on
            self.face.update(dt, display_state, self.emotion, face_offset=face_pos)
            self.face.draw()

            await asyncio.sleep(0.001)

    async def send_data_loop(self):
        while self.running:
            if self.state in ["IDLE", "LISTENING", "TALKING"]:
                # Audio
                data = self.audio.read_mic()
                if data and self.session:
                    try:
                        await self.session.send_realtime_input(
                            media={"data": data, "mime_type": "audio/pcm;rate=16000"})
                    except:
                        pass  # Errors handled in main loop

                # Video (Low FPS)
                img = self.vision.get_frame_bytes()
                if img and self.session:
                    try:
                        await self.session.send_realtime_input(media={"data": img, "mime_type": "image/jpeg"})
                    except:
                        pass
            await asyncio.sleep(0.01)

    async def receive_loop(self):
        while self.running:
            if self.session:
                try:
                    async for response in self.session.receive():
                        if response.data:
                            self.audio.write_audio(response.data)
                        if response.text:
                            tags = re.findall(r"\[(HAPPY|SAD|NEUTRAL|SURPRISED|ANGRY|LOVE)\]", response.text.upper())
                            if tags:
                                self.emotion = tags[-1]
                except Exception as e:
                    print(f"Receive Error: {e}")
                    # Throw error to break the loop and trigger retry in main()
                    raise e
            await asyncio.sleep(0.1)

    async def run(self):
        gemini_config = LiveConnectConfig(
            response_modalities=["AUDIO"],
            system_instruction=Content(parts=[Part(text=SYSTEM_INSTRUCTION)])
        )

        # Start Face Task
        face_task = asyncio.create_task(self.face_update_loop())

        # --- AUTO WAKEUP LOGIC ---
        print(">>> SYSTEM BOOT. SLEEPING FOR 3 SECONDS...")
        await asyncio.sleep(3)  # Simulate boot time
        self.state = "WAKING"
        self.audio.play_sfx("wakeup")
        await asyncio.sleep(2)  # Allow sound to play

        while self.running:

            # --- CONNECTION STATE ---
            if self.state == "WAKING" or self.state == "RETRYING":
                try:
                    print(">>> ATTEMPTING CONNECTION...")
                    async with self.client.aio.live.connect(model=MODEL_ID, config=gemini_config) as session:
                        self.session = session
                        self.state = "IDLE"
                        print(">>> CONNECTED!")

                        # Run the comms loops
                        # If these crash (due to internet), we catch the error below
                        await asyncio.gather(
                            self.send_data_loop(),
                            self.receive_loop()
                        )
                except Exception as e:
                    print(f"Connection Lost/Failed: {e}")
                    self.state = "ERROR"
                    self.session = None
                    self.last_error_time = time.time()
                    self.audio.play_sfx("error")  # Play ONCE

            # --- ERROR HANDLING STATE ---
            if self.state == "ERROR":
                # Wait for the delay
                if time.time() - self.last_error_time > self.retry_delay:
                    print(">>> RETRYING NOW...")
                    self.state = "RETRYING"

            await asyncio.sleep(0.1)

        await face_task
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    bot = AIRARobot()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        pass