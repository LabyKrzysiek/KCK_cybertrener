from tts import speak
import config


class CyberTrainer:
    def __init__(self):
        self.counter = 0
        self.stage = "PRZYGOTOWANIE"
        self.feedback = "PRZYGOTUJ SIE..."
        self.feedback_color = config.COLOR_WARNING
        self.bad_rep = False

        self.welcome_spoken = False
        self.calib_spoken = False

        self.warned_back = False
        self.warned_legs = False

        self.back_error_frames = 0

        self.start_announced = False
        self.delay_counter = 0

        self.calibration_counter = 0
        self.calib_hip_angles = []
        self.calib_knee_angles = []
        self.calib_back_angles = []

        self.lockout_hip_threshold = config.DEFAULT_HIP_LOCKOUT
        self.lockout_knee_threshold = config.DEFAULT_KNEE_LOCKOUT
        self.safe_back_threshold = config.DEFAULT_BACK_SAFE

    def update(self, back_angle, hip_angle, knee_angle):
        if self.stage == "PRZYGOTOWANIE":
            if not self.welcome_spoken:
                speak("Przygotuj się do kalibracji. Stań prosto przed kamerą.")
                self.welcome_spoken = True

            self.delay_counter += 1

            delay_limit = getattr(config, 'CALIBRATION_DELAY_FRAMES', 90)
            remaining_seconds = int(3 - (self.delay_counter / (delay_limit / 3)))

            self.feedback = f"START ZA: {max(1, remaining_seconds)}s"

            if self.delay_counter >= delay_limit:
                self.stage = "KALIBRACJA"
                speak("Kalibracja. Stój nieruchomo.")
            return

        elif self.stage == "KALIBRACJA":
            self.calibration_counter += 1
            self.calib_hip_angles.append(hip_angle)
            self.calib_knee_angles.append(knee_angle)
            self.calib_back_angles.append(back_angle)

            progress = min(100, int((self.calibration_counter / config.CALIBRATION_FRAMES) * 100))
            self.feedback = f"KALIBRACJA [{progress}%]"
            self.feedback_color = config.COLOR_WARNING

            if self.calibration_counter >= config.CALIBRATION_FRAMES:
                try:
                    user_max_hip = sum(self.calib_hip_angles) / len(self.calib_hip_angles)
                    user_max_knee = sum(self.calib_knee_angles) / len(self.calib_knee_angles)
                    user_max_back = sum(self.calib_back_angles) / len(self.calib_back_angles)

                    self.lockout_hip_threshold = user_max_hip - getattr(config, 'CALIBRATION_MARGIN_DEGREES', 12)
                    self.lockout_knee_threshold = user_max_knee - getattr(config, 'CALIBRATION_MARGIN_DEGREES', 12)
                    self.safe_back_threshold = user_max_back - getattr(config, 'CALIBRATION_MARGIN_BACK_DEGREES', 12)

                    self.stage = "BRAK"
                    self.feedback = "KALIBRACJA UKONCZONA! MOZNA ZACZAC"
                    self.feedback_color = config.COLOR_SUCCESS

                    if not self.calib_spoken:
                        speak("Kalibracja zakończona sukcesem.")
                        self.calib_spoken = True
                except Exception as e:
                    print(f"Błąd obliczeń kalibracji: {e}")
                    self.stage = "BRAK"

        else:
            if not self.bad_rep:
                self.feedback = "Postawa OK"
                self.feedback_color = config.COLOR_SUCCESS

            if hip_angle < config.START_HIP_MAX and knee_angle < config.START_KNEE_MAX:
                if not self.start_announced:
                    speak("Pozycja startowa.")
                    self.start_announced = True

                self.stage = "STARTOWA"
                self.bad_rep = False
                self.warned_back = False
                self.warned_legs = False
                self.back_error_frames = 0

            elif self.stage == "STARTOWA" and (
                    hip_angle >= config.START_HIP_MAX + 5 or knee_angle >= config.START_KNEE_MAX + 5):
                self.stage = "PODNOSZENIE"

            elif hip_angle > self.lockout_hip_threshold and knee_angle > self.lockout_knee_threshold:
                if self.stage == "PODNOSZENIE":
                    if not self.bad_rep:
                        self.counter += 1
                        speak(str(self.counter))

                        if self.counter > 0 and self.counter % config.PRAISE_INTERVAL == 0:
                            speak("Świetna robota, tak trzymaj!")

                self.stage = "PELNY WYPROST"

            elif self.stage == "PELNY WYPROST" and (
                    hip_angle < self.lockout_hip_threshold or knee_angle < self.lockout_knee_threshold):
                self.stage = "OPUSZCZANIE"
                self.start_announced = False

            if self.stage == "PODNOSZENIE" and not self.bad_rep:

                if back_angle < self.safe_back_threshold:
                    self.back_error_frames += 1
                    if self.back_error_frames >= 2:
                        self.bad_rep = True
                        self.start_announced = False
                        self.feedback = "BLAD: Koci grzbiet!"
                        self.feedback_color = config.COLOR_ERROR

                        if not self.warned_back:
                            speak("Błąd! Zgarbione plecy.")
                            self.warned_back = True
                else:
                    self.back_error_frames = 0

                if knee_angle > config.ERROR_KNEE_MIN and hip_angle < config.ERROR_HIP_MAX:
                    self.bad_rep = True
                    self.start_announced = False
                    self.feedback = "BLAD: Wyprostowane nogi!"
                    self.feedback_color = config.COLOR_ERROR

                    if not self.warned_legs:
                        speak("Błąd! Zbyt wcześnie nogi.")
                        self.warned_legs = True