from tts import speak


class CyberTrainer:
    def __init__(self):
        self.counter = 0
        self.stage = "KALIBRACJA"
        self.feedback = "STAN PROSTO PRZED KAMERA"
        self.feedback_color = (0, 165, 255)
        self.bad_rep = False

        self.welcome_spoken = False
        self.calib_spoken = False

        self.warned_back = False
        self.warned_legs = False

        self.calibration_counter = 0
        self.calibration_limit = 60
        self.calib_hip_angles = []
        self.calib_knee_angles = []
        self.calib_back_angles = []

        self.lockout_hip_threshold = 160
        self.lockout_knee_threshold = 160
        self.safe_back_threshold = 140

    def update(self, back_angle, hip_angle, knee_angle):
        if self.stage == "KALIBRACJA":
            if not self.welcome_spoken:
                speak("Rozpoczynam kalibrację. Stań prosto przodem do kamery i poczekaj.")
                self.welcome_spoken = True

            self.calibration_counter += 1
            self.calib_hip_angles.append(hip_angle)
            self.calib_knee_angles.append(knee_angle)
            self.calib_back_angles.append(back_angle)

            progress = int((self.calibration_counter / self.calibration_limit) * 100)
            self.feedback = f"KALIBRACJA [{progress}%]"
            self.feedback_color = (0, 165, 255)

            if self.calibration_counter >= self.calibration_limit:
                user_max_hip = sum(self.calib_hip_angles) / len(self.calib_hip_angles)
                user_max_knee = sum(self.calib_knee_angles) / len(self.calib_knee_angles)
                user_max_back = sum(self.calib_back_angles) / len(self.calib_back_angles)

                self.lockout_hip_threshold = user_max_hip - 12
                self.lockout_knee_threshold = user_max_knee - 12
                self.safe_back_threshold = user_max_back - 12

                self.stage = "BRAK"
                self.feedback = "KALIBRACJA UKONCZONA! MOZNA ZACZAC"
                self.feedback_color = (0, 255, 0)

                if not self.calib_spoken:
                    speak("Kalibracja zakończona sukcesem. Możesz zacząć ćwiczyć.")
                    self.calib_spoken = True

        else:
            if not self.bad_rep:
                self.feedback = "Postawa OK"
                self.feedback_color = (0, 255, 0)


            if hip_angle < 110 and knee_angle < 120:
                self.stage = "STARTOWA"
                self.bad_rep = False
                self.warned_back = False
                self.warned_legs = False
            # ------------------------

            elif self.stage == "STARTOWA" and (hip_angle >= 110 or knee_angle >= 120):
                self.stage = "PODNOSZENIE"

            elif hip_angle > self.lockout_hip_threshold and knee_angle > self.lockout_knee_threshold:
                if self.stage == "PODNOSZENIE":
                    if not self.bad_rep:
                        self.counter += 1
                        speak(str(self.counter))

                        if self.counter > 0 and self.counter % 5 == 0:
                            speak("Świetna robota, tak trzymaj!")

                self.stage = "PELNY WYPROST"

            elif self.stage == "PELNY WYPROST" and (
                    hip_angle < self.lockout_hip_threshold or knee_angle < self.lockout_knee_threshold):
                self.stage = "OPUSZCZANIE"

            if self.stage == "PODNOSZENIE" and not self.bad_rep:
                if back_angle < self.safe_back_threshold:
                    self.bad_rep = True
                    self.feedback = "BLAD: Koci grzbiet!"
                    self.feedback_color = (0, 0, 255)

                    if not self.warned_back:
                        speak("Błąd! Zgarbione plecy. Ściągnij łopatki i wypnij klatkę piersiową.")
                        self.warned_back = True

                elif knee_angle > 140 and hip_angle < 135:
                    self.bad_rep = True
                    self.feedback = "BLAD: Wyprostowane nogi!"
                    self.feedback_color = (0, 0, 255)

                    if not self.warned_legs:
                        speak("Błąd! Zbyt wcześnie prostujesz nogi. Używaj bioder!")
                        self.warned_legs = True