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

    if sys.platform == "darwin":  # macOS — afplay supports mp3, wav, m4a
        subprocess.Popen(["afplay", s_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif sys.platform == "win32": # Windows
        if s_path.lower().endswith(".wav"):
            import winsound
            winsound.PlaySound(s_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            # Note: Windows natively supports background .wav files.
            # .mp3/.m4a files without external dependencies might briefly open the default media player.
            os.startfile(s_path)
    else:                         # Linux
        if shutil.which("paplay"):
            subprocess.Popen(["paplay", s_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif shutil.which("aplay"):
            subprocess.Popen(["aplay", s_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def all_sounds(sounds_dir):
    exts = ("*.mp3", "*.wav", "*.m4a")
    return [f for ext in exts for f in sounds_dir.glob(ext)]

def main():
    parser = argparse.ArgumentParser(description="Play Claude Code sounds")
    parser.add_argument("--context", action="store_true", help="Read stdin to determine sound")
    parser.add_argument("--event", choices=["start", "done"], help="Play sound for a specific event")
    args = parser.parse_args()

    sounds_dir = Path(__file__).parent / "sounds"
    if not sounds_dir.exists():
        return

    sound_to_play = None

    if args.event == "done":
        sound_to_play = sounds_dir / "Jobs Done.m4a"

    elif args.event == "start":
        candidates = [sounds_dir / "Zugg Zugg.m4a", sounds_dir / "Yes Me Lord.m4a"]
        candidates = [p for p in candidates if p.exists()]
        if candidates:
            sound_to_play = random.choice(candidates)

    elif args.context:
        # Read hook output from stdin
        input_text = sys.stdin.read().lower()

        if any(word in input_text for word in ["complete", "done", "finished", "success"]):
            sound_to_play = sounds_dir / "Jobs Done.m4a"
        else:
            candidates = [sounds_dir / "Zugg Zugg.m4a", sounds_dir / "Yes Me Lord.m4a"]
            candidates = [p for p in candidates if p.exists()]
            if candidates:
                sound_to_play = random.choice(candidates)

    else:
        # Random playback from all available sounds
        sounds = all_sounds(sounds_dir)
        if sounds:
            sound_to_play = random.choice(sounds)

    if sound_to_play:
        play_sound(sound_to_play)

if __name__ == "__main__":
    main()
