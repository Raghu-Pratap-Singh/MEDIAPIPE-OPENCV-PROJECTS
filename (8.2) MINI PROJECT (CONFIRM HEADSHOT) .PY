import cv2

# Load the pre-trained Haar Cascade classifier for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Open the default camera (0 refers to the default webcam)
cap = cv2.VideoCapture(0)

# Infinite loop to continuously get frames from the webcam
while True:
    
    # Read a frame from the camera
    res, frame = cap.read()

    # Convert the frame to grayscale (required for face detection)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces in the grayscale frame
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)

    stat = False
    # If faces are detected, draw shapes and labels
    for (x, y, w, h) in faces:
        # We enter this loop only if a face is detected
        stat = True

        # Calculate the midpoint of the detected face rectangle
        xmid = ((2*x + w) // 2)
        ymid = ((2*y + h) // 2)

        # Draw a red circle centered slightly above the face
        cv2.circle(frame, (xmid, (ymid - 50)), 20, (0, 0, 255), thickness=2)

        # Draw a red crosshair marker
        # Horizontal line
        cv2.line(frame, ((xmid - 870), (ymid - 50)), ((xmid + 870), (ymid - 50)), (0, 0, 255), thickness=2)

        # Vertical line
        cv2.line(frame, (xmid, (ymid - 820)), (xmid, (ymid + 820)), (0, 0, 255), thickness=2)

        # Green center dot
        cv2.circle(frame, (xmid, (ymid - 50)), 5, (0, 255, 0), thickness=-1)

        # Display a "LOCKED" label below the crosshair
        cv2.putText(frame, 
                    f"LOCKED :({xmid},{ymid})",               # Text to display
                    ((xmid - 100), (ymid + 100)),  # Position of the text
                    cv2.FONT_HERSHEY_DUPLEX,       # Font style
                    1,                             # Font size
                    (0, 0, 255))                   # Text color (red)


    # Resize frame for display
    frame = cv2.resize(frame, (1100, 800))

    # Draw a green rectangle as background for status text
    cv2.rectangle(frame, (90, 40), (600, 110), (0, 255, 0), thickness=-1)
    
    # Display the status message depending on whether a face was found
    if stat:
        cv2.putText(frame, 
                    "TARGET FOUND..", 
                    (100, 100), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    2, 
                    (0, 0, 255), 
                    thickness=3)
    else:
        cv2.putText(frame, 
                    "TARGET LOST..", 
                    (100, 100), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    2, 
                    (0, 0, 255), 
                    thickness=3)

    # Show the processed frame in a window
    cv2.imshow("FACE DETECTION", frame)

    # Exit the loop and release the camera if 'q' is pressed
    if cv2.waitKey(1) & 0xff == ord('q'):
        cap.release()  # Release the camera
        break

# Close all OpenCV windows
cv2.destroyAllWindows()
