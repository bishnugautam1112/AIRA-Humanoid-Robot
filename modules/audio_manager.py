# modules/audio_manager.py
import pyaudio
import numpy as np
import pygame
import os
import config


class AudioManager:
    def __init__(self):
        # 1. Setup Local SFX (Pygame Mixer)
        pygame.mixer.init()
        self.sounds = {}
        self.load_sfx()

        # 2. Setup Streaming (PyAudio)
        self.p = pyaudio.PyAudio()

        # Input Stream (Mic) - 16kHz, Mono
        self.stream_in = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )

        # Output Stream (Speaker) - 24kHz, Mono (Gemini Standard)
        self.stream_out = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=24000,
            output=True
        )

        self.current_out_volume = 0.0
        self.current_in_volume = 0.0

    def load_sfx(self):
        """Pre-load sound files to avoid lag later"""
        # Ensure directory exists
        if not os.path.exists(config.SOUNDS_DIR):
            os.makedirs(config.SOUNDS_DIR)
            print(f"[WARNING] Sound directory missing: {config.SOUNDS_DIR}")
            return

        # Map generic names to files
        sfx_map = {
            "wakeup": "wakeup.wav",
            "sleep": "sleep.wav",
            "hmm": "hmm.wav",
            "error": "error.wav"
        }

        for name, filename in sfx_map.items():
            path = os.path.join(config.SOUNDS_DIR, filename)
            if os.path.exists(path):
                self.sounds[name] = pygame.mixer.Sound(path)
            else:
                print(f"[WARN] Sound file not found: {filename}")

    def play_sfx(self, name):
        """Play a local sound file non-blocking"""
        if name in self.sounds:
            self.sounds[name].play()

    def read_mic(self):
        """Read chunk from mic and calculate volume"""
        if self.stream_in.get_read_available() > 0:
            data = self.stream_in.read(1024, exception_on_overflow=False)

            # Calculate Volume (RMS) for 'Listening' state
            numpy_data = np.frombuffer(data, dtype=np.int16)
            if len(numpy_data) > 0:
                self.current_in_volume = np.linalg.norm(numpy_data) / len(numpy_data)

            return data
        return None

    def write_audio(self, data):
        """Play audio chunk received from Gemini"""
        if data:
            self.stream_out.write(data)

            # Calculate Volume for 'Talking' Mouth Animation
            numpy_data = np.frombuffer(data, dtype=np.int16)
            if len(numpy_data) > 0:
                # Normalize roughly 0.0 to 1.0
                self.current_out_volume = (np.linalg.norm(numpy_data) / len(numpy_data)) / 100.0

    def get_user_volume(self):
        return self.current_in_volume

    def get_bot_volume(self):
        return self.current_out_volume

    def close(self):
        self.stream_in.stop_stream()
        self.stream_in.close()
        self.stream_out.stop_stream()
        self.stream_out.close()
        self.p.terminate()

    def detect_noise(self, threshold=2000):
        """Simple wake detection: Is it loud?"""
        if self.current_in_volume > threshold:
            return True
        return False