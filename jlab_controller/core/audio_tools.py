"""Procedural Audio Tools: Burn-In Tool & Ambient Relaxation Noise Synthesizer."""

import math
import os
import random
import subprocess
import tempfile
import threading
import time
import wave
from typing import Optional

class AudioSynthesizer:
    """Synthesizes procedural noise signals (White, Pink, Brown, Sine Sweeps) for Burn-in and Relaxation."""

    @staticmethod
    def generate_white_noise(duration_sec: float = 5.0, sample_rate: int = 44100) -> bytes:
        total_samples = int(duration_sec * sample_rate)
        data = bytearray()
        for _ in range(total_samples):
            val = int(random.uniform(-16384, 16384))
            data.extend(val.to_bytes(2, byteorder="little", signed=True))
        return bytes(data)

    @staticmethod
    def generate_pink_noise(duration_sec: float = 5.0, sample_rate: int = 44100) -> bytes:
        """Voss-McCartney 1/f Pink Noise generation algorithm."""
        total_samples = int(duration_sec * sample_rate)
        data = bytearray()
        b0 = b1 = b2 = b3 = b4 = b5 = b6 = 0.0
        for _ in range(total_samples):
            white = random.uniform(-1.0, 1.0)
            b0 = 0.99886 * b0 + white * 0.0555179
            b1 = 0.99332 * b1 + white * 0.0750759
            b2 = 0.96900 * b2 + white * 0.1538520
            b3 = 0.86650 * b3 + white * 0.3104856
            b4 = 0.55000 * b4 + white * 0.5329522
            b5 = -0.7616 * b5 - white * 0.0168980
            pink = (b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362) * 0.11
            b6 = white * 0.115926
            val = max(-32767, min(32767, int(pink * 32767)))
            data.extend(val.to_bytes(2, byteorder="little", signed=True))
        return bytes(data)

    @staticmethod
    def generate_sine_sweep(duration_sec: float = 5.0, start_freq: float = 20.0, end_freq: float = 20000.0, sample_rate: int = 44100) -> bytes:
        total_samples = int(duration_sec * sample_rate)
        data = bytearray()
        for i in range(total_samples):
            t = i / sample_rate
            # Logarithmic frequency sweep
            freq = start_freq * (end_freq / start_freq) ** (t / duration_sec)
            val = int(math.sin(2 * math.pi * freq * t) * 16384)
            data.extend(val.to_bytes(2, byteorder="little", signed=True))
        return bytes(data)


class NoisePlayer:
    """Plays generated background noise tracks using standard Linux ALSA/PulseAudio/PipeWire utilities."""

    def __init__(self):
        self._proc: Optional[subprocess.Popen] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.active_mode: Optional[str] = None

    def play(self, noise_type: str = "pink") -> None:
        self.stop()
        self._running = True
        self.active_mode = noise_type
        self._thread = threading.Thread(target=self._play_loop, args=(noise_type,), daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        self.active_mode = None
        if self._proc:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=0.5)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            self._proc = None

    def _play_loop(self, noise_type: str) -> None:
        sample_rate = 44100
        duration = 4.0

        if noise_type == "pink":
            raw_pcm = AudioSynthesizer.generate_pink_noise(duration, sample_rate)
        elif noise_type == "white":
            raw_pcm = AudioSynthesizer.generate_white_noise(duration, sample_rate)
        elif noise_type == "sweep":
            raw_pcm = AudioSynthesizer.generate_sine_sweep(duration, 20.0, 20000.0, sample_rate)
        else:
            raw_pcm = AudioSynthesizer.generate_pink_noise(duration, sample_rate)

        # Write to temp WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = f.name
            with wave.open(f, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(raw_pcm)

        try:
            # Play in loop using pw-play / paplay / aplay
            player_bin = "pw-play"
            if subprocess.run(["which", "pw-play"], capture_output=True).returncode != 0:
                if subprocess.run(["which", "paplay"], capture_output=True).returncode == 0:
                    player_bin = "paplay"
                else:
                    player_bin = "aplay"

            while self._running:
                self._proc = subprocess.Popen([player_bin, wav_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self._proc.wait()
        except Exception:
            pass
        finally:
            if os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except Exception:
                    pass
