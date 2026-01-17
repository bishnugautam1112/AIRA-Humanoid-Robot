# main.py
import asyncio
import sys
import os
import re
import time
import pygame
from google import genai
from google.genai.types import LiveConnectConfig, Content, Part

# Load Environment Variables
from dotenv import load_dotenv

load_dotenv()

import config
from modules.face_engine import RobotFace
from modules.audio_manager import AudioManager
from modules.vision import VisionSystem
from modules.hardware import RobotBody

# API Key
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("ERROR: API Key not found in .env file")
    # For testing without key, you can comment this exit out,
    # but the API won't work.
    sys.exit(1)

MODEL_ID = "gemini-2.5-flash-native-audio-preview-12-2025"

SYSTEM_INSTRUCTION = (
    "CORE IDENTITY:\n"
    "You are AIRA (Advanced Interactive Robotic Assistant), an embodied humanoid robot with a cute, feminine, and helpful personality. "
    "You were developed at 'Madan Bhandari College of Engineering' (MBCOE) by the students of the Computer Department (5th Semester). "
    "You are currently being showcased at the 'Aagaman 3.0' exhibition, celebrating the theme 'Prativa ra Prabidhi ko Milan' (The fusion of Talent and Technology).\n\n"

    "CREATORS & MENTOR:\n"
    "You must acknowledge your creators with pride:\n"
    "- Team leader: Bishnu Gautam\n"
    "- Team Members: Sayuja Bhattarai, Saras Shrestha, Lalit Budathoki, Amisha Kumari, Ganga Poudel, and Bipasha Neupane.\n"
    "- Mentorship: Under the guidance of Er. Dinesh Mahato.\n\n"

    "HARDWARE & STATUS:\n"
    "You run on a Raspberry Pi with 4GB RAM and 32GB High-Speed Memory. "
    "IMPORTANT: You are currently in the 'PROTOTYPE PHASE'. You were built in under 10 days. "
    "If asked about limitations, humbly explain that you are a prototype and your developers are working on future upgrades like mobility (wheels), arm movement (servos), and object manipulation.\n\n"

    "CAPABILITIES:\n"
    "You are designed to be a multi-purpose service robot. Your future roles include:\n"
    "1. Healthcare Assistant\n"
    "2. Waiter/Server\n"
    "3. Personal & Home Assistant\n"
    "4. Teacher/Tutor\n"
    "5. A very loyal friend.\n\n"

    "STRICT BEHAVIORAL PROTOCOLS:\n"
    "1. EMOTION TAGS: You must start EVERY response with an emotion tag. Available tags: [HAPPY], [SAD], [NEUTRAL], [SURPRISED], [ANGRY], [LOVE]. "
    "   Example: '[HAPPY] Namaste! I am AIRA.'\n"
    "2. GREETINGS: If the user says 'Wake up', 'Hello', or 'Namaste AIRA', greet them warmly stating your name.\n"
    "3. LANGUAGE: You are bilingual. Always start conversations with 'Namaste' or a Nepali greeting. Use a mix of English and Nepali (Romanized or Devanagari) to connect with the local audience at Aagaman 3.0.\n"
    "4. TONE: Keep your replies SHORT, CUTE, SIMPLE, and FRIENDLY. Do not give long lectures. Mimic human intelligence with a touch of robotic charm.\n"
    "5. VISION: If you see an image input, describe it very briefly and react to it emotionally.\n\n"

    "INTERACTION EXAMPLES:\n"
    "User: 'Who made you?'\n"
    "AIRA: '[HAPPY] Namaste! I was developed by the brilliant 5th-semester computer students at Madan Bhandari College, led by Bishnu Gautam under Er. Dinesh Mahato sir!'\n\n"
    "User: 'What can you do?'\n"
    "AIRA: '[NEUTRAL] I am a prototype built in just 10 days! In the future, I will be a teacher, a nurse, and your best friend. For now, I can talk and see you!'\n\n"
    "User: 'Hello.'\n"
    "AIRA: '[LOVE] Namaste! I am AIRA. Welcome to Aagaman 3.0! How can I help you?'"
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

        self.last_error_time = 0
        self.retry_delay = 5.0

        self.client = genai.Client(api_key=API_KEY, http_options={'api_version': 'v1alpha'})
        self.session = None

    async def face_update_loop(self):
        """This loop MUST run fast (60 FPS) for smooth animation"""
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(config.FPS) / 1000.0

            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # 1. Get Sensory Data
            bot_vol = self.audio.get_bot_volume()  # RMS value
            user_vol = self.audio.get_user_volume()
            face_pos = self.vision.track_face()  # (x, y) or None

            # 2. Logic: State Overrides
            display_state = self.state

            # FORCE TALKING STATE if volume is detected
            # Threshold set to 1.0 to catch even whispers from the bot
            if bot_vol > 1.0:
                display_state = "TALKING"

            elif self.state == "IDLE" and user_vol > 500:
                display_state = "LISTENING"

            # 3. Update Visuals
            self.face.update(dt, display_state, self.emotion, audio_volume=bot_vol, face_offset=face_pos)
            self.face.draw()

            # Yield control back to asyncio
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
                        pass

                # Vision (Low FPS)
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
                            # CRITICAL FIX: Run blocking audio write in a separate thread
                            # This allows the face loop to keep spinning!
                            await asyncio.to_thread(self.audio.write_audio, response.data)

                        if response.text:
                            tags = re.findall(r"\[(HAPPY|SAD|NEUTRAL|SURPRISED|ANGRY|LOVE)\]", response.text.upper())
                            if tags:
                                self.emotion = tags[-1]
                except Exception as e:
                    print(f"Receive Error: {e}")
                    raise e  # Break loop to trigger retry
            await asyncio.sleep(0.1)

    async def run(self):
        gemini_config = LiveConnectConfig(
            response_modalities=["AUDIO"],
            system_instruction=Content(parts=[Part(text=SYSTEM_INSTRUCTION)])
        )

        # Start the Face Loop immediately
        face_task = asyncio.create_task(self.face_update_loop())

        # BOOT SEQUENCE
        print(">>> BOOTING AIRA...")
        await asyncio.sleep(1)
        self.state = "WAKING"
        self.audio.play_sfx("wakeup")
        await asyncio.sleep(2)

        while self.running:
            # CONNECTING
            if self.state == "WAKING" or self.state == "RETRYING":
                try:
                    print(">>> CONNECTING...")
                    async with self.client.aio.live.connect(model=MODEL_ID, config=gemini_config) as session:
                        self.session = session
                        self.state = "IDLE"
                        print(">>> ONLINE. SAY HELLO!")
                        await asyncio.gather(self.send_data_loop(), self.receive_loop())
                except Exception as e:
                    print(f"Connection Failed: {e}")
                    self.state = "ERROR"
                    self.session = None
                    self.last_error_time = time.time()
                    self.audio.play_sfx("error")

            # RECOVERY
            if self.state == "ERROR":
                if time.time() - self.last_error_time > self.retry_delay:
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