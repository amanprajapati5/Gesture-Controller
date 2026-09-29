import ctypes
import os
import platform
import time

import cv2
import mediapipe as mp
import pyautogui
from mediapipe.tasks.python import vision

WINDOW = "Gesture Controller"
IS_MAC = platform.system() == "Darwin"
IS_WIN = platform.system() == "Windows"

# Finger patterns are (index, middle, ring, pinky), 1 = finger is up.
OPEN, THREE, TWO, ONE, PINKY, ROCK, FIST = (
    (1, 1, 1, 1), (1, 1, 1, 0), (1, 1, 0, 0), (1, 0, 0, 0), (0, 0, 0, 1), (1, 0, 0, 1), (0, 0, 0, 0))
NAMES = {OPEN: "Open palm", THREE: "3 fingers", TWO: "2 fingers", ONE: "1 finger",
         PINKY: "Pinky", ROCK: "Rock sign", FIST: "Fist"}

# HOLD: keeps repeating while you hold the gesture (seeking, volume, next slide).
# ONCE: fires one time, then you must change gesture to use it again (play/pause, mute, fullscreen).
HOLD, ONCE = True, False


def slides(start):
    """Same keys in every slide app, only the 'start' shortcut changes."""
    return {
        OPEN: ("Next slide", ("right",), HOLD),
        THREE: ("Previous slide", ("left",), HOLD),
        TWO: ("Start slideshow", start, ONCE),
        FIST: ("Exit slideshow", ("esc",), ONCE),
    }


# Each mode: window-title words to look for, seconds between actions, and gesture -> (label, keys, repeat).
MODES = [
    {"name": "Google Slides", "match": ["google slides"], "delay": 1.5,
     "gestures": slides(("command", "enter") if IS_MAC else ("ctrl", "f5"))},
    {"name": "PowerPoint", "match": ["powerpoint"], "delay": 1.5,
     "gestures": slides(("command", "shift", "return") if IS_MAC else ("f5",))},
    {"name": "LibreOffice Impress", "match": ["impress"], "delay": 1.5,
     "gestures": slides(("f5",))},
    {"name": "YouTube", "match": ["youtube"], "delay": 0.6,
     "gestures": {
         OPEN: ("Play / Pause", ("k",), ONCE),
         THREE: ("Forward 10s", ("l",), HOLD),
         TWO: ("Back 10s", ("j",), HOLD),
         ONE: ("Volume up", ("up",), HOLD),
         PINKY: ("Volume down", ("down",), HOLD),
         ROCK: ("Fullscreen", ("f",), ONCE),
         FIST: ("Mute / Unmute", ("m",), ONCE),
     }},
    {"name": "VLC", "match": ["vlc"], "delay": 0.6,
     "gestures": {
         OPEN: ("Play / Pause", ("space",), ONCE),
         THREE: ("Forward 10s", ("alt", "right"), HOLD),
         TWO: ("Back 10s", ("alt", "left"), HOLD),
         ONE: ("Volume up", ("ctrl", "up"), HOLD),
         PINKY: ("Volume down", ("ctrl", "down"), HOLD),
         ROCK: ("Fullscreen", ("f",), ONCE),
         FIST: ("Mute / Unmute", ("m",), ONCE),
     }},
    {"name": "Other slides / PDF", "match": [], "delay": 1.5,
     "gestures": slides(("f5",))},
]

LINES = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8), (5, 9), (9, 10), (10, 11),
         (11, 12), (9, 13), (13, 14), (14, 15), (15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)]

STEADY_FRAMES = 6   # a gesture must last this many frames before it counts


def active_window_title():
    """Title of the window in front (Windows only)."""
    if not IS_WIN:
        return ""
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    buf = ctypes.create_unicode_buffer(user32.GetWindowTextLengthW(hwnd) + 1)
    user32.GetWindowTextW(hwnd, buf, len(buf))
    return buf.value


def fingers_up(hand):
    """A finger is up when its tip is higher on screen than the joint below it."""
    tips, joints = [8, 12, 16, 20], [6, 10, 14, 18]
    return tuple(int(hand[t].y < hand[j].y) for t, j in zip(tips, joints))


def put(frame, text, y, color=(0, 255, 0), size=0.7):
    cv2.putText(frame, text, (20, y), cv2.FONT_HERSHEY_SIMPLEX, size, color, 2)


# --- setup ---------------------------------------------------------------
model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "hand_landmarker.task")
if not os.path.exists(model_path):
    exit("Model not found. Run: python setup_models.py")

detector = vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
    num_hands=1,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5,
))
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if IS_WIN else cv2.VideoCapture(0)

mode = MODES[0]
auto = True                 # pick the mode from the window in front
title, last_title_check = "", 0
pattern, steady = None, 0
used = None                 # last ONCE gesture that fired, blocked until you change gesture
missing = 0                 # frames without a hand
last_fire = 0
message, message_until = "", 0

print("In the camera window:  q = quit   m = next app   a = auto-detect app")

try:
    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break
        now = time.time()

        # Look at the window in front a few times a second and switch mode to match it.
        if IS_WIN and now - last_title_check > 0.3:
            title, last_title_check = active_window_title(), now
            if auto:
                for m in MODES:
                    if any(word in title.lower() for word in m["match"]):
                        mode = m
                        break
        in_preview = IS_WIN and title == WINDOW   # keys would go to this window, not your app

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))

        if result.hand_landmarks:
            missing = 0
            hand = result.hand_landmarks[0]
            points = [(int(p.x * w), int(p.y * h)) for p in hand]
            for a, b in LINES:
                cv2.line(frame, points[a], points[b], (0, 255, 0), 1)
            for p in points:
                cv2.circle(frame, p, 3, (0, 255, 0), -1)

            new = fingers_up(hand)
            steady = steady + 1 if new == pattern else 1
            pattern = new
            if steady >= STEADY_FRAMES and pattern != used:
                used = None     # a different gesture is steady, so the last ONCE gesture is free again

            action = mode["gestures"].get(pattern)
            ready = steady >= STEADY_FRAMES and now - last_fire > mode["delay"] and not in_preview
            if action and ready and (action[2] == HOLD or pattern != used):
                pyautogui.hotkey(*action[1])
                message, message_until, last_fire = action[0], now + 1, now
                if action[2] == ONCE:
                    used = pattern
        else:
            pattern, steady = None, 0
            missing += 1
            if missing > 15:    # hand really left the picture, not just a missed frame
                used = None

        # On-screen info
        put(frame, message if now < message_until else "Waiting...", 40, size=1)
        put(frame, f"App: {mode['name']} ({'auto' if auto and IS_WIN else 'manual'})", 75, (255, 255, 0))
        put(frame, f"{pattern}  {steady}/{STEADY_FRAMES}", 105, (0, 255, 255), 0.6)
        if in_preview:
            put(frame, "Click your app window to start", 135, (0, 0, 255))
        y = h - 15 - 24 * (len(mode["gestures"]) - 1)
        for g, (label, _, _) in mode["gestures"].items():
            put(frame, f"{NAMES[g]}: {label}", y, (255, 255, 255), 0.55)
            y += 24

        cv2.imshow(WINDOW, frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("m"):
            auto = False
            mode = MODES[(MODES.index(mode) + 1) % len(MODES)]
        if key == ord("a"):
            auto = True

except KeyboardInterrupt:
    pass
finally:
    cap.release()
    cv2.destroyAllWindows()
