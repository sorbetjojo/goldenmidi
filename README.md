<div align="center">
  
# GoldenMIDI
GoldenMIDI translates live MIDI input or MIDI files into Webfishing guitar input through keyboard and mouse. It features MIDI velocity support (so it actually reacts to how hard you play), configurable string/fret mapping, transpose functionality, and adjustable note cooldown speed (to balance between accuracy and performance on lower FPS)
</div>

## Features
- Detects realtime notes from your MIDI controller and maps them to in-game strings/frets.
- Load and play `.mid`/`.midi` files automatically in the game
- Toggle whether incoming MIDI velocity affects the strum (on) or use a fixed velocity (off).
- Scale incoming velocities up or down to make strums stronger or softer.
- Option to ignore notes with a velocity lower than the treshold, so quiet notes don’t trigger.
- Add a short delay between actions to balance accuracy and performance on low FPS.
- Shift notes up/down by semitones.

## Quick Start

1. Download the latest release from the [Releases page](https://github.com/sorbetjojo/goldenmidi/releases).
2. Extract the files to your preferred location.
3. Open Webfishing and make sure to be in guitar playing mode.
4. Run `goldenmidi.exe`.
5. Select MIDI Input or MIDI File playback.
6. Enjoy :]

## How It Works

GoldenMIDI translates MIDI notes to Webfishing guitar controls:
- Maps MIDI notes to guitar strings (1-6) and frets (0-15).
- Handles note velocity for realistic strumming dynamics by using the 6 playable strings on the right.
- Automatically focuses the Webfishing window during playback.

## Configuration

The tool creates a `config.json` file with customizable settings:

### Quick Settings Menu
Access via the main menu option `[3] Quick Settings`:

- `Use Velocity` Enable/disable velocity-sensitive strumming.
- `Velocity Multiplier` Adjust strumming intensity.
- `Velocity Threshold` Minimum velocity to trigger notes.
- `Cooldown` Delay between actions.
- `Transpose` Shift all notes up/down in semitones.

### Advanced Configuration
Edit `config.json` directly for fine-tuning:
- You can change all note/string positions, especially necessary if you have different screen resolution other than 1920x1080.

## Requirements

- Webfishing
- Windows OS
- MIDI Device (optional)

## MIDI File Support

Place MIDI files in the `midi` folder in the same directory, or select from anywhere on your system. The tool supports standard `.mid` and `.midi` formats.

## Troubleshooting

### Common Issues
- **"Webfishing window not found"** -> Make sure Webfishing is open and the window title starts with `"WEBFISHING v"`.
- **Some notes not playing** -> Increase the cooldown value in `Quick Settings`.
- **Wrong positioning** -> Adjust mouse coordinates in `config.json` for your screen resolution.

## Controls

### Main Menu
- `[1]` -> MIDI Input mode
- `[2]` -> MIDI File playback  
- `[3]` -> Quick Settings

### During Playback
- `[0]` -> Stop and return to menu
- Any other key -> Stop playback (MIDI files only)

## Building from Source

```
git clone https://github.com/sorbetjojo/goldenmidi
cd goldenmidi
pip install -r requirements.txt
python main.py
```
