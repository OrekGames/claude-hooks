# Claude Code Sounds

Play Warcraft 3 sound bites when Claude Code notifies you.

## Requirements

- Python 3
- Claude Code CLI

## Install

1. Clone this repo:
   ```
   git clone https://github.com/youruser/claude-code-sounds.git
   cd claude-code-sounds
   ```

2. Add your sound files to the `sounds/` directory (.mp3 or .wav)
   (Note: Windows users get best out-of-the-box results with .wav files)

3. Run the setup script:
   ```
   python3 setup.py
   ```
   On Windows: `python setup.py`

4. Restart Claude Code

## Uninstall

```
python3 uninstall.py
```
On Windows: `python uninstall.py`

## Adding Custom Sounds

Drop any `.mp3` or `.wav` files into the `sounds/` directory.
The random player picks from all files in that folder.

## Customization

Edit `play.py` to map keywords to specific sounds (in context mode).
Or configure per-tool hooks manually — see the setup plan for examples.
