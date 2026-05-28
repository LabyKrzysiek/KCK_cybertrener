import cv2
import mediapipe as mp
import math
import time
import threading
import queue
import pythoncom 
import win32com.client 

speech_queue = queue.Queue()

def tts_worker():
    pythoncom.CoInitialize() 
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    while True:
        text = speech_queue.get()
        if text is None:
            break
        speaker.Speak(text)
        speech_queue.task_done()

threading.Thread(target=tts_worker, daemon=True).start()

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
cv2.namedWindow('cybertrener', cv2.WINDOW_NORMAL)
cv2.resizeWindow('cybertrener', 1280, 720)

counter = 0
stage = "KALIBRACJA"
feedback = "STAN PROSTO PRZED KAMERA" 
feedback_color = (0, 165, 255) 
bad_rep = False
calib_spoken = False 

calibration_counter = 0
calibration_limit = 60
calib_hip_angles = []
calib_knee_angles = []
calib_back_angles = [] 

lockout_hip_threshold = 160
lockout_knee_threshold = 160
safe_back_threshold = 140 

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
            mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2),
            mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
        )
        
        try:
            landmarks = results.pose_landmarks.landmark
            
            ear = [landmarks[mp_pose.PoseLandmark.LEFT_EAR.value].x, 
                   landmarks[mp_pose.PoseLandmark.LEFT_EAR.value].y]
            shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, 
                        landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, 
                   landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, 
                    landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, 
                     landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

            back_angle = calculate_angle(ear, shoulder, hip)
            hip_angle = calculate_angle(shoulder, hip, knee)
            knee_angle = calculate_angle(hip, knee, ankle)

            if stage == "KALIBRACJA":
                calibration_counter += 1
                calib_hip_angles.append(hip_angle)
                calib_knee_angles.append(knee_angle)
                calib_back_angles.append(back_angle)
                
                progress = int((calibration_counter / calibration_limit) * 100)
                feedback = f"KALIBRACJA [{progress}%]"
                feedback_color = (0, 165, 255)
                
                if calibration_counter >= calibration_limit:
                    user_max_hip = sum(calib_hip_angles) / len(calib_hip_angles)
                    user_max_knee = sum(calib_knee_angles) / len(calib_knee_angles)
                    user_max_back = sum(calib_back_angles) / len(calib_back_angles)
                    
                    lockout_hip_threshold = user_max_hip - 12
                    lockout_knee_threshold = user_max_knee - 12
                    safe_back_threshold = user_max_back - 12 
                    
                    stage = "BRAK"
                    feedback = "KALIBRACJA UKONCZONA! MOZNA ZACZAC"
                    feedback_color = (0, 255, 0)
                    
                    if not calib_spoken:
                        speech_queue.put("Kalibracja zakończona.")
                        calib_spoken = True
                        
                    time.sleep(1)

            else:
                if not bad_rep:
                    feedback = "Postawa OK"
                    feedback_color = (0, 255, 0)

                if hip_angle < 110 and knee_angle < 120:
                    stage = "STARTOWA"
                    bad_rep = False
                    
                elif stage == "STARTOWA" and (hip_angle >= 110 or knee_angle >= 120):
                    stage = "PODNOSZENIE"
                    
                elif hip_angle > lockout_hip_threshold and knee_angle > lockout_knee_threshold:
                    if stage == "PODNOSZENIE":
                        if not bad_rep: 
                            counter += 1
                    stage = "PELNY WYPROST"
                    
                elif stage == "PELNY WYPROST" and (hip_angle < lockout_hip_threshold or knee_angle < lockout_knee_threshold):
                    stage = "OPUSZCZANIE"

                if stage == "PODNOSZENIE" and not bad_rep:
                    
                    if back_angle < safe_back_threshold:
                        bad_rep = True
                        feedback = "BLAD: Koci grzbiet!"
                        feedback_color = (0, 0, 255)
                        speech_queue.put("Błąd! Zgarbione plecy.")
                        
                    elif knee_angle > 140 and hip_angle < 135:
                        bad_rep = True
                        feedback = "BLAD: Wyprostowane nogi!"
                        feedback_color = (0, 0, 255)
                        speech_queue.put("Błąd! Za szybko nogi.")

            back_pixel_pos = (int(shoulder[0] * w), int(shoulder[1] * h))
            hip_pixel_pos = (int(hip[0] * w), int(hip[1] * h))
            knee_pixel_pos = (int(knee[0] * w), int(knee[1] * h))
            
            cv2.putText(frame, str(int(back_angle)), back_pixel_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, str(int(hip_angle)), hip_pixel_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, str(int(knee_angle)), knee_pixel_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

        except Exception as e:
            pass

    cv2.rectangle(frame, (0, 0), (550, 150), (245, 117, 16), -1)
    
    cv2.putText(frame, 'POWT:', (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(frame, str(counter), (110, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)
    
    cv2.putText(frame, 'FAZA:', (15, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(frame, stage, (110, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)

    cv2.putText(frame, 'STATUS:', (15, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(frame, feedback, (110, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.9, feedback_color, 2, cv2.LINE_AA)

    cv2.imshow('cybertrener', frame)

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()