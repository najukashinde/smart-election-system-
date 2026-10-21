import os
import sys
import csv
import time
import pickle
import cv2
from datetime import datetime
from sklearn.neighbors import KNeighborsClassifier

sys.path.append(os.path.dirname(__file__))
from liveness import BlinkLivenessDetector  # noqa: E402
from ledger import append_vote  # noqa: E402
from candidates import load_candidates  # noqa: E402

# Cross-platform, offline text-to-speech. Falls back to printing if pyttsx3 /
# a speech engine isn't available (e.g. no audio device on the demo machine),
# instead of hard-failing like the original win32com-only version.
try:
    import pyttsx3
    _engine = pyttsx3.init()

    def speak(text):
        _engine.say(text)
        _engine.runAndWait()
except Exception:
    def speak(text):
        print(f"[VOICE] {text}")


BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
DATA_DIR = os.path.join(BASE_DIR, 'data')
VOTES_CSV = os.path.join(BASE_DIR, 'Votes.csv')
BACKGROUND_PATH = os.path.join(BASE_DIR, 'background.png')


def load_model():
    with open(os.path.join(DATA_DIR, 'names.pkl'), 'rb') as f:
        labels = pickle.load(f)
    with open(os.path.join(DATA_DIR, 'faces_data.pkl'), 'rb') as f:
        faces = pickle.load(f)
    knn = KNeighborsClassifier(n_neighbors=5)
    knn.fit(faces, labels)
    return knn


def check_if_voted(name):
    if not os.path.isfile(VOTES_CSV):
        return False
    with open(VOTES_CSV, 'r', newline='') as f:
        for row in csv.reader(f):
            if row and row[0] == name:
                return True
    return False


def main():
    candidates = load_candidates()
    knn = load_model()
    facedetect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    liveness = BlinkLivenessDetector(required_blinks=1, window_seconds=8)

    img_background = cv2.imread(BACKGROUND_PATH) if os.path.isfile(BACKGROUND_PATH) else None

    video = cv2.VideoCapture(0)

    print("Look at the camera and blink naturally to verify liveness, then press your candidate number.")
    for key, c in candidates.items():
        print(f"  [{key}] {c['name']} ({c['party']})")
    print("  [q] quit")

    voted_this_session = False

    while True:
        ret, frame = video.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = facedetect.detectMultiScale(gray, 1.3, 5)

        output = None
        is_live = False

        for (x, y, w, h) in faces:
            crop_img = frame[y:y + h, x:x + w]
            resized_img = cv2.resize(crop_img, (50, 50)).flatten().reshape(1, -1)
            output = knn.predict(resized_img)

            is_live = liveness.update(gray, (x, y, w, h))

            color = (0, 200, 0) if is_live else (0, 0, 255)
            label = f"{output[0]} LIVE" if is_live else f"{output[0]} blink to verify ({liveness.blink_count})"
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.rectangle(frame, (x, y - 40), (x + w, y), color, -1)
            cv2.putText(frame, label, (x, y - 15), cv2.FONT_HERSHEY_COMPLEX, 0.6, (255, 255, 255), 1)
            break  # only handle the first detected face

        display = frame
        if img_background is not None:
            display = img_background.copy()
            try:
                display[370:370 + 480, 225:225 + 640] = frame
            except ValueError:
                display = frame  # background.png dimensions don't match; fall back to raw feed

        cv2.imshow('Smart Election System', display)
        k = cv2.waitKey(1)

        if output is not None and not voted_this_session:
            name = str(output[0])

            if check_if_voted(name):
                speak("You have already voted.")
                print(f"{name} has already voted.")
                break

            if not is_live:
                if k != -1 and chr(k & 0xFF) in candidates:
                    print("Liveness not confirmed yet — please blink before voting.")
                continue

            for key, cand in candidates.items():
                if k == ord(key):
                    ts = time.time()
                    date = datetime.fromtimestamp(ts).strftime("%d-%m-%Y")
                    timestamp = datetime.fromtimestamp(ts).strftime("%H:%M:%S")

                    row_hash = append_vote(VOTES_CSV, name, cand['party'], date, timestamp)

                    speak("Your vote has been recorded. Thank you for participating in the elections.")
                    print(f"Vote recorded for {name} -> {cand['party']}. Ledger hash: {row_hash[:12]}...")
                    voted_this_session = True
                    time.sleep(2)
                    break

        if voted_this_session or k == ord('q'):
            break

    video.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
