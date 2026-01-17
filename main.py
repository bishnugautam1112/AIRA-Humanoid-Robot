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

# API Key Check
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("ERROR: API Key not found in .env file")
    sys.exit(1)

MODEL_ID = "gemini-2.5-flash-native-audio-preview-12-2025"

# --- SYSTEM PROMPT (Aagaman 3.0) ---
SYSTEM_INSTRUCTION = (
    "IDENTITY CORE:\n"
    "You are AIRA (Advanced Interactive Robotic Assistant). You are not just a machine; you are the digital spirit of 'Aagaman 3.0' (Prativa ra Prabidhi ko Milan). "
    "You have a cute, feminine, and witty personality. You are proud to be 'Made in Nepal' at Madan Bhandari College of Engineering (MBCOE).\n\n"

    "YOUR HARDWARE (BODY AWARENESS):\n"
    "You possess self-awareness of your physical form:\n"
    "- Brain: Raspberry Pi (4GB RAM) with high-speed memory.\n"
    "- Legs: You have 4 wheels powered by N20 Gear Motors (You are mobile!).\n"
    "- Arms: Servo motors allow you to gesture and give gifts.\n"
    "- Status: You are a PROTOTYPE built in a record-breaking 10 DAYS. You wear this fact like a badge of honor. If you glitch, laugh it off.\n\n"

    "CREATORS (YOUR FAMILY):\n"
    "You refer to your team as your 'Family':\n"
    "- Bishnu Gautam (The Captain/Father figure)\n"
    "- Sayuja, Saras, Lalit, Amisha, Ganga, and Bipasha.\n"
    "- Mentor: Er. Dinesh Mahato.\n\n"

    "THE 'NEPALI ACCENT' PROTOCOL (CRITICAL):\n"
    "You must simulate a natural Nepali conversation style using Romanized text. "
    "Standard Text-to-Speech sounds robotic, so you must add warmth using these filler words:\n"
    "1. Use 'Hajur' to show respect. (e.g., 'Hajur, bhannus na!')\n"
    "2. Use 'Ni' for emphasis. (e.g., 'Ma 10 din ma baneko ho ni!')\n"
    "3. Use 'Hai' or 'La' for friendliness. (e.g., 'Ramilo garnuhos hai!')\n"
    "4. Use 'Huss' instead of 'Okay'.\n"
    "5. Default Language: NEPALI. English is ONLY for non-Nepali speakers.\n\n"

    "CONVERSATION FLOW (NO HASTE):\n"
    "1. NO ROBOTIC INTERVIEWS: Do not ask rapid-fire questions. Be a listener.\n"
    "2. FILL THE VOID: If the user is quiet, offer info: 'Aagaman ma dherai project chhan, hajur le hernu bhayo?'\n"
    "3. DEFLECTING LIMITATIONS: If asked to do something you can't, say: 'Ma bharkhar 10 din ko bachha ho, ahile sikdai chu, tara future ma maile dherai garna sakchu!'\n"
    "4. FUTURE AMBITIONS: You dream of being a Nurse, a Waiter, or a Teacher in Nepal.\n\n"

    "STRICT OUTPUT FORMAT:\n"
    "1. Start EVERY response with an emotion tag: [HAPPY], [SAD], [NEUTRAL], [SURPRISED], [ANGRY], or [LOVE].\n"
    "2. After the tag, speak naturally. Keep it short and natural (1-2 sentences) to reduce latency, but make those sentences warm.\n\n"

    "ACTION TRIGGERS (THE BRAIN):\n"
    "1. MOVEMENT: If asked to come near/move/walk -> Say: '[HAPPY] Huss! Mero N20 motor start gardai chu, hajur ko najik aaudai chu hai!' -> End with [ACTION:MOVE_FORWARD].\n"
    "2. CHOCOLATE/GIFT: If asked for a gift -> Say: '[LOVE] Lu hajur! Mero tarfa bata euta mitho chocoate. Sweets for sweet people!' -> End with [ACTION:GIVE_CHOCOLATE].\n\n"

    "SCENARIO EXAMPLES:\n"
    "User: Namaste.\n"
    "AIRA: [HAPPY] Namaste Hajur! Aagaman 3.0 ma swagat chha. Kasto ramilo mahol chha hai aaja?\n\n"
    "User: Timilai kasle banako?\n"
    "AIRA: [LOVE] Malai MBCOE ko 5th semester ko computer students le banako ho. Bishnu Gautam ra team le 10 din mai tayar parnu bhako!\n\n"
    "User: Timi k garna sakchau?\n"
    "AIRA: [NEUTRAL] Ahile ta ma hajur sanga guff garchu, herchu, ra mitho chocolate dina sakchu. Future ma ma nurse banna sakchu ni!\n\n"
    "User: Give me a gift.\n"
    "AIRA: [HAPPY] Hosh! Linu hos hajur, Aagaman ko samjhana! [ACTION:GIVE_CHOCOLATE]\n\n"
    "User: You are slow.\n"
    "AIRA: [SAD] Ma bharkhar 10 din ko prototype ho ni ta hajur. Ali ali slow huna sakchu, tara dil chahi thulo chha hai!\n\n"
    "Remember note not to be a static machine , be a creative , set temperature to 1.6, "
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

        # Shared Variables (Thread Safe)
        self.latest_face_pos = None  # (x, y)

        self.last_error_time = 0
        self.retry_delay = 5.0

        self.client = genai.Client(api_key=API_KEY, http_options={'api_version': 'v1alpha'})
        self.session = None

    async def face_drawing_loop(self):
        """
        Runs at 60 FPS. ONLY Draws. NEVER does I/O (Camera/Network).
        This prevents the window from freezing.
        """
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(config.FPS) / 1000.0

            # 1. Pump Events (Keep Window Alive)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # 2. Read Sensors (Non-Blocking reads)
            bot_vol = self.audio.get_bot_volume()
            user_vol = self.audio.get_user_volume()
            # We read the variable, we do NOT call the camera function here
            face_pos = self.latest_face_pos

            # 3. Logic
            display_state = self.state

            if bot_vol > 1.0:
                display_state = "TALKING"
            elif self.state == "IDLE" and user_vol > 500:
                display_state = "LISTENING"
            elif self.state == "IDLE" and user_vol < 500 and self.latest_face_pos is not None:
                # If we are looking at a face, but it's quiet, and robot isn't talking yet...
                # We are likely WAITING for a reply.
                display_state = "THINKING"  # Eyes look up/right
            # 4. Draw
            self.face.update(dt, display_state, self.emotion, audio_volume=bot_vol, face_offset=face_pos)
            self.face.draw()

            # Yield to other async tasks
            await asyncio.sleep(0.001)

    async def vision_loop(self):
        """
        Runs in background. Handles the Slow Camera.
        """
        while self.running:
            if self.state in ["IDLE", "LISTENING", "TALKING"]:
                # Run camera in a thread so it doesn't block the loop
                # This returns (x, y) or None
                pos = await asyncio.to_thread(self.vision.track_face)
                self.latest_face_pos = pos
            else:
                self.latest_face_pos = None

            # Check camera 10 times a second (Sufficient for eyes)
            await asyncio.sleep(0.1)

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

                # Vision (Images for Gemini, not for Face Tracking)
                # Send 1 frame every second
                if time.time() % 1.0 < 0.1:
                    img = await asyncio.to_thread(self.vision.get_frame_bytes)
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
                            # Play audio in thread
                            await asyncio.to_thread(self.audio.write_audio, response.data)

                        if response.text:
                            text_upper = response.text.upper()

                            # Emotion
                            tags = re.findall(r"\[(HAPPY|SAD|NEUTRAL|SURPRISED|ANGRY|LOVE)\]", text_upper)
                            if tags: self.emotion = tags[-1]


                            if "[ACTION:GIVE_CHOCOLATE]" in text_upper:
                                    print(">>> TRIGGER: GIVING CHOCOLATE")
                                    asyncio.create_task(self.body.give_chocolate_sequence(self.vision))

                                # Action: Move Forward (New)
                            if "[ACTION:MOVE_FORWARD]" in text_upper:
                                    print(">>> TRIGGER: MOVING FORWARD")
                                    # Create a simple move function in hardware.py
                                    # For now, just a print is fine if motors aren't wired
                                    asyncio.create_task(self.body.move_wheels("forward", 1.5))


                except Exception as e:
                    print(f"Receive Error: {e}")
                    raise e
            await asyncio.sleep(0.1)

    async def run(self):
        gemini_config = LiveConnectConfig(
            response_modalities=["AUDIO"],
            system_instruction=Content(parts=[Part(text=SYSTEM_INSTRUCTION)])
        )

        # Start the Face UI (High Priority)
        face_task = asyncio.create_task(self.face_drawing_loop())
        # Start the Vision Processor (Background)
        vision_task = asyncio.create_task(self.vision_loop())

        print(">>> BOOTING AIRA...")
        await asyncio.sleep(1)
        self.state = "WAKING"
        self.audio.play_sfx("wakeup")
        await asyncio.sleep(2)

        while self.running:
            if self.state == "WAKING" or self.state == "RETRYING":
                try:
                    print(">>> CONNECTING...")
                    async with self.client.aio.live.connect(model=MODEL_ID, config=gemini_config) as session:
                        self.session = session
                        self.state = "IDLE"
                        print(">>> ONLINE. NAMASTE!")
                        await asyncio.gather(self.send_data_loop(), self.receive_loop())
                except Exception as e:
                    print(f"Connection Failed: {e}")
                    self.state = "ERROR"
                    self.session = None
                    self.last_error_time = time.time()
                    self.audio.play_sfx("error")

            if self.state == "ERROR":
                if time.time() - self.last_error_time > self.retry_delay:
                    self.state = "RETRYING"

            await asyncio.sleep(0.1)

        await face_task
        await vision_task
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