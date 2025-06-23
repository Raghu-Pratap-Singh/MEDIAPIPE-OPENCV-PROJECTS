import mediapipe as mp
import cv2
import numpy as np
from pyfirmata import Arduino, util
import time

# -------------------------------------
# Arduino USB connection setup
board = Arduino('COM7')

# Define motor 1 control pins
in1 = board.get_pin('d:4:o')  # Digital pin 4 as output
in2 = board.get_pin('d:7:o')  # Digital pin 7 as output
pwm_pin = board.get_pin('d:9:p')  # PWM output pin

# Define motor 2 control pins and PWM
in3 = board.get_pin('d:2:o')  # Digital pin 2 as output
in4 = board.get_pin('d:8:o')  # Digital pin 8 as output
pwm_pin2 = board.get_pin('d:11:p')  # PWM pin for motor 2 speed control

# Motor 2 fixed at 50% speed and one direction
in3.write(1)
in4.write(0)
pwm_pin2.write(0.5)

time.sleep(1)  # Allow Arduino time to initialize

# Initialize webcam
cap = cv2.VideoCapture(1)

# Setup MediaPipe Holistic model and drawing utilities
mp_drawing = mp.solutions.drawing_utils
mp_holistic = mp.solutions.holistic

# Initialize tracking variables
st_len = 0
stopspeed = 0
switch_case=0

with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
    while True:
        res, frame = cap.read()
        frame = cv2.flip(frame, 1)
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = holistic.process(img)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        # Draw landmarks
        mp_drawing.draw_landmarks(frame, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
        mp_drawing.draw_landmarks(frame, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS)

        # Get dimensions and initialize fingertip coordinates
        h, w, _ = img.shape
        cx_index = cy_index = cx_index_l = cy_index_l = 0
        cx_middle = cy_middle = cx_middle_l = cy_middle_l = 0

        # Right hand fingertips
        if results.right_hand_landmarks:
            index_tip = results.right_hand_landmarks.landmark[8]
            middle_tip = results.right_hand_landmarks.landmark[12]
            cx_index, cy_index = int(index_tip.x * w), int(index_tip.y * h)
            cx_middle, cy_middle = int(middle_tip.x * w), int(middle_tip.y * h)
            cv2.circle(frame, (cx_index, cy_index), 10, (255, 0, 0), cv2.FILLED)
            cv2.circle(frame, (cx_middle, cy_middle), 10, (0, 255, 0), cv2.FILLED)

        # Left hand fingertips
        if results.left_hand_landmarks:
            index_tip = results.left_hand_landmarks.landmark[8]
            middle_tip = results.left_hand_landmarks.landmark[12]
            cx_index_l, cy_index_l = int(index_tip.x * w), int(index_tip.y * h)
            cx_middle_l, cy_middle_l = int(middle_tip.x * w), int(middle_tip.y * h)
            cv2.circle(frame, (cx_index_l, cy_index_l), 10, (255, 105, 180), cv2.FILLED)
            cv2.circle(frame, (cx_middle_l, cy_middle_l), 10, (144, 238, 144), cv2.FILLED)

        # Calculate distances (pinch detection)
        dist = (((cx_middle - cx_index) ** 2) + ((cy_middle - cy_index) ** 2)) ** 0.5
        dist_l = (((cx_middle_l - cx_index_l) ** 2) + ((cy_middle_l - cy_index_l) ** 2)) ** 0.5

        if dist <= 20 and dist_l <= 20:
            line_dist = (((cx_index_l - cx_index) ** 2) + ((cy_index_l - cy_index) ** 2)) ** 0.5

            if st_len == 0:
                st_len = line_dist

            increase = int(line_dist - st_len)
            pwm_value = np.interp(abs(increase), [0, 150], [0, 1])
            pwm_value = max(0, min(1, pwm_value))
            stopspeed = pwm_value

            if increase>=0:
                in1.write(1)
                in2.write(0)
                switch_case=0
            else:
                in1.write(0)
                in2.write(1)
                switch_case=1
            pwm_pin.write(pwm_value)

            cv2.line(frame, (cx_index, cy_index), (cx_index_l, cy_index_l), (0, 0, 255), 5)
            cv2.putText(frame, f"line length: {int(line_dist)} pixels", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, f"Increase: {increase} px", (50, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            st_len = 0
            # Maintain previous speed and direction
            if switch_case==0:
                in1.write(1)
                in2.write(0)
            else:
                in1.write(0)
                in2.write(1)
            pwm_pin.write(stopspeed)

            cv2.putText(frame, f"line length: 0 pixels", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, f"Increase: 0 px", (50, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        frame = cv2.resize(frame, (1300, 800))
        cv2.imshow("WEB CAM", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Cleanup
cap.release()
cv2.destroyAllWindows()
in3.write(0)
in4.write(0)
board.exit()
print(mp_holistic.HAND_CONNECTIONS)
