"""
FlyHigh! - 3D Volleyball Game
Procedural Audio Generator and Sound Manager
Uses standard library wave module to synthesize arcade audio effects.
Zero external audio asset dependencies!
"""
import os
import wave
import struct
import math
import random
import pyray as pr

import sys

class AudioManager:
    def __init__(self, sounds_dir=None):
        if sounds_dir is None:
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
            self.sounds_dir = os.path.join(base_dir, "assets", "sounds")
        else:
            self.sounds_dir = sounds_dir

        self.sounds = {}
        self.enabled = True
        self.volume = 0.8
        self._init_sounds()

    def _init_sounds(self):
        os.makedirs(self.sounds_dir, exist_ok=True)
        self._generate_all_waves()
        
        # Raylib audio device init
        pr.init_audio_device()
        
        sound_names = ["whistle", "hit_bump", "hit_set", "hit_spike", "floor_bounce", "cheer", "point"]
        for name in sound_names:
            path = os.path.join(self.sounds_dir, f"{name}.wav")
            if os.path.exists(path):
                try:
                    snd = pr.load_sound(path)
                    pr.set_sound_volume(snd, self.volume)
                    self.sounds[name] = snd
                except Exception as e:
                    print(f"[Audio] Warning loading sound {name}: {e}")

    def _write_wav(self, filename, samples, sample_rate=44100):
        filepath = os.path.join(self.sounds_dir, filename)
        if os.path.exists(filepath):
            return  # Cache already created
        with wave.open(filepath, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            data = bytearray()
            for s in samples:
                val = int(max(-32767, min(32767, s * 32767)))
                data.extend(struct.pack('<h', val))
            wf.writeframes(data)

    def _generate_all_waves(self):
        sr = 44100
        
        # 1. Whistle (Referee two-tone trill)
        duration = 0.35
        n = int(sr * duration)
        samples = []
        for i in range(n):
            t = i / sr
            # Two frequencies beating for trill effect
            f1 = 2600 + 150 * math.sin(2 * math.pi * 35 * t)
            f2 = 2850 + 120 * math.sin(2 * math.pi * 32 * t)
            env = min(1.0, t / 0.02) * math.exp(-3.5 * t)
            val = 0.4 * (math.sin(2 * math.pi * f1 * t) + math.sin(2 * math.pi * f2 * t)) * env
            samples.append(val)
        self._write_wav("whistle.wav", samples, sr)

        # 2. Bump Hit (Soft deep cushion thud)
        duration = 0.18
        n = int(sr * duration)
        samples = []
        for i in range(n):
            t = i / sr
            freq = 140 * math.exp(-14 * t) + 60
            noise = (random.random() * 2.0 - 1.0) * 0.15 * math.exp(-35 * t)
            env = math.exp(-22 * t)
            val = (0.75 * math.sin(2 * math.pi * freq * t) + noise) * env
            samples.append(val)
        self._write_wav("hit_bump.wav", samples, sr)

        # 3. Set Hit (Crisp fingertip tap)
        duration = 0.14
        n = int(sr * duration)
        samples = []
        for i in range(n):
            t = i / sr
            freq = 380 * math.exp(-20 * t) + 180
            noise = (random.random() * 2.0 - 1.0) * 0.25 * math.exp(-40 * t)
            env = math.exp(-28 * t)
            val = (0.6 * math.sin(2 * math.pi * freq * t) + noise) * env
            samples.append(val)
        self._write_wav("hit_set.wav", samples, sr)

        # 4. Spike Hit (Explosive boom & sharp slap)
        duration = 0.38
        n = int(sr * duration)
        samples = []
        for i in range(n):
            t = i / sr
            bass_freq = 110 * math.exp(-12 * t) + 40
            bass = 0.8 * math.sin(2 * math.pi * bass_freq * t) * math.exp(-12 * t)
            slap_noise = (random.random() * 2.0 - 1.0) * 0.7 * math.exp(-38 * t)
            click = 0.6 * math.sin(2 * math.pi * 950 * t) * math.exp(-65 * t)
            val = bass + slap_noise + click
            samples.append(max(-1.0, min(1.0, val)))
        self._write_wav("hit_spike.wav", samples, sr)

        # 5. Floor Bounce (Gym floor bounce thud)
        duration = 0.22
        n = int(sr * duration)
        samples = []
        for i in range(n):
            t = i / sr
            freq = 160 * math.exp(-18 * t) + 50
            env = math.exp(-18 * t)
            val = 0.7 * math.sin(2 * math.pi * freq * t) * env
            samples.append(val)
        self._write_wav("floor_bounce.wav", samples, sr)

        # 6. Cheer (Crowd cheering swell)
        duration = 1.2
        n = int(sr * duration)
        samples = []
        accum = 0.0
        for i in range(n):
            t = i / sr
            white = (random.random() * 2.0 - 1.0)
            accum = accum * 0.92 + white * 0.08
            env = math.sin(math.pi * min(1.0, t / duration)) ** 1.5
            val = accum * env * 2.2
            samples.append(max(-1.0, min(1.0, val)))
        self._write_wav("cheer.wav", samples, sr)

        # 7. Point Chime (Sweet harmonic chime)
        duration = 0.45
        n = int(sr * duration)
        samples = []
        for i in range(n):
            t = i / sr
            c1 = math.sin(2 * math.pi * 587.33 * t) * 0.4  # D5
            c2 = math.sin(2 * math.pi * 880.0 * t) * 0.4   # A5
            env = math.exp(-7.0 * t)
            val = (c1 + c2) * env
            samples.append(val)
        self._write_wav("point.wav", samples, sr)

    def play(self, name):
        if not self.enabled or name not in self.sounds:
            return
        pr.play_sound(self.sounds[name])

    def toggle_mute(self):
        self.enabled = not self.enabled

    def close(self):
        for snd in self.sounds.values():
            pr.unload_sound(snd)
        pr.close_audio_device()
