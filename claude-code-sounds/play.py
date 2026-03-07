#!/usr/bin/env python3
import os
import sys
import random
import subprocess
import argparse
import shutil
from pathlib import Path

def play_sound(sound_path):
    if not sound_path or not sound_path.exists():
        return

    s_path = str(sound_path.resolve())

    if sys.platform == "darwin":  # macOS
        subprocess.Popen(["afplay", s_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif sys.platform == "win32": # Windows
        if s_path.lower().endswith(".wav"):
            import winsound
            winsound.PlaySound(s_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            # Note: Windows natively supports background .wav files.
            # .mp3 files without external dependencies might briefly open the default media player.
            os.startfile(s_path)
    else:                         # Linux
        if shutil.which("paplay"):
            subprocess.Popen(["paplay", s_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif shutil.which("aplay"):
            subprocess.Popen(["aplay", s_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    parser = argparse.ArgumentParser(description="Play Claude Code sounds")
    parser.add_argument("--context", action="store_true", help="Read stdin to determine sound")
    args = parser.parse_args()

    sounds_dir = Path(__file__).parent / "sounds"
    if not sounds_dir.exists():
        return

    sound_to_play = None

    if args.context:
        # Read hook output from stdin
        input_text = sys.stdin.read().lower()

        if any(word in input_text for word in ["complete", "done", "finished", "success"]):
            sound_to_play = sounds_dir / "jobs-done.mp3"
        elif any(word in input_text for word in ["error", "fail", "blocked"]):
            sound_to_play = sounds_dir / "stop-poking-me.mp3"
        else:
            sound_to_play = sounds_dir / "yes-me-lord.mp3"

        # Fallback to .wav if the .mp3 version doesn't exist
        if sound_to_play and not sound_to_play.exists():
            sound_to_play = sound_to_play.with_suffix('.wav')
    else:
        # Random playback
        sounds = list(sounds_dir.glob("*.mp3")) + list(sounds_dir.glob("*.wav"))
        if sounds:
            sound_to_play = random.choice(sounds)

    if sound_to_play:
        play_sound(sound_to_play)

if __name__ == "__main__":
    main()
