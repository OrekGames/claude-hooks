#!/usr/bin/env python3
import argparse
import json
import shutil
import sys
from pathlib import Path

AUDIO_EXTS = {".mp3", ".wav", ".m4a"}
HOOK_MARKER = "claude-code-sounds"

LEGACY_DEFAULTS = (
    Path("sounds/start/Righto.m4a"),
    Path("sounds/start/Work Work.m4a"),
    Path("sounds/start/Yes Me Lord.m4a"),
    Path("sounds/start/Ready to Work.m4a"),
    Path("sounds/start/Zugg Zugg.m4a"),
    Path("sounds/done/Jobs Done.m4a"),
)


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


def copy_bundle(script_dir, install_dir):
    install_dir.mkdir(parents=True, exist_ok=True)

    if script_dir.resolve() != install_dir.resolve():
        shutil.copy2(script_dir / "play.py", install_dir / "play.py")

    sounds_src = script_dir / "sounds"
    sounds_dst = install_dir / "sounds"
    sounds_dst.mkdir(parents=True, exist_ok=True)

    for legacy_file in LEGACY_DEFAULTS:
        target = install_dir / legacy_file
        if target.is_file():
            target.unlink()

    if not sounds_src.exists():
        return

    for event_dir in sounds_src.iterdir():
        if not event_dir.is_dir():
            continue

        dst_event_dir = sounds_dst / event_dir.name
        dst_event_dir.mkdir(parents=True, exist_ok=True)

        for sound_file in event_dir.iterdir():
            if sound_file.is_file() and sound_file.suffix.lower() in AUDIO_EXTS:
                shutil.copy2(sound_file, dst_event_dir / sound_file.name)


def build_hooks(install_dir):
    py_bin = "python" if sys.platform == "win32" else "python3"
    play_path = str((install_dir / "play.py").resolve())
    play_cmd = f'{py_bin} "{play_path}"'

    return {
        "UserPromptSubmit": [
            {
                "matcher": "",
                "hooks": [
                    {"type": "command", "command": f"{play_cmd} --event start"}
                ],
            }
        ],
        "Stop": [
            {
                "matcher": "",
                "hooks": [
                    {"type": "command", "command": f"{play_cmd} --event done"}
                ],
            }
        ],
    }


def load_settings(settings_file):
    if not settings_file.exists():
        return {}

    try:
        with open(settings_file) as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error parsing {settings_file}.")
        sys.exit(1)


def write_settings(settings_file, settings):
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_file, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")


def install(script_dir, install_dir, settings_file, yes=False):
    script_dir = Path(script_dir).resolve()
    install_dir = Path(install_dir).resolve()
    settings_file = Path(settings_file)

    print(f"Installing to {install_dir} ...")
    copy_bundle(script_dir, install_dir)

    if sys.platform != "win32":
        (install_dir / "play.py").chmod(0o755)

    new_hooks = build_hooks(install_dir)

    if settings_file.exists() and not yes:
        print(f"\nExisting settings found at {settings_file}")
        print("The following hooks will be merged in:")
        for event, entries in new_hooks.items():
            print(f"  {event}: {entries[0]['hooks'][0]['command']}")

        if ask("\nMerge hooks into existing settings? [y/N]: ", "n") not in ("y", "yes"):
            print(f"Aborted. Add hooks manually to {settings_file}")
            sys.exit(0)

    settings = load_settings(settings_file)
    remove_managed_hooks(settings)

    hooks = settings.setdefault("hooks", {})
    for event, entries in new_hooks.items():
        hooks.setdefault(event, []).extend(entries)

    write_settings(settings_file, settings)
    print(f"\nHooks written to {settings_file}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Install Claude Code sound notification hooks."
    )
    parser.add_argument(
        "--project",
        metavar="PATH",
        help="Install into the given Claude Code project root.",
    )
    parser.add_argument(
        "--global",
        dest="global_install",
        action="store_true",
        help="Install into ~/.claude for all Claude Code projects.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Merge into existing settings without prompting.",
    )
    args = parser.parse_args()

    if args.project and args.global_install:
        parser.error("--project and --global cannot be used together")

    return args


def resolve_targets(args, script_dir):
    if args.global_install:
        install_dir = Path.home() / ".claude" / "claude-code-sounds"
        settings_file = Path.home() / ".claude" / "settings.json"
        return install_dir, settings_file

    if args.project:
        project_root = Path(args.project).expanduser().resolve()
    else:
        project_root = Path.cwd().resolve()
        if project_root == script_dir:
            print(
                "Error: setup is running from the hook source directory. "
                "Run it from the target project root, or pass --project "
                "/path/to/project.",
                file=sys.stderr,
            )
            sys.exit(2)

    install_dir = project_root / ".claude" / "claude-code-sounds"
    settings_file = project_root / ".claude" / "settings.json"
    return install_dir, settings_file


def main():
    print("Claude Code Sound Notifications — Setup")
    print("=========================================\n")
    script_dir = Path(__file__).parent.resolve()
    args = parse_args()
    install_dir, settings_file = resolve_targets(args, script_dir)

    install(script_dir, install_dir, settings_file, yes=args.yes)

    print("Done! Sound notifications are now active.")
    print("Restart Claude Code for hooks to take effect.")


if __name__ == "__main__":
    main()
