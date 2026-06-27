# OrekGames Claude Hooks

This repository publishes self-contained Claude Code hooks that can be copied
into other projects. Each hook keeps its code, assets, tests, and README in its
own top-level directory.

## Available Hooks

| Hook | Description |
| --- | --- |
| [claude-code-sounds](./claude-code-sounds) | Plays a random sound when Claude Code receives a prompt and when Claude Code stops. Bundled defaults are WAV files, and custom `.wav`, `.mp3`, or `.m4a` clips can be placed in event subdirectories. |

## Usage

Open the hook directory you want to use and follow its README. Hook directories
are intended to be copied or installed without shared repository infrastructure.

## Contributing

- Keep each hook self-contained.
- Prefer low-dependency implementations that are easy to audit.
- Update the repository README and the hook README whenever behavior, setup,
  supported events, or layout changes.
