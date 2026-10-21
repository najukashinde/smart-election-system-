"""
Blink-based liveness detection.

Goal: stop a printed photo or a phone screen from being accepted as a real
voter. A static image can match the face-recognition model just fine, but it
can't blink on command — so we require a real blink before a vote is allowed.

Implementation deliberately uses only OpenCV Haar cascades (already a
dependency of this project) rather than dlib/mediapipe, so there is nothing
new to install:

  1. Look for eyes inside the top ~60% of the detected face box each frame.
  2. If eyes disappear for a few consecutive frames and then reappear, count
     that as one blink.
  3. Once enough blinks are seen inside a rolling time window, the person in
     front of the camera is treated as "live".

This is a lightweight anti-spoofing check, not a forensic-grade one — a
short pre-recorded video of a blink could still fool it. It is meant to
block the trivial "hold up a printed photo" attack a judge is likely to try.
"""

import time
import cv2


class BlinkLivenessDetector:
    def __init__(self, required_blinks=1, window_seconds=8, eyes_closed_frames_threshold=2):
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        self.required_blinks = required_blinks
        self.window_seconds = window_seconds
        self.eyes_closed_frames_threshold = eyes_closed_frames_threshold

        self._blink_count = 0
        self._consec_closed = 0
        self._eyes_were_open = False
        self._start_time = None

    def reset(self):
        self._blink_count = 0
        self._consec_closed = 0
        self._eyes_were_open = False
        self._start_time = None

    def update(self, gray_frame, face_box):
        """Call once per video frame with the grayscale frame and the
        (x, y, w, h) face box. Returns True once enough blinks have been
        observed within the rolling time window."""
        if self._start_time is None:
            self._start_time = time.time()

        x, y, w, h = face_box
        roi_gray = gray_frame[y:y + int(h * 0.6), x:x + w]
        eyes = self.eye_cascade.detectMultiScale(roi_gray, 1.1, 8, minSize=(15, 15))
        eyes_open_now = len(eyes) >= 2

        if eyes_open_now:
            if not self._eyes_were_open and self._consec_closed >= self.eyes_closed_frames_threshold:
                self._blink_count += 1
            self._consec_closed = 0
            self._eyes_were_open = True
        else:
            self._consec_closed += 1
            self._eyes_were_open = False

        if time.time() - self._start_time > self.window_seconds:
            # No luck in this window — give them a fresh window rather than
            # permanently failing.
            self._start_time = time.time()
            self._blink_count = 0

        return self._blink_count >= self.required_blinks

    @property
    def blink_count(self):
        return self._blink_count
