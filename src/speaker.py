import pyttsx3
import threading

class Speaker:
    def __init__(self):
        pass

    def speak(self, text):
        """
        Speak text using a fresh engine instance per call.
        This enables robustness against pyttsx3 event loop issues on Windows
        where reusing the loop often fails after the first run.
        """
        threading.Thread(target=self._speak_thread, args=(text,), daemon=True).start()

    def _speak_thread(self, text):
        try:
            # Initialize a fresh engine for this specific utterance
            # This ensures no state pollution or event loop conflicts
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.say(text)
            engine.runAndWait()
            # Engine cleans up when function exits and object is garbage collected
        except Exception as e:
            print(f"TTS Error: {e}")

    def stop(self):
        pass
