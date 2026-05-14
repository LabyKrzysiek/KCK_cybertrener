import cv2
import mediapipe as mp
import math

def calculate_angle(a, b, c):
    radians = math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
    angle = abs(radians * 180.0 / math.pi)
    
    if angle > 180.0:
        angle = 360 - angle
        
    return angle

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0)
print("Kamera uruchomiona. Wciśnij 'q', aby zamknąć okno.")

counter = 0
stage = "BRAK"

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Nie można pobrać obrazu z kamery.")
        break

    h, w, _ = frame.shape
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)

    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2),
            mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
        )
        
        try:
            landmarks = results.pose_landmarks.landmark
            
            shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, 
                        landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, 
                   landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, 
                    landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, 
                     landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

            hip_angle = calculate_angle(shoulder, hip, knee)
            knee_angle = calculate_angle(hip, knee, ankle)

            if hip_angle < 110 and knee_angle < 120:
                stage = "STARTOWA"
                
            elif stage == "STARTOWA" and (hip_angle >= 110 or knee_angle >= 120):
                stage = "PODNOSZENIE"
                
            elif hip_angle > 160 and knee_angle > 160:
                if stage == "PODNOSZENIE":
                    counter += 1
                stage = "PELNY WYPROST"
                
            elif stage == "PELNY WYPROST" and (hip_angle < 160 or knee_angle < 160):
                stage = "OPUSZCZANIE"

            hip_pixel_pos = (int(hip[0] * w), int(hip[1] * h))
            knee_pixel_pos = (int(knee[0] * w), int(knee[1] * h))

            cv2.putText(frame, str(int(hip_angle)), hip_pixel_pos, 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, str(int(knee_angle)), knee_pixel_pos, 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        except Exception as e:
            pass

    cv2.rectangle(frame, (0, 0), (320, 110), (245, 117, 16), -1)
    
    cv2.putText(frame, 'POWT:', (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(frame, str(counter), (110, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)
    
    cv2.putText(frame, 'FAZA:', (15, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(frame, stage, (110, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)

    cv2.imshow('cybertrener', frame)

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()