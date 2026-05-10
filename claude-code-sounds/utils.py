from pathlib import Path


def ask(prompt, default=""):
    try:
        return input(prompt).strip().lower() or default
    except (EOFError, KeyboardInterrupt):
        return default


def get_paths(global_mode):
    if global_mode:
        install_dir = Path.home() / ".claude" / "claude-code-sounds"
        settings_file = Path.home() / ".claude" / "settings.json"
    else:
        project_root = Path.cwd()
        install_dir = project_root / ".claude" / "claude-code-sounds"
        settings_file = project_root / ".claude" / "settings.json"
    return install_dir, settings_file
