import mediapipe as mp
import cv2
import numpy as np
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL

# Volume setup (Windows only)
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
vol_min, vol_max = volume_interface.GetVolumeRange()[:2]  # usually -65.25 to 0.0

# Initialize webcam
cap = cv2.VideoCapture(0)

# MediaPipe drawing and holistic setup
mp_drawing = mp.solutions.drawing_utils
mp_holistic = mp.solutions.holistic

# STORE STARTING LENGTH
st_len = 0
#Volume Fixer
volume=0
dist = 0
dist_l = 0
# Start MediaPipe Holistic
with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
    while True:
        # Read frame from webcam
        res, frame = cap.read()
        frame = cv2.flip(frame, 1)
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = holistic.process(img)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        # Draw hand landmarks
        mp_drawing.draw_landmarks(frame, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
        mp_drawing.draw_landmarks(frame, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS)

        # Coordinate placeholders
        cx_index, cy_index, cx_index_l, cy_index_l = 0,0,0,0
        cx_middle, cy_middle, cx_middle_l, cy_middle_l = 0,0,0,0

        # Right hand
        if results.right_hand_landmarks:
            h, w, c = img.shape
            index_tip = results.right_hand_landmarks.landmark[8]
            middle_tip = results.right_hand_landmarks.landmark[12]
            cx_index, cy_index = int(index_tip.x * w), int(index_tip.y * h)
            cx_middle, cy_middle = int(middle_tip.x * w), int(middle_tip.y * h)
            cv2.circle(frame, (cx_index, cy_index), 10, (255, 0, 0), cv2.FILLED)
            cv2.putText(frame, f"Index: ({cx_index}, {cy_index})", (cx_index + 15, cy_index - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            cv2.circle(frame, (cx_middle, cy_middle), 10, (0, 255, 0), cv2.FILLED)
            cv2.putText(frame, f"Middle: ({cx_middle}, {cy_middle})", (cx_middle + 15, cy_middle - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Left hand
        if results.left_hand_landmarks:
            h, w, c = img.shape
            index_tip = results.left_hand_landmarks.landmark[8]
            middle_tip = results.left_hand_landmarks.landmark[12]
            cx_index_l, cy_index_l = int(index_tip.x * w), int(index_tip.y * h)
            cx_middle_l, cy_middle_l = int(middle_tip.x * w), int(middle_tip.y * h)
            cv2.circle(frame, (cx_index_l, cy_index_l), 10, (255, 105, 180), cv2.FILLED)
            cv2.putText(frame, f"L Index: ({cx_index_l}, {cy_index_l})", (cx_index_l + 15, cy_index_l - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 105, 180), 2)
            cv2.circle(frame, (cx_middle_l, cy_middle_l), 10, (144, 238, 144), cv2.FILLED)
            cv2.putText(frame, f"L Middle: ({cx_middle_l}, {cy_middle_l})", (cx_middle_l + 15, cy_middle_l - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (144, 238, 144), 2)
            # Finger distances
            dist = (((cx_middle - cx_index) ** 2) + ((cy_middle - cy_index) ** 2)) ** 0.5
            dist_l = (((cx_middle_l - cx_index_l) ** 2) + ((cy_middle_l - cy_index_l) ** 2)) ** 0.5
        

        

        if dist <= 20 and dist_l <= 20:
            
            line_dist = (((cx_index_l - cx_index) ** 2) + ((cy_index_l - cy_index) ** 2)) ** 0.5
            if st_len == 0:
                st_len = line_dist

            increase = int(line_dist - st_len)

            # Volume control
            volume_level = volume=np.interp(line_dist, [st_len, st_len + 150], [vol_min, vol_max])
            volume_interface.SetMasterVolumeLevel(volume_level, None)

            # Visuals
            cv2.line(frame, (cx_index, cy_index), (cx_index_l, cy_index_l), (0, 0, 255), 5)
            cv2.putText(frame, f"line length: {int(line_dist)} pixels", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, f"Increase: {increase} px", (50, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # Volume bar
            bar_pos = int(np.interp(line_dist, [st_len, st_len + 150], [400, 150]))
            volume_percent = int(np.interp(line_dist, [st_len, st_len + 150], [0, 100]))
            cv2.rectangle(frame, (50, 150), (85, 400), (0, 255, 0), 2)
            cv2.rectangle(frame, (50, bar_pos), (85, 400), (0, 255, 0), cv2.FILLED)
            cv2.putText(frame, f'{volume_percent} %', (40, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            volume_interface.SetMasterVolumeLevel(volume, None)
            st_len = 0
            cv2.putText(frame, f"line length: 0 pixels", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, f"Increase: 0 px", (50, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Show the webcam feed
        frame = cv2.resize(frame, (1520, 750))
        cv2.imshow("WEB CAM", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Cleanup
cap.release()
cv2.destroyAllWindows()
print(mp_holistic.HAND_CONNECTIONS)
