# Gesture Controller

Control your slides and your video player with hand gestures. The program watches your webcam, works out which fingers you are holding up, and presses the matching keyboard shortcut for the app you are using.

Built with Python, OpenCV, MediaPipe and PyAutoGUI by Aman Prajapati.

## Supported apps

| App | What it controls |
| --- | --- |
| Google Slides | Slides |
| PowerPoint | Slides |
| LibreOffice Impress | Slides |
| YouTube (in a browser) | Play / pause, seek, volume, mute |
| VLC media player | Play / pause, seek, volume, mute |
| Other slides or PDF viewers | Slides (generic keys) |

On Windows the program reads the title of the window in front and switches to the right app by itself. On Mac and Linux, press `m` in the camera window until the correct app name appears.

## Gestures

Fingers are counted as index, middle, ring and pinky. The thumb is ignored.

### Slides

| Gesture | Action |
| --- | --- |
| Open palm | Next slide |
| 3 fingers (index, middle, ring) | Previous slide |
| 2 fingers (index, middle) | Start slideshow |
| Fist | Exit slideshow |

Start slideshow uses `Ctrl+F5` in Google Slides, `F5` in PowerPoint and Impress, and the Mac equivalents on Mac.

### YouTube and VLC

| Gesture | Action |
| --- | --- |
| Open palm | Play / pause |
| 3 fingers | Forward 10 seconds |
| 2 fingers | Back 10 seconds |
| 1 finger (index only) | Volume up |
| Pinky only | Volume down |
| Rock sign (index + pinky) | Fullscreen |
| Fist | Mute / unmute |

Slides wait about 1.5 seconds between actions. Video modes wait about 0.6 seconds.

Some actions repeat while you hold the gesture: next / previous slide, seek forward and back, and volume. Toggle actions fire only once: start / exit slideshow, play / pause, mute / unmute and fullscreen. To use a toggle again, change to another gesture (or take your hand away) and show it again.

A gesture only counts after it is held steady for a few frames, so moving from one gesture to another will not trigger the ones in between.

## Setup

You need Python 3.9 or newer and a webcam.

1. Get the project:

   ```bash
   git clone <your-repository-url>
   cd <project-folder>
   ```

2. Install the libraries (use `python3` on Mac or Linux):

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Download the hand tracking model (one time only):

   ```bash
   python setup_models.py
   ```

## Running it

```bash
python main.py
```

1. Open your presentation or video.
2. Click that window once so it has keyboard focus.
3. Show a gesture to the camera.

Keys in the camera window: `q` to quit, `m` to switch app, `a` to turn auto-detect back on. `Ctrl+C` in the terminal also stops it.

For YouTube, click on the video first. If the cursor is in the search box, the keys would be typed as text.

## On-screen information

- Top line: the last action taken.
- Cyan line: the current app and whether it was picked automatically or manually.
- Yellow line: the detected finger pattern and how many steady frames have been counted.
- Bottom left: the gestures and actions for the current app.
- Red message: the camera window has focus. Click your app window, otherwise the keys go to the wrong place.

## Mac permissions

Open System Settings, go to Privacy & Security, and allow Accessibility and Input Monitoring for the app you run Python from (Terminal, VS Code or PyCharm).

## Troubleshooting

| Problem | Try this |
| --- | --- |
| "Model not found" | Run `python setup_models.py`. |
| Black camera window | Close other apps that use the camera. |
| Hand not detected | Palm to the camera, fingers up, about an arm's length away, good light. |
| Pattern is right but nothing happens | Click your app window so it has focus. |
| Wrong app shown | Press `m` to change it. |
| YouTube keys do nothing | Click the video, not the search box. |
| VLC seek or volume does nothing | Check the hotkeys in VLC under Tools, Preferences, Hotkeys. |

## Changing the code

Everything is in `main.py`.

- Each app is one entry in the `MODES` list: a name, words to find in the window title, the delay between actions, and a map from gesture to keys.
- To add an app, copy an entry and change those values.
- `STEADY_FRAMES` sets how long a gesture must be held.

## How it works

1. OpenCV reads and mirrors a webcam frame.
2. MediaPipe finds 21 points on the hand.
3. A finger counts as up when its tip is higher on screen than the joint below it.
4. If the same pattern holds long enough and the delay has passed, PyAutoGUI presses the key for that app.

Limits: fingers need to point upward, only one hand is tracked, and app detection is automatic on Windows only.

## Files

```
main.py            the gesture controller
setup_models.py    downloads the MediaPipe hand model
requirements.txt   Python libraries
models/            created by setup_models.py
```
