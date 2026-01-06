import sounddevice as sd
from scipy.io.wavfile import write
import os
import tempfile
import threading
import numpy as np
import time

class AudioRecorder:
    def __init__(self, sample_rate=16000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.recording = False
        self.frames = []
        self.stream = None
        self.thread = None
        
        # VAD Parameters
        self.vad_enabled = False
        self.silence_threshold = 500  # Amplitude threshold (int16) - Adjust based on mic
        self.silence_blocks = 0
        self.max_silence_blocks = 30  # Approx 1-1.5 seconds of silence to stop
        self.is_speaking = False
        self.on_speech_end = None # Callback function

    def start_listening(self, on_speech_end_callback):
        """Starts the VAD loop."""
        if self.recording:
            return
        self.recording = True
        self.vad_enabled = True
        self.frames = []
        self.is_speaking = False
        self.silence_blocks = 0
        self.on_speech_end = on_speech_end_callback
        
        def record_thread():
            # Block size: 1024 samples ~ 64ms
            with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, dtype='int16', blocksize=1024) as stream:
                print("Microphone listening...")
                while self.recording:
                    # Read audio chunk
                    data, overflowed = stream.read(1024)
                    if overflowed:
                        pass
                    
                    # Calculate amplitude (max of abs)
                    amplitude = np.max(np.abs(data))
                    
                    if not self.is_speaking:
                        # Waiting for speech to start
                        if amplitude > self.silence_threshold:
                            print("Speech detected! Starting capture...")
                            self.is_speaking = True
                            self.frames = [data] # Start fresh
                            self.silence_blocks = 0
                    else:
                        # Currently speaking
                        self.frames.append(data)
                        
                        if amplitude < self.silence_threshold:
                            self.silence_blocks += 1
                        else:
                            self.silence_blocks = 0 # Reset if we hear noise again
                        
                        # Check if silence has lasted long enough to stop
                        if self.silence_blocks > self.max_silence_blocks:
                            print("Speech ended.")
                            self.is_speaking = False
                            
                            # Determine if valid recording (not just a click)
                            if len(self.frames) > 15: # Ignore very short blips
                                recording_data = np.concatenate(self.frames, axis=0)
                                
                                # Save and callback
                                fd, path = tempfile.mkstemp(suffix=".wav")
                                os.close(fd)
                                write(path, self.sample_rate, recording_data)
                                
                                if self.on_speech_end:
                                    self.on_speech_end(path)
                            
                            self.frames = [] # Reset for next phrase
                            self.silence_blocks = 0

        self.thread = threading.Thread(target=record_thread, daemon=True)
        self.thread.start()

    def stop_recording(self):
        self.recording = False
        if self.thread:
            self.thread.join()
        self.frames = []
        return None
