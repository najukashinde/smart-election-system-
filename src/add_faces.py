import os
import cv2
import pickle
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

video = cv2.VideoCapture(0)
facedetect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
faces_data = []

i = 0
name = input("Enter your Aadhar number: ")
frames_total = 51
capture_after_frame = 2

while True:
    ret, frame = video.read()
    if not ret:
        break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = facedetect.detectMultiScale(gray, 1.3, 5)
    for (x, y, w, h) in faces:
        crop_img = frame[y:y + h, x:x + w]
        resized_img = cv2.resize(crop_img, (50, 50))
        if len(faces_data) <= frames_total and i % capture_after_frame == 0:
            faces_data.append(resized_img)
        i += 1
        cv2.putText(frame, str(len(faces_data)), (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 255), 1)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (50, 50, 255), 1)

    cv2.imshow('Register Face — press q to stop early', frame)
    k = cv2.waitKey(1)
    if k == ord('q') or len(faces_data) >= frames_total:
        break

video.release()
cv2.destroyAllWindows()

faces_data = np.asarray(faces_data)
faces_data = faces_data.reshape((frames_total, -1))

names_path = os.path.join(DATA_DIR, 'names.pkl')
faces_path = os.path.join(DATA_DIR, 'faces_data.pkl')

if not os.path.exists(names_path):
    names = [name] * frames_total
    with open(names_path, 'wb') as f:
        pickle.dump(names, f)
else:
    with open(names_path, 'rb') as f:
        names = pickle.load(f)
    names = names + [name] * frames_total
    with open(names_path, 'wb') as f:
        pickle.dump(names, f)

if not os.path.exists(faces_path):
    with open(faces_path, 'wb') as f:
        pickle.dump(faces_data, f)
else:
    with open(faces_path, 'rb') as f:
        faces = pickle.load(f)
    faces = np.append(faces, faces_data, axis=0)
    with open(faces_path, 'wb') as f:
        pickle.dump(faces, f)

print(f"Registered {frames_total} face samples for {name}.")
