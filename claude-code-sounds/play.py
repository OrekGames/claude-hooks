#!/usr/bin/env python3
import os
import sys
import random
import subprocess
import argparse
import shutil
from pathlib import Path

AUDIO_EXTS = (".mp3", ".wav", ".m4a")


def play_sound(sound_path):
    if not sound_path or not sound_path.exists():
        return

    s_path = str(sound_path.resolve())

    if sys.platform == "darwin":  # macOS — afplay supports mp3, wav, m4a
        subprocess.Popen(["afplay", s_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif sys.platform == "win32":  # Windows
        if s_path.lower().endswith(".wav"):
            import winsound
            winsound.PlaySound(s_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            os.startfile(s_path)
    else:  # Linux
        if shutil.which("paplay"):
            subprocess.Popen(["paplay", s_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif shutil.which("aplay"):
            subprocess.Popen(["aplay", s_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def find_sounds(directory):
    """Return all audio files in a directory."""
    return [f for f in directory.iterdir() if f.is_file() and f.suffix.lower() in AUDIO_EXTS]


def main():
    sounds_dir = Path(__file__).parent / "sounds"

    # Build the list of available event names from subdirectories
    available_events = []
    if sounds_dir.exists():
        available_events = sorted(d.name for d in sounds_dir.iterdir() if d.is_dir())

    parser = argparse.ArgumentParser(description="Play Claude Code sounds")
    parser.add_argument("--event", choices=available_events or None,
                        help="Play a random sound for the given event type")
    args = parser.parse_args()

    if not sounds_dir.exists():
        return

    if args.event:
        event_dir = sounds_dir / args.event
        candidates = find_sounds(event_dir) if event_dir.is_dir() else []
    else:
        # No event specified — pick from all sounds across all event dirs
        candidates = []
        for d in sounds_dir.iterdir():
            if d.is_dir():
                candidates.extend(find_sounds(d))

    if candidates:
        play_sound(random.choice(candidates))


if __name__ == "__main__":
    main()
