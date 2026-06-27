# Claude Code Sounds

Play random sound clips for Claude Code start and done events.

## Requirements

- Python 3
- Claude Code CLI
- One of the platform audio players used by `play.py`:
  - macOS: `afplay`
  - Linux: `paplay` or `aplay`
  - Windows: `winsound` for `.wav` files, or the default media app for other formats

Bundled defaults are `.wav` files because WAV is the most portable format across
macOS, Linux, and Windows. Custom `.mp3` and `.m4a` files are still accepted on a
best-effort basis.

## Install Into A Project

Run setup from the target project root, or pass the target project explicitly:

```bash
cd /absolute/path/to/target-project
python3 /absolute/path/to/claude-hooks/claude-code-sounds/setup.py --yes
```

```bash
python3 /absolute/path/to/claude-hooks/claude-code-sounds/setup.py \
  --project /absolute/path/to/target-project \
  --yes
```

On Windows, use `python` instead of `python3`.

Setup copies this hook into:

```text
target-project/
└── .claude/
    ├── settings.json
    └── claude-code-sounds/
        ├── play.py
        └── sounds/
            ├── start/
            └── done/
```

The generated hook commands use absolute paths to the installed `play.py`.
Running setup from the hook source directory without `--project` exits with an
instruction to choose a target project.

Restart Claude Code after installing.

## Global Install

To install into `~/.claude` for all Claude Code projects:

```bash
python3 /absolute/path/to/claude-hooks/claude-code-sounds/setup.py --global --yes
```

## Uninstall

Remove hooks from a project:

```bash
python3 /absolute/path/to/claude-hooks/claude-code-sounds/uninstall.py \
  --project /absolute/path/to/target-project \
  --yes
```

Remove a global install:

```bash
python3 /absolute/path/to/claude-hooks/claude-code-sounds/uninstall.py --global --yes
```

Uninstall removes only command hooks whose command references
`claude-code-sounds`; unrelated settings and sibling hooks are preserved.

## Events And Sound Layout

The event names come from subdirectories under `sounds/`.

```text
sounds/
├── start/   # UserPromptSubmit
│   ├── Righto.wav
│   └── ...
└── done/    # Stop
    └── Jobs Done.wav
```

Add custom clips to the matching event directory:

```text
.claude/claude-code-sounds/sounds/start/my-start-sound.wav
.claude/claude-code-sounds/sounds/done/my-done-sound.wav
```

Do not place loose audio files directly in `sounds/`; `play.py` looks inside
event subdirectories.

## Manual Playback

```bash
python3 claude-code-sounds/play.py --event start
python3 claude-code-sounds/play.py --event done
```

Without `--event`, `play.py` chooses from all event directories.
