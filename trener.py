import cv2
import mediapipe as mp
from tts import start_tts
from utils import calculate_angle
from logic import CyberTrainer

start_tts()

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

trainer = CyberTrainer()

cap = cv2.VideoCapture(0)
cv2.namedWindow('cybertrener', cv2.WINDOW_NORMAL)
cv2.resizeWindow('cybertrener', 1280, 720)

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    h, w, _ = frame.shape
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)

    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
            mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
        )

        try:
            landmarks = results.pose_landmarks.landmark

            ear = [landmarks[mp_pose.PoseLandmark.LEFT_EAR.value].x, landmarks[mp_pose.PoseLandmark.LEFT_EAR.value].y]
            shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                        landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                    landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                     landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

            back_angle = calculate_angle(ear, shoulder, hip)
            hip_angle = calculate_angle(shoulder, hip, knee)
            knee_angle = calculate_angle(hip, knee, ankle)

            trainer.update(back_angle, hip_angle, knee_angle)

            back_pixel_pos = (int(shoulder[0] * w), int(shoulder[1] * h))
            hip_pixel_pos = (int(hip[0] * w), int(hip[1] * h))
            knee_pixel_pos = (int(knee[0] * w), int(knee[1] * h))

            cv2.putText(frame, str(int(back_angle)), back_pixel_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2,
                        cv2.LINE_AA)
            cv2.putText(frame, str(int(hip_angle)), hip_pixel_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2,
                        cv2.LINE_AA)
            cv2.putText(frame, str(int(knee_angle)), knee_pixel_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2,
                        cv2.LINE_AA)

        except Exception as e:
            pass

    cv2.rectangle(frame, (0, 0), (550, 150), (245, 117, 16), -1)

    cv2.putText(frame, 'POWT:', (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(frame, str(trainer.counter), (110, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)

    cv2.putText(frame, 'FAZA:', (15, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(frame, trainer.stage, (110, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)

    cv2.putText(frame, 'STATUS:', (15, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(frame, trainer.feedback, (110, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.9, trainer.feedback_color, 2,
                cv2.LINE_AA)

    cv2.imshow('cybertrener', frame)

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()