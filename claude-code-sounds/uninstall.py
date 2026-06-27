#!/usr/bin/env python3
import argparse
import json
import shutil
import sys
from pathlib import Path

HOOK_MARKER = "claude-code-sounds"


def ask(prompt, default=""):
    try:
        return input(prompt).strip().lower() or default
    except (EOFError, KeyboardInterrupt):
        return default


def is_managed_hook(hook):
    return (
        isinstance(hook, dict)
        and "command" in hook
        and HOOK_MARKER in str(hook.get("command", ""))
    )


def remove_managed_hooks(settings):
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return False

    changed = False
    for event, entries in list(hooks.items()):
        if not isinstance(entries, list):
            continue

        new_entries = []
        for entry in entries:
            if isinstance(entry, dict) and isinstance(entry.get("hooks"), list):
                kept_hooks = [
                    hook for hook in entry["hooks"]
                    if not is_managed_hook(hook)
                ]
                if len(kept_hooks) != len(entry["hooks"]):
                    changed = True
                    if kept_hooks:
                        new_entry = dict(entry)
                        new_entry["hooks"] = kept_hooks
                        new_entries.append(new_entry)
                else:
                    new_entries.append(entry)
            elif is_managed_hook(entry):
                changed = True
            else:
                new_entries.append(entry)

        if new_entries:
            hooks[event] = new_entries
        else:
            del hooks[event]
            changed = True

    if not hooks:
        settings.pop("hooks", None)

    return changed


def remove_hooks(settings_file):
    if not settings_file.exists():
        print(f"No settings file found at {settings_file}")
        return False

    try:
        with open(settings_file) as f:
            settings = json.load(f)
    except json.JSONDecodeError:
        print(f"Error parsing {settings_file}")
        sys.exit(1)

    changed = remove_managed_hooks(settings)
    if changed:
        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=2)
            f.write("\n")
        print(f"Hooks removed from {settings_file}")
    else:
        print(f"No matching hooks found in {settings_file}")

    return changed


def parse_args():
    parser = argparse.ArgumentParser(
        description="Uninstall Claude Code sound notification hooks."
    )
    parser.add_argument(
        "--project",
        metavar="PATH",
        help="Uninstall from the given Claude Code project root.",
    )
    parser.add_argument(
        "--global",
        dest="global_install",
        action="store_true",
        help="Uninstall from ~/.claude.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Remove the install directory without prompting.",
    )
    args = parser.parse_args()

    if args.project and args.global_install:
        parser.error("--project and --global cannot be used together")

    return args


def resolve_targets(args):
    if args.global_install:
        install_dir = Path.home() / ".claude" / "claude-code-sounds"
        settings_file = Path.home() / ".claude" / "settings.json"
    else:
        if args.project:
            project_root = Path(args.project).expanduser().resolve()
        else:
            project_root = Path.cwd().resolve()
        install_dir = project_root / ".claude" / "claude-code-sounds"
        settings_file = project_root / ".claude" / "settings.json"

    return install_dir, settings_file


def main():
    print("Claude Code Sound Notifications — Uninstall")
    print("=============================================\n")
    args = parse_args()
    install_dir, settings_file = resolve_targets(args)

    remove_hooks(settings_file)

    if install_dir.exists():
        if args.yes or ask(f"\nRemove install directory {install_dir}? [y/N]: ", "n") in ("y", "yes"):
            shutil.rmtree(install_dir)
            print(f"Removed {install_dir}")

    print("\nDone. Restart Claude Code for changes to take effect.")


if __name__ == "__main__":
    main()
