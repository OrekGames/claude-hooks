# Claude Code Sound Notifications

Play Warcraft 3 (or any) sound bites when Claude Code triggers events — task complete, errors, tool usage, etc. Distributed as a simple GitHub repo that users clone and run a setup script.

## Repo Structure

```
claude-code-sounds/
├── README.md              # Setup instructions (copy from this plan)
├── setup.py               # Automated installer
├── uninstall.py           # Clean removal
├── play.py                # Main player script (handles random and context-aware)
└── sounds/                # Sound files
    ├── jobs-done.mp3
    ├── yes-me-lord.mp3
    ├── ready-to-work.mp3
    ├── work-work.mp3
    ├── work-complete.mp3
    ├── stop-poking-me.mp3
    └── ...
```

## How It Works

Claude Code has a **hooks** system — shell commands that fire on events. This project configures hooks to play sound clips via macOS `afplay`, Linux `paplay`/`aplay`, or Windows `winsound`/`startfile`.

Hooks are configured in `~/.claude/settings.json` under the `hooks` key. Each hook has an event type, an optional matcher (tool name filter), and a command to run. The command receives the tool input/event data as stdin.

## Scripts

### play.py — Sound player (Random & Context-aware)

```python
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
```

### setup.py — Installer

```python
#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

def main():
    print("Claude Code Sound Notifications — Setup")
    print("=========================================\n")

    script_dir = Path(__file__).parent.resolve()
    settings_file = Path.home() / ".claude" / "settings.json"
    
    # Ensure ~/.claude exists
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Make play.py executable on Unix systems
    if sys.platform != "win32":
        play_script = script_dir / "play.py"
        if play_script.exists():
            play_script.chmod(play_script.stat().st_mode | 0o111)

    print("Which mode?")
    print("  1) Random sound on every notification")
    print("  2) Context-aware (different sounds for success/error/other)")
    
    while True:
        try:
            choice = input("Choice [1/2]: ").strip()
            if choice in ('1', '2'):
                break
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(1)

    # Build the command cross-platform
    py_bin = "python" if sys.platform == "win32" else "python3"
    cmd = f'{py_bin} "{script_dir / "play.py"}"'
    
    if choice == '2':
        cmd += ' --context'

    hooks_config = {
        "hooks": {
            "Notification": [
                {
                    "command": cmd
                }
            ]
        }
    }

    if settings_file.exists():
        print(f"\nExisting settings found at {settings_file}")
        print("The following hook will be added:")
        print(json.dumps(hooks_config, indent=2))
        
        try:
            confirm = input("\nMerge hooks into existing settings? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            confirm = 'n'
            
        if confirm not in ('y', 'yes'):
            print(f"Aborted. Add the hooks manually to {settings_file}")
            sys.exit(0)
            
        try:
            with open(settings_file, "r") as f:
                settings = json.load(f)
        except json.JSONDecodeError:
            print("Error parsing existing settings.json.")
            sys.exit(1)
            
        # Safely Merge
        settings.setdefault("hooks", {}).setdefault("Notification", []).append(
            hooks_config["hooks"]["Notification"][0]
        )
        
        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=2)
            
        print(f"\nHooks merged into {settings_file}")
    else:
        with open(settings_file, "w") as f:
            json.dump(hooks_config, f, indent=2)
        print(f"Created {settings_file}")

    print("\nDone! Sound notifications are now active.")
    print("Restart Claude Code for hooks to take effect.")

if __name__ == "__main__":
    main()
```

### uninstall.py — Clean removal

```python
#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def main():
    settings_file = Path.home() / ".claude" / "settings.json"
    
    print(f"Removing sound notification hooks from {settings_file}...\n")
    
    if not settings_file.exists():
        print("No settings file found. Nothing to do.")
        return
        
    try:
        with open(settings_file, "r") as f:
            settings = json.load(f)
    except json.JSONDecodeError:
        print("Error parsing settings.json.")
        sys.exit(1)
        
    if "hooks" in settings and "Notification" in settings["hooks"]:
        original_count = len(settings["hooks"]["Notification"])
        
        # Keep hooks that don't belong to our script
        settings["hooks"]["Notification"] = [
            hook for hook in settings["hooks"]["Notification"] 
            if "command" not in hook or "play.py" not in str(hook["command"])
        ]
        
        # Cleanup empty sections
        if not settings["hooks"]["Notification"]:
            del settings["hooks"]["Notification"]
        if not settings["hooks"]:
            del settings["hooks"]
            
        if "hooks" not in settings or len(settings.get("hooks", {}).get("Notification", [])) < original_count:
            with open(settings_file, "w") as f:
                json.dump(settings, f, indent=2)
            print("Hooks removed successfully.")
        else:
            print("No matching hooks found.")
    else:
        print("No hooks to remove.")
        
    print("Done. Restart Claude Code for changes to take effect.")

if __name__ == "__main__":
    main()
```

## Hook Configuration Reference

The setup script writes this to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Notification": [
      {
        "command": "python3 \"/path/to/claude-code-sounds/play.py\""
      }
    ]
  }
}
```

### Alternative: Per-tool-use hooks

For more granular control, users can manually configure `PostToolUse` hooks:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "SendMessage",
        "command": "python3 \"/path/to/claude-code-sounds/play.py\" --context"
      },
      {
        "matcher": "Bash",
        "command": "python3 \"/path/to/claude-code-sounds/play.py\""
      }
    ]
  }
}
```

## README.md Content (for the repo)

```markdown
# Claude Code Sounds

Play Warcraft 3 sound bites when Claude Code notifies you.

## Requirements

- Python 3
- Claude Code CLI

## Install

1. Clone this repo:
   git clone https://github.com/youruser/claude-code-sounds.git
   cd claude-code-sounds

2. Add your sound files to the `sounds/` directory (.mp3 or .wav)
   (Note: Windows users get best out-of-the-box results with .wav files)

3. Run the setup script:
   python3 setup.py
   (On Windows: python setup.py)

4. Restart Claude Code

## Uninstall

   python3 uninstall.py
   (On Windows: python uninstall.py)

## Adding Custom Sounds

Drop any `.mp3` or `.wav` files into the `sounds/` directory.
The random player picks from all files in that folder.

## Customization

Edit `play.py` to map keywords to specific sounds (in context mode).
Or configure per-tool hooks manually — see the setup plan for examples.
```

## TODO

- [ ] Collect WC3 sound files (peon, grunt, peasant, etc.)
- [ ] Create GitHub repo
- [ ] Test setup.py on clean macOS/Windows install
- [ ] Test Linux compatibility (paplay/aplay fallback)
