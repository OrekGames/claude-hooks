#!/usr/bin/env python3
import json
import shutil
import sys
from pathlib import Path


def ask(prompt, default=""):
    try:
        return input(prompt).strip().lower() or default
    except (EOFError, KeyboardInterrupt):
        return default


def install(script_dir, install_dir, settings_file):
    print(f"Installing to {install_dir} ...")
    install_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(script_dir / "play.py", install_dir / "play.py")

    sounds_dst = install_dir / "sounds"
    sounds_src = script_dir / "sounds"
    if sounds_src.exists():
        if sounds_dst.exists():
            shutil.rmtree(sounds_dst)
        shutil.copytree(sounds_src, sounds_dst)

    if sys.platform != "win32":
        (install_dir / "play.py").chmod(0o755)

    py_bin = "python" if sys.platform == "win32" else "python3"
    play_cmd = f'{py_bin} "{install_dir / "play.py"}"'

    new_hooks = {
        "UserPromptSubmit": [{"hooks": [{"type": "command", "command": f"{play_cmd} --event start"}]}],
        "Stop":             [{"hooks": [{"type": "command", "command": f"{play_cmd} --event done"}]}],
    }

    if settings_file.exists():
        print(f"\nExisting settings found at {settings_file}")
        print("The following hooks will be merged in:")
        for event, entries in new_hooks.items():
            print(f"  {event}: {entries[0]['hooks'][0]['command']}")

        if ask("\nMerge hooks into existing settings? [y/N]: ", "n") not in ("y", "yes"):
            print(f"Aborted. Add hooks manually to {settings_file}")
            sys.exit(0)

        try:
            with open(settings_file) as f:
                settings = json.load(f)
        except json.JSONDecodeError:
            print("Error parsing existing settings.json.")
            sys.exit(1)

        hooks = settings.setdefault("hooks", {})
        for event, entries in new_hooks.items():
            hooks.setdefault(event, []).extend(entries)
    else:
        settings = {"hooks": new_hooks}

    settings_file.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_file, "w") as f:
        json.dump(settings, f, indent=2)

    print(f"\nHooks written to {settings_file}")


def main():
    print("Claude Code Sound Notifications — Setup")
    print("=========================================\n")
    print("Install mode:")
    print("  [L] Local  — project .claude/  (default, recommended)")
    print("  [g] Global — user ~/.claude/")

    mode = ask("\nChoose mode [L/g]: ", "l")
    global_mode = mode in ("g", "global")

    script_dir = Path(__file__).parent.resolve()

    if global_mode:
        install_dir   = Path.home() / ".claude" / "claude-code-sounds"
        settings_file = Path.home() / ".claude" / "settings.json"
    else:
        # Local: install relative to cwd (the project root)
        project_root  = Path.cwd()
        install_dir   = project_root / ".claude" / "claude-code-sounds"
        settings_file = project_root / ".claude" / "settings.json"

    install(script_dir, install_dir, settings_file)

    print("Done! Sound notifications are now active.")
    print("Restart Claude Code for hooks to take effect.")


if __name__ == "__main__":
    main()
