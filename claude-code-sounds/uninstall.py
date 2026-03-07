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
