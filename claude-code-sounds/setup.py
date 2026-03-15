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

    # Build the command cross-platform
    py_bin = "python" if sys.platform == "win32" else "python3"
    play = f'{py_bin} "{script_dir / "play.py"}"'

    hooks_config = {
        "hooks": {
            "UserPromptSubmit": [
                {
                    "command": f'{play} --event start'
                }
            ],
            "Stop": [
                {
                    "command": f'{play} --event done'
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
        hooks = settings.setdefault("hooks", {})
        for event, entries in hooks_config["hooks"].items():
            hooks.setdefault(event, []).extend(entries)

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
