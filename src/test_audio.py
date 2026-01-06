import sounddevice as sd
import numpy as np
import time

def test_mic():
    fs = 16000
    duration = 3  # seconds
    print("Recording 3 seconds of audio for testing...")
    
    try:
        myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()
        print("Recording complete.")
        
        max_val = np.max(np.abs(myrecording))
        print(f"Max Amplitude: {max_val}")
        
        if max_val == 0:
            print("ERROR: Recorded silence. Check your microphone settings.")
        else:
            print("Audio signal detected.")
            
    except Exception as e:
        print(f"Error accessing microphone: {e}")

if __name__ == "__main__":
    test_mic()
