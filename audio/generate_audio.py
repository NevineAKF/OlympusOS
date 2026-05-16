"""
Generate emergency_call.wav using espeak (Ubuntu) or a fallback sine-wave WAV.
Run once on the server: python3 audio/generate_audio.py
"""
import os
import struct
import subprocess
import wave

TEXT = (
    "Officer, there is a crowd surge at Gate 4. "
    "We need immediate assistance. Evacuation corridor required. "
    "Approximately eighty thousand fans are attempting to exit. "
    "Gate 4 is at critical density. Please respond."
)
OUT = os.path.join(os.path.dirname(__file__), "emergency_call.wav")


def try_espeak():
    try:
        subprocess.run(
            ["espeak", "-s", "135", "-p", "45", "-a", "180", "-w", OUT, TEXT],
            check=True, capture_output=True,
        )
        print(f"espeak → {OUT}")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def try_gtts():
    try:
        from gtts import gTTS
        import tempfile, shutil
        tmp_mp3 = tempfile.mktemp(suffix=".mp3")
        gTTS(TEXT, lang="en").save(tmp_mp3)
        # Convert to WAV with ffmpeg (16 kHz mono for Speechmatics)
        subprocess.run(
            ["ffmpeg", "-y", "-i", tmp_mp3, "-ar", "16000", "-ac", "1", OUT],
            check=True, capture_output=True,
        )
        os.unlink(tmp_mp3)
        print(f"gTTS + ffmpeg → {OUT}")
        return True
    except Exception as e:
        print(f"gTTS failed: {e}")
        return False


def write_sine_fallback():
    """Write a 5-second 440Hz sine wave as a stand-in."""
    import math
    sample_rate = 16000
    duration    = 5
    freq        = 440
    samples = [
        int(32767 * math.sin(2 * math.pi * freq * i / sample_rate))
        for i in range(sample_rate * duration)
    ]
    packed = struct.pack(f"<{len(samples)}h", *samples)
    with wave.open(OUT, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(packed)
    print(f"Sine-wave fallback → {OUT}")


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    if not try_espeak():
        if not try_gtts():
            write_sine_fallback()
