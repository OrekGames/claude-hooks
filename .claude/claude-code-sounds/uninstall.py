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


def remove_hooks(settings_file):
    if not settings_file.exists():
        print(f"No settings file found at {settings_file}")
        return

    try:
        with open(settings_file) as f:
            settings = json.load(f)
    except json.JSONDecodeError:
        print(f"Error parsing {settings_file}")
        sys.exit(1)

    hooks = settings.get("hooks", {})
    changed = False
    for event in ("UserPromptSubmit", "Stop"):
        if event in hooks:
            before = len(hooks[event])
            hooks[event] = [
                h for h in hooks[event]
                if not any(
                    "claude-code-sounds" in str(c.get("command", ""))
                    for c in h.get("hooks", [])
                )
            ]
            if len(hooks[event]) < before:
                changed = True
            if not hooks[event]:
                del hooks[event]

    if not hooks:
        settings.pop("hooks", None)

    if changed:
        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=2)
        print(f"Hooks removed from {settings_file}")
    else:
        print(f"No matching hooks found in {settings_file}")


def main():
    print("Claude Code Sound Notifications — Uninstall")
    print("=============================================\n")
    print("Uninstall mode:")
    print("  [L] Local  — project .claude/  (default)")
    print("  [g] Global — user ~/.claude/")

    mode = ask("\nChoose mode [L/g]: ", "l")
    global_mode = mode in ("g", "global")

    if global_mode:
        install_dir   = Path.home() / ".claude" / "claude-code-sounds"
        settings_file = Path.home() / ".claude" / "settings.json"
    else:
        project_root  = Path.cwd()
        install_dir   = project_root / ".claude" / "claude-code-sounds"
        settings_file = project_root / ".claude" / "settings.json"

    remove_hooks(settings_file)

    if install_dir.exists():
        if ask(f"\nRemove install directory {install_dir}? [y/N]: ", "n") in ("y", "yes"):
            shutil.rmtree(install_dir)
            print(f"Removed {install_dir}")

    print("\nDone. Restart Claude Code for changes to take effect.")


if __name__ == "__main__":
    main()
