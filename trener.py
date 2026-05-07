import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)


cap = cv2.VideoCapture(0)

print("Kamera uruchomiona. Wciśnij 'q', aby zamknąć okno.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Nie można pobrać obrazu z kamery.")
        break

    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    results = pose.process(image_rgb)

    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            frame, 
            results.pose_landmarks, 
            mp_pose.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2), # Kolor punktów
            mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)  # Kolor linii
        )
        
        landmarks = results.pose_landmarks.landmark
        
        left_elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value]
        
        print(f"Lewy łokieć - X: {left_elbow.x:.2f}, Y: {left_elbow.y:.2f}, Z: {left_elbow.z:.2f}")

    cv2.imshow('Personal Trainer - PoC Pose Detection', frame)

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
