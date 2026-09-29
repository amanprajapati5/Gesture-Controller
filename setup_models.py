"""
Download required MediaPipe models
"""
import os
import urllib.request
import ssl

# Always create models/ next to this script, no matter where it is run from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

# Disable SSL verification for downloading
ssl._create_default_https_context = ssl._create_unverified_context

# Official MediaPipe model location
models = {
    "hand_landmarker": [
        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
    ]
}

for name, urls in models.items():
    model_path = os.path.join(MODELS_DIR, f"{name}.task")

    if os.path.exists(model_path):
        # The model is a binary file, so read it as bytes and check for an XML error page
        with open(model_path, 'rb') as f:
            head = f.read(200).lower()
        if b'<error' in head or b'<?xml' in head or os.path.getsize(model_path) < 100_000:
            print(f"✗ Model {name} is corrupted, re-downloading...")
            os.remove(model_path)
        else:
            print(f"✓ Model {name} already exists")
            continue

    downloaded = False
    for url in urls:
        print(f"Trying to download {name} from {url}...")
        try:
            urllib.request.urlretrieve(url, model_path)
            print(f"✓ Downloaded {name}")
            downloaded = True
            break
        except Exception as e:
            print(f"  Failed: {e}")

    if not downloaded:
        print(f"✗ Could not download {name} from any source")
