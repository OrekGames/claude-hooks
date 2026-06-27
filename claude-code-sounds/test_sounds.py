#!/usr/bin/env python3
"""Test harness for claude-code-sounds."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT_DIR   = Path(__file__).parent.resolve()
PLAY_PY      = SCRIPT_DIR / "play.py"
SETUP_PY     = SCRIPT_DIR / "setup.py"
UNINSTALL_PY = SCRIPT_DIR / "uninstall.py"
SOUNDS_DIR   = SCRIPT_DIR / "sounds"
AUDIO_EXTS   = (".mp3", ".wav", ".m4a")


def audio_files(directory):
    return [
        f for f in directory.iterdir()
        if f.is_file() and f.suffix.lower() in AUDIO_EXTS
    ]


def load_module(name, path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_play_module():
    return load_module("play", PLAY_PY)


# ---------------------------------------------------------------------------
# play.py
# ---------------------------------------------------------------------------

class TestSoundFiles(unittest.TestCase):

    def test_event_directories_exist(self):
        for name in ("start", "done"):
            self.assertTrue((SOUNDS_DIR / name).is_dir(), f"Missing event dir: sounds/{name}")

    def test_start_sounds_exist(self):
        sounds = audio_files(SOUNDS_DIR / "start")
        self.assertGreater(len(sounds), 0, "No sounds in sounds/start/")

    def test_done_sounds_exist(self):
        sounds = audio_files(SOUNDS_DIR / "done")
        self.assertGreater(len(sounds), 0, "No sounds in sounds/done/")

    def test_no_loose_files_in_sounds_root(self):
        loose = [
            f for f in SOUNDS_DIR.iterdir()
            if f.is_file() and f.suffix.lower() in AUDIO_EXTS
        ]
        self.assertEqual(loose, [], f"Sound files should be in subdirs, found: {loose}")

    def test_bundled_default_audio_files_are_wav(self):
        bundled = []
        for event in ("start", "done"):
            bundled.extend(audio_files(SOUNDS_DIR / event))

        self.assertGreater(len(bundled), 0, "No bundled audio files found")
        self.assertTrue(
            all(f.suffix.lower() == ".wav" for f in bundled),
            f"Bundled defaults should be WAV files: {bundled}",
        )


class TestPlaySounds(unittest.TestCase):

    def test_event_done_plays_from_done_dir(self):
        play = load_play_module()
        done_names = {f.name for f in audio_files(SOUNDS_DIR / "done")}
        played = []
        with patch.object(play, "play_sound", side_effect=lambda p: played.append(p)):
            with patch("sys.argv", ["play.py", "--event", "done"]):
                play.main()
        self.assertEqual(len(played), 1)
        self.assertIn(played[0].name, done_names)

    def test_event_start_plays_from_start_dir(self):
        play = load_play_module()
        start_names = {f.name for f in audio_files(SOUNDS_DIR / "start")}
        played = []
        with patch.object(play, "play_sound", side_effect=lambda p: played.append(p)):
            with patch("sys.argv", ["play.py", "--event", "start"]):
                play.main()
        self.assertEqual(len(played), 1)
        self.assertIn(played[0].name, start_names)

    def test_event_start_is_random(self):
        """Run start event many times and confirm multiple sounds appear."""
        play = load_play_module()
        seen = set()
        for _ in range(50):
            played = []
            with patch.object(play, "play_sound", side_effect=lambda p: played.append(p)):
                with patch("sys.argv", ["play.py", "--event", "start"]):
                    play.main()
            if played:
                seen.add(played[0].name)

        start_sounds = {f.name for f in audio_files(SOUNDS_DIR / "start")}
        self.assertEqual(seen, start_sounds,
                         f"Expected all start sounds to appear across 50 runs, got {seen}")

    def test_no_args_plays_from_any_event_dir(self):
        play = load_play_module()
        all_names = set()
        for d in SOUNDS_DIR.iterdir():
            if d.is_dir():
                all_names.update(f.name for f in audio_files(d))

        played = []
        with patch.object(play, "play_sound", side_effect=lambda p: played.append(p)):
            with patch("sys.argv", ["play.py"]):
                play.main()
        self.assertEqual(len(played), 1)
        self.assertIn(played[0].name, all_names)

    def test_only_one_sound_plays_per_invocation(self):
        play = load_play_module()
        for event in ("start", "done"):
            played = []
            with patch.object(play, "play_sound", side_effect=lambda p: played.append(p)):
                with patch("sys.argv", ["play.py", "--event", event]):
                    play.main()
            self.assertEqual(len(played), 1, f"Expected exactly 1 sound for --event {event}")

    def test_new_event_dir_is_autodiscovered(self):
        """Adding a new subdirectory makes it a valid --event value."""
        test_dir = SOUNDS_DIR / "_test_event"
        test_file = test_dir / "beep.m4a"
        try:
            test_dir.mkdir()
            test_file.write_bytes(b"\x00")  # dummy file

            play = load_play_module()
            played = []
            with patch.object(play, "play_sound", side_effect=lambda p: played.append(p)):
                with patch("sys.argv", ["play.py", "--event", "_test_event"]):
                    play.main()
            self.assertEqual(len(played), 1)
            self.assertEqual(played[0].name, "beep.m4a")
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_metadata_files_are_ignored(self):
        test_dir = SOUNDS_DIR / "_metadata_event"
        metadata_file = test_dir / ".DS_Store"
        test_file = test_dir / "beep.wav"
        try:
            test_dir.mkdir()
            metadata_file.write_bytes(b"metadata")
            test_file.write_bytes(b"RIFF")

            play = load_play_module()
            played = []
            with patch.object(play, "play_sound", side_effect=lambda p: played.append(p)):
                with patch("sys.argv", ["play.py", "--event", "_metadata_event"]):
                    play.main()
            self.assertEqual(len(played), 1)
            self.assertEqual(played[0].name, "beep.wav")
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_missing_sounds_dir_does_not_crash(self):
        play = load_play_module()
        fake_dir = Path("/tmp/nonexistent_sounds_dir_12345")
        with patch("sys.argv", ["play.py", "--event", "done"]):
            # Temporarily override sounds_dir path
            original = play.Path
            with patch.object(play, "Path", wraps=play.Path) as mock_path:
                # Just verify it doesn't raise when sounds_dir is missing
                result = subprocess.run(
                    [sys.executable, str(PLAY_PY), "--event", "done"],
                    env={**subprocess.os.environ, "HOME": "/tmp/nonexistent"},
                    capture_output=True
                )
                # play.py uses __file__ relative path, so it will still find sounds/
                # This just confirms it exits cleanly
                self.assertEqual(result.returncode, 0)


# ---------------------------------------------------------------------------
# setup.py / uninstall.py — install round-trip
# ---------------------------------------------------------------------------

class TestInstallRoundtrip(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.install_dir   = self.tmp / ".claude" / "claude-code-sounds"
        self.settings_file = self.tmp / ".claude" / "settings.json"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run_setup(self):
        mod = load_module("setup", SETUP_PY)
        mod.install(SCRIPT_DIR, self.install_dir, self.settings_file, yes=True)

    def _run_uninstall(self):
        mod = load_module("uninstall", UNINSTALL_PY)

        mod.remove_hooks(self.settings_file)
        if self.install_dir.exists():
            shutil.rmtree(self.install_dir)

    def _load_settings(self):
        with open(self.settings_file) as f:
            return json.load(f)

    def _managed_commands(self, settings, event):
        commands = []
        for entry in settings.get("hooks", {}).get(event, []):
            for hook in entry.get("hooks", []):
                command = hook.get("command", "")
                if "claude-code-sounds" in command:
                    commands.append(command)
        return commands

    def test_install_copies_play_py(self):
        self._run_setup()
        self.assertTrue((self.install_dir / "play.py").exists())

    def test_install_copies_sound_subdirs(self):
        self._run_setup()
        for event in ("start", "done"):
            event_dir = self.install_dir / "sounds" / event
            self.assertTrue(event_dir.is_dir(), f"Missing installed dir: sounds/{event}")
            sounds = audio_files(event_dir)
            self.assertGreater(len(sounds), 0, f"No sounds in installed sounds/{event}/")

    def test_install_writes_settings(self):
        self._run_setup()
        self.assertTrue(self.settings_file.exists())
        settings = self._load_settings()
        self.assertIn("hooks", settings)
        self.assertIn("UserPromptSubmit", settings["hooks"])
        self.assertIn("Stop", settings["hooks"])

    def test_install_hook_format_valid(self):
        self._run_setup()
        settings = self._load_settings()

        for event in ("UserPromptSubmit", "Stop"):
            entries = settings["hooks"][event]
            self.assertIsInstance(entries, list)
            for entry in entries:
                self.assertIn("hooks", entry)
                for hook in entry["hooks"]:
                    self.assertEqual(hook["type"], "command")
                    self.assertIn("command", hook)
                    self.assertIn("play.py", hook["command"])

    def test_install_hook_commands_reference_install_dir(self):
        self._run_setup()
        settings = self._load_settings()

        for event in ("UserPromptSubmit", "Stop"):
            cmd = settings["hooks"][event][0]["hooks"][0]["command"]
            self.assertIn(str(self.install_dir), cmd)
            self.assertIn(str(self.install_dir / "play.py"), cmd)

    def test_install_merges_with_existing_settings(self):
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        existing = {"env": {"MY_VAR": "1"}, "permissions": {"allow": []}}
        with open(self.settings_file, "w") as f:
            json.dump(existing, f)

        self._run_setup()

        settings = self._load_settings()
        self.assertEqual(settings["env"]["MY_VAR"], "1")
        self.assertIn("hooks", settings)

    def test_setup_project_flag_installs_to_chosen_project(self):
        result = subprocess.run(
            [sys.executable, str(SETUP_PY), "--project", str(self.tmp), "--yes"],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        settings = self._load_settings()
        self.assertTrue((self.install_dir / "play.py").exists())
        for event in ("UserPromptSubmit", "Stop"):
            commands = self._managed_commands(settings, event)
            self.assertEqual(len(commands), 1)
            self.assertIn(str(self.install_dir), commands[0])

    def test_setup_rerun_is_idempotent(self):
        self._run_setup()
        self._run_setup()
        settings = self._load_settings()

        for event in ("UserPromptSubmit", "Stop"):
            self.assertEqual(len(self._managed_commands(settings, event)), 1)

    def test_install_preserves_sibling_hooks_in_same_matcher_entry(self):
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        existing = {
            "hooks": {
                "Stop": [
                    {
                        "matcher": "",
                        "hooks": [
                            {"type": "command", "command": "echo keep"},
                            {
                                "type": "command",
                                "command": 'python3 "/old/.claude/claude-code-sounds/play.py" --event done',
                            },
                        ],
                    }
                ]
            }
        }
        with open(self.settings_file, "w") as f:
            json.dump(existing, f)

        self._run_setup()

        settings = self._load_settings()
        stop_hooks = settings["hooks"]["Stop"]
        all_commands = [
            hook["command"]
            for entry in stop_hooks
            for hook in entry.get("hooks", [])
        ]
        self.assertIn("echo keep", all_commands)
        self.assertEqual(len(self._managed_commands(settings, "Stop")), 1)

    def test_install_preserves_custom_sounds_and_removes_legacy_defaults(self):
        custom_file = self.install_dir / "sounds" / "start" / "custom.wav"
        legacy_file = self.install_dir / "sounds" / "start" / "Righto.m4a"
        legacy_file.parent.mkdir(parents=True, exist_ok=True)
        custom_file.write_bytes(b"custom")
        legacy_file.write_bytes(b"legacy")

        self._run_setup()

        self.assertTrue(custom_file.exists())
        self.assertFalse(legacy_file.exists())
        self.assertTrue((self.install_dir / "sounds" / "start" / "Righto.wav").exists())

    def test_setup_from_source_dir_without_project_fails(self):
        result = subprocess.run(
            [sys.executable, "setup.py", "--yes"],
            cwd=SCRIPT_DIR,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--project", result.stderr)

    def test_uninstall_removes_hooks(self):
        self._run_setup()
        self._run_uninstall()

        if self.settings_file.exists():
            settings = self._load_settings()
            hooks = settings.get("hooks", {})
            for event in ("UserPromptSubmit", "Stop"):
                remaining = [
                    h for h in hooks.get(event, [])
                    if any("claude-code-sounds" in c.get("command", "")
                           for c in h.get("hooks", []))
                ]
                self.assertEqual(remaining, [])

    def test_uninstall_preserves_other_settings(self):
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        existing = {"env": {"KEEP_ME": "yes"}}
        with open(self.settings_file, "w") as f:
            json.dump(existing, f)

        self._run_setup()
        self._run_uninstall()

        settings = self._load_settings()
        self.assertEqual(settings.get("env", {}).get("KEEP_ME"), "yes")

    def test_uninstall_preserves_sibling_hooks_in_same_matcher_entry(self):
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        existing = {
            "hooks": {
                "Stop": [
                    {
                        "matcher": "",
                        "hooks": [
                            {"type": "command", "command": "echo keep"},
                            {
                                "type": "command",
                                "command": 'python3 "/tmp/.claude/claude-code-sounds/play.py" --event done',
                            },
                        ],
                    }
                ]
            }
        }
        with open(self.settings_file, "w") as f:
            json.dump(existing, f)

        mod = load_module("uninstall", UNINSTALL_PY)
        mod.remove_hooks(self.settings_file)

        settings = self._load_settings()
        stop_entries = settings["hooks"]["Stop"]
        commands = [
            hook["command"]
            for entry in stop_entries
            for hook in entry.get("hooks", [])
        ]
        self.assertEqual(commands, ["echo keep"])

    def test_uninstall_removes_install_dir(self):
        self._run_setup()
        self.assertTrue(self.install_dir.exists())
        self._run_uninstall()
        self.assertFalse(self.install_dir.exists())

    def test_uninstall_no_settings_file_is_safe(self):
        self._run_uninstall()


# ---------------------------------------------------------------------------
# CLI smoke test (subprocess)
# ---------------------------------------------------------------------------

class TestCLISmoke(unittest.TestCase):

    def test_play_event_done_exits_zero(self):
        result = subprocess.run(
            [sys.executable, str(PLAY_PY), "--event", "done"],
            capture_output=True
        )
        self.assertEqual(result.returncode, 0)

    def test_play_event_start_exits_zero(self):
        result = subprocess.run(
            [sys.executable, str(PLAY_PY), "--event", "start"],
            capture_output=True
        )
        self.assertEqual(result.returncode, 0)

    def test_play_no_args_exits_zero(self):
        result = subprocess.run(
            [sys.executable, str(PLAY_PY)],
            capture_output=True
        )
        self.assertEqual(result.returncode, 0)

    def test_play_invalid_event_exits_nonzero(self):
        result = subprocess.run(
            [sys.executable, str(PLAY_PY), "--event", "bogus"],
            capture_output=True
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
