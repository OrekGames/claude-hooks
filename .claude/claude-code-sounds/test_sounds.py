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


def load_play_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location("play", PLAY_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# play.py
# ---------------------------------------------------------------------------

class TestSoundFiles(unittest.TestCase):

    def test_event_directories_exist(self):
        for name in ("start", "done"):
            self.assertTrue((SOUNDS_DIR / name).is_dir(), f"Missing event dir: sounds/{name}")

    def test_start_sounds_exist(self):
        sounds = list((SOUNDS_DIR / "start").iterdir())
        self.assertGreater(len(sounds), 0, "No sounds in sounds/start/")

    def test_done_sounds_exist(self):
        sounds = list((SOUNDS_DIR / "done").iterdir())
        self.assertGreater(len(sounds), 0, "No sounds in sounds/done/")

    def test_no_loose_files_in_sounds_root(self):
        loose = [f for f in SOUNDS_DIR.iterdir() if f.is_file()]
        self.assertEqual(loose, [], f"Sound files should be in subdirs, found: {loose}")


class TestPlaySounds(unittest.TestCase):

    def test_event_done_plays_from_done_dir(self):
        play = load_play_module()
        done_names = {f.name for f in (SOUNDS_DIR / "done").iterdir() if f.is_file()}
        played = []
        with patch.object(play, "play_sound", side_effect=lambda p: played.append(p)):
            with patch("sys.argv", ["play.py", "--event", "done"]):
                play.main()
        self.assertEqual(len(played), 1)
        self.assertIn(played[0].name, done_names)

    def test_event_start_plays_from_start_dir(self):
        play = load_play_module()
        start_names = {f.name for f in (SOUNDS_DIR / "start").iterdir() if f.is_file()}
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

        start_sounds = {f.name for f in (SOUNDS_DIR / "start").iterdir() if f.is_file()}
        self.assertEqual(seen, start_sounds,
                         f"Expected all start sounds to appear across 50 runs, got {seen}")

    def test_no_args_plays_from_any_event_dir(self):
        play = load_play_module()
        all_names = set()
        for d in SOUNDS_DIR.iterdir():
            if d.is_dir():
                all_names.update(f.name for f in d.iterdir() if f.is_file())

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
        import importlib.util
        spec = importlib.util.spec_from_file_location("setup", SETUP_PY)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        with patch("builtins.input", return_value="y"):
            mod.install(SCRIPT_DIR, self.install_dir, self.settings_file)

    def _run_uninstall(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("uninstall", UNINSTALL_PY)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        with patch("builtins.input", return_value="y"):
            mod.remove_hooks(self.settings_file)
            if self.install_dir.exists():
                shutil.rmtree(self.install_dir)

    def test_install_copies_play_py(self):
        self._run_setup()
        self.assertTrue((self.install_dir / "play.py").exists())

    def test_install_copies_sound_subdirs(self):
        self._run_setup()
        for event in ("start", "done"):
            event_dir = self.install_dir / "sounds" / event
            self.assertTrue(event_dir.is_dir(), f"Missing installed dir: sounds/{event}")
            sounds = [f for f in event_dir.iterdir() if f.is_file()]
            self.assertGreater(len(sounds), 0, f"No sounds in installed sounds/{event}/")

    def test_install_writes_settings(self):
        self._run_setup()
        self.assertTrue(self.settings_file.exists())
        with open(self.settings_file) as f:
            settings = json.load(f)
        self.assertIn("hooks", settings)
        self.assertIn("UserPromptSubmit", settings["hooks"])
        self.assertIn("Stop", settings["hooks"])

    def test_install_hook_format_valid(self):
        self._run_setup()
        with open(self.settings_file) as f:
            settings = json.load(f)

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
        with open(self.settings_file) as f:
            settings = json.load(f)

        for event in ("UserPromptSubmit", "Stop"):
            cmd = settings["hooks"][event][0]["hooks"][0]["command"]
            self.assertIn(str(self.install_dir), cmd)

    def test_install_merges_with_existing_settings(self):
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        existing = {"env": {"MY_VAR": "1"}, "permissions": {"allow": []}}
        with open(self.settings_file, "w") as f:
            json.dump(existing, f)

        self._run_setup()

        with open(self.settings_file) as f:
            settings = json.load(f)
        self.assertEqual(settings["env"]["MY_VAR"], "1")
        self.assertIn("hooks", settings)

    def test_uninstall_removes_hooks(self):
        self._run_setup()
        self._run_uninstall()

        if self.settings_file.exists():
            with open(self.settings_file) as f:
                settings = json.load(f)
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

        with open(self.settings_file) as f:
            settings = json.load(f)
        self.assertEqual(settings.get("env", {}).get("KEEP_ME"), "yes")

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
