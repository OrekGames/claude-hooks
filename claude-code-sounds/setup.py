#!/usr/bin/env python3
import json
import shutil
import sys
from pathlib import Path

INSTALL_DIR = Path.home() / ".claude" / "claude-code-sounds"
SETTINGS_FILE = Path.home() / ".claude" / "settings.json"

def main():
    print("Claude Code Sound Notifications — Setup")
    print("=========================================\n")

    script_dir = Path(__file__).parent.resolve()

    # Copy files to ~/.claude/claude-code-sounds/
    print(f"Installing to {INSTALL_DIR} ...")
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)

    shutil.copy2(script_dir / "play.py", INSTALL_DIR / "play.py")

    sounds_src = script_dir / "sounds"
    sounds_dst = INSTALL_DIR / "sounds"
    if sounds_src.exists():
        if sounds_dst.exists():
            shutil.rmtree(sounds_dst)
        shutil.copytree(sounds_src, sounds_dst)

    # Make play.py executable
    if sys.platform != "win32":
        (INSTALL_DIR / "play.py").chmod(0o755)

    py_bin = "python" if sys.platform == "win32" else "python3"
    play = f'{py_bin} "{INSTALL_DIR / "play.py"}"'

    hooks_config = {
        "hooks": {
            "UserPromptSubmit": [{"command": f"{play} --event start"}],
            "Stop": [{"command": f"{play} --event done"}]
        }
    }

    if SETTINGS_FILE.exists():
        print(f"\nExisting settings found at {SETTINGS_FILE}")
        print("The following hooks will be added:")
        print(json.dumps(hooks_config, indent=2))

        try:
            confirm = input("\nMerge hooks into existing settings? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            confirm = "n"

        if confirm not in ("y", "yes"):
            print(f"Aborted. Add the hooks manually to {SETTINGS_FILE}")
            sys.exit(0)

        try:
            with open(SETTINGS_FILE) as f:
                settings = json.load(f)
        except json.JSONDecodeError:
            print("Error parsing existing settings.json.")
            sys.exit(1)

        hooks = settings.setdefault("hooks", {})
        for event, entries in hooks_config["hooks"].items():
            hooks.setdefault(event, []).extend(entries)
    else:
        settings = hooks_config

    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

    print(f"\nHooks written to {SETTINGS_FILE}")
    print("Done! Sound notifications are now active.")
    print("Restart Claude Code for hooks to take effect.")

if __name__ == "__main__":
    main()
