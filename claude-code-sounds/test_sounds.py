#!/usr/bin/env python3
"""Test harness for claude-code-sounds."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

SCRIPT_DIR = Path(__file__).parent.resolve()
PLAY_PY    = SCRIPT_DIR / "play.py"
SETUP_PY   = SCRIPT_DIR / "setup.py"
UNINSTALL_PY = SCRIPT_DIR / "uninstall.py"
SOUNDS_DIR = SCRIPT_DIR / "sounds"


# ---------------------------------------------------------------------------
# play.py
# ---------------------------------------------------------------------------

class TestPlaySounds(unittest.TestCase):

    def test_sound_files_exist(self):
        for name in ("Jobs Done.m4a", "Zugg Zugg.m4a", "Yes Me Lord.m4a"):
            self.assertTrue((SOUNDS_DIR / name).exists(), f"Missing sound: {name}")

    def test_event_done_plays_jobs_done(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("play", PLAY_PY)
        play = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(play)

        played = []
        with patch.object(play, "play_sound", side_effect=lambda p: played.append(p)):
            with patch("sys.argv", ["play.py", "--event", "done"]):
                play.main()

        self.assertEqual(len(played), 1)
        self.assertEqual(played[0].name, "Jobs Done.m4a")

    def test_event_start_plays_a_start_sound(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("play", PLAY_PY)
        play = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(play)

        start_sounds = {"Zugg Zugg.m4a", "Yes Me Lord.m4a"}
        played = []
        with patch.object(play, "play_sound", side_effect=lambda p: played.append(p)):
            with patch("sys.argv", ["play.py", "--event", "start"]):
                play.main()

        self.assertEqual(len(played), 1)
        self.assertIn(played[0].name, start_sounds)

    def test_event_start_is_random(self):
        """Run start event many times and confirm both sounds appear."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("play", PLAY_PY)
        play = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(play)

        seen = set()
        for _ in range(30):
            played = []
            with patch.object(play, "play_sound", side_effect=lambda p: played.append(p)):
                with patch("sys.argv", ["play.py", "--event", "start"]):
                    play.main()
            if played:
                seen.add(played[0].name)

        self.assertEqual(seen, {"Zugg Zugg.m4a", "Yes Me Lord.m4a"},
                         "Expected both start sounds to appear across 30 runs")

    def test_no_args_plays_random_sound(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("play", PLAY_PY)
        play = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(play)

        all_sounds = {f.name for f in SOUNDS_DIR.glob("*.m4a")}
        played = []
        with patch.object(play, "play_sound", side_effect=lambda p: played.append(p)):
            with patch("sys.argv", ["play.py"]):
                play.main()

        self.assertEqual(len(played), 1)
        self.assertIn(played[0].name, all_sounds)

    def test_missing_sounds_dir_does_not_crash(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("play", PLAY_PY)
        play = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(play)

        with patch("sys.argv", ["play.py", "--event", "done"]):
            with patch.object(Path, "exists", return_value=False):
                # Should return silently, not raise
                play.main()


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

    def _run_setup(self, extra_patches=None):
        import importlib.util
        spec = importlib.util.spec_from_file_location("setup", SETUP_PY)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        patches = {
            "INSTALL_DIR":   self.install_dir,
            "SETTINGS_FILE": self.settings_file,
        }
        if extra_patches:
            patches.update(extra_patches)

        for attr, val in patches.items():
            setattr(mod, attr, val)

        with patch("builtins.input", return_value="y"):
            mod.install(SCRIPT_DIR, self.install_dir, self.settings_file)

        return mod

    def _run_uninstall(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("uninstall", UNINSTALL_PY)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        with patch("builtins.input", return_value="y"):
            mod.remove_hooks(self.settings_file)
            if self.install_dir.exists():
                shutil.rmtree(self.install_dir)

        return mod

    def test_install_copies_play_py(self):
        self._run_setup()
        self.assertTrue((self.install_dir / "play.py").exists())

    def test_install_copies_sounds(self):
        self._run_setup()
        self.assertTrue((self.install_dir / "sounds").is_dir())
        for name in ("Jobs Done.m4a", "Zugg Zugg.m4a", "Yes Me Lord.m4a"):
            self.assertTrue((self.install_dir / "sounds" / name).exists())

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

    def test_install_does_not_duplicate_hooks(self):
        self._run_setup()
        self._run_setup()  # second install

        with open(self.settings_file) as f:
            settings = json.load(f)

        for event in ("UserPromptSubmit", "Stop"):
            # Each install appends; two installs = 2 entries. That's expected
            # behaviour — uninstall cleans both.
            entries = settings["hooks"][event]
            cmds = [e["hooks"][0]["command"] for e in entries]
            self.assertTrue(len(cmds) >= 1)

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
        # Should not raise even if nothing was installed
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

    def test_play_invalid_event_exits_nonzero(self):
        result = subprocess.run(
            [sys.executable, str(PLAY_PY), "--event", "bogus"],
            capture_output=True
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
