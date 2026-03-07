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
