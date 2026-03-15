#!/usr/bin/env python3
import json
import shutil
import sys
from pathlib import Path

INSTALL_DIR = Path.home() / ".claude" / "claude-code-sounds"
SETTINGS_FILE = Path.home() / ".claude" / "settings.json"

def main():
    print(f"Removing sound notification hooks from {SETTINGS_FILE}...\n")

    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE) as f:
                settings = json.load(f)
        except json.JSONDecodeError:
            print("Error parsing settings.json.")
            sys.exit(1)

        hooks = settings.get("hooks", {})
        changed = False
        for event in ("UserPromptSubmit", "Stop"):
            if event in hooks:
                before = len(hooks[event])
                hooks[event] = [
                    h for h in hooks[event]
                    if "play.py" not in str(h.get("command", ""))
                ]
                if len(hooks[event]) < before:
                    changed = True
                if not hooks[event]:
                    del hooks[event]

        if not hooks:
            settings.pop("hooks", None)

        if changed:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(settings, f, indent=2)
            print("Hooks removed from settings.json.")
        else:
            print("No matching hooks found in settings.json.")
    else:
        print("No settings file found.")

    if INSTALL_DIR.exists():
        try:
            confirm = input(f"\nRemove install directory {INSTALL_DIR}? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            confirm = "n"

        if confirm in ("y", "yes"):
            shutil.rmtree(INSTALL_DIR)
            print(f"Removed {INSTALL_DIR}")

    print("\nDone. Restart Claude Code for changes to take effect.")

if __name__ == "__main__":
    main()
