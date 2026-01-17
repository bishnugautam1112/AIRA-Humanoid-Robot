# modules/audio_manager.py
import pyaudio
import numpy as np
import pygame
import os
import math
import config


class AudioManager:
    def __init__(self):
        # 1. Setup Local SFX
        pygame.mixer.init()
        self.sounds = {}
        self.load_sfx()

        # 2. Setup Streaming
        self.p = pyaudio.PyAudio()

        # Mic Input
        self.stream_in = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )

        # Speaker Output
        self.stream_out = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=24000,
            output=True
        )

        # Volatiles
        self.current_out_volume = 0.0
        self.current_in_volume = 0.0

    def load_sfx(self):
        if not os.path.exists(config.SOUNDS_DIR):
            try:
                os.makedirs(config.SOUNDS_DIR)
            except:
                pass

        sfx_map = {"wakeup": "wakeup.wav", "sleep": "sleep.wav", "error": "error.wav"}
        for name, filename in sfx_map.items():
            path = os.path.join(config.SOUNDS_DIR, filename)
            if os.path.exists(path):
                self.sounds[name] = pygame.mixer.Sound(path)

    def play_sfx(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    def calculate_rms(self, data):
        try:
            if not data: return 0
            shorts = np.frombuffer(data, dtype=np.int16)
            if len(shorts) == 0: return 0
            sum_squares = np.sum(shorts.astype(np.float64) ** 2)
            return math.sqrt(sum_squares / len(shorts))
        except:
            return 0

    def read_mic(self):
        if self.stream_in.get_read_available() > 0:
            data = self.stream_in.read(1024, exception_on_overflow=False)
            self.current_in_volume = self.calculate_rms(data)
            return data
        return None

    def write_audio(self, data):
        """
        Writes audio to speaker.
        CRITICAL FIX: Reset volume to 0 immediately after writing.
        """
        if data:
            # 1. Set Volume High -> Triggers "TALKING" state
            self.current_out_volume = self.calculate_rms(data)

            # 2. Write to stream -> This BLOCKS until the sound is heard
            self.stream_out.write(data)

            # 3. Audio finished? Reset Volume -> Triggers "IDLE" state
            self.current_out_volume = 0.0

    def get_user_volume(self):
        return self.current_in_volume

    def get_bot_volume(self):
        return self.current_out_volume

    def close(self):
        try:
            self.stream_in.stop_stream()
            self.stream_in.close()
            self.stream_out.stop_stream()
            self.stream_out.close()
            self.p.terminate()
        except:
            pass