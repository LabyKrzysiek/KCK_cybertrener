import pythoncom
import win32com.client
import threading
import queue

speech_queue = queue.Queue()

def _tts_worker():
    pythoncom.CoInitialize()
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    while True:
        text = speech_queue.get()
        if text is None:
            break
        speaker.Speak(text)
        speech_queue.task_done()

def start_tts():
    threading.Thread(target=_tts_worker, daemon=True).start()

def speak(text):
    speech_queue.put(text)