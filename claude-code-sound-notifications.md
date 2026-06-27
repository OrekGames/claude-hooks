# Claude Code Sound Notifications

This document records the shipped behavior of `claude-code-sounds`. The hook
README remains the source of truth for installation and use.

## Current Behavior

- `UserPromptSubmit` plays a random clip from `sounds/start/`.
- `Stop` plays a random clip from `sounds/done/`.
- Event names are discovered from subdirectories under `sounds/`.
- Bundled defaults are WAV files for portable playback.
- Custom `.wav`, `.mp3`, and `.m4a` files are accepted on a best-effort basis.
- The runtime uses only Python standard library modules and platform audio
  tools.

## Repository Layout

```text
claude-code-sounds/
├── README.md
├── play.py
├── setup.py
├── uninstall.py
├── settings.json.template
├── test_sounds.py
└── sounds/
    ├── start/
    │   ├── Ready to Work.wav
    │   ├── Righto.wav
    │   ├── Work Work.wav
    │   ├── Yes Me Lord.wav
    │   └── Zugg Zugg.wav
    └── done/
        └── Jobs Done.wav
```

## Hook Configuration

`setup.py` installs the hook into a target project at
`.claude/claude-code-sounds/` and writes absolute commands into
`.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"/absolute/path/to/target-project/.claude/claude-code-sounds/play.py\" --event start"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"/absolute/path/to/target-project/.claude/claude-code-sounds/play.py\" --event done"
          }
        ]
      }
    ]
  }
}
```

## Installer Notes

- Local install defaults to the current working directory as the target project.
- `--project PATH` installs into a specific project root.
- `--global` installs into `~/.claude`.
- `--yes` merges into existing settings without prompting.
- Re-running setup removes only existing `claude-code-sounds` command hooks and
  then writes the current start/done hooks.
- Setup copies bundled defaults without deleting custom sound files.
- Setup removes known legacy bundled `.m4a` defaults from install targets during
  upgrade.

## Uninstaller Notes

`uninstall.py` removes only command hooks whose command references
`claude-code-sounds`. If a matcher entry also contains unrelated hooks, those
hooks stay in place.
