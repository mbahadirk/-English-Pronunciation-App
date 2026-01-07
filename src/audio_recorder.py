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
        
        # Device management
        self.input_device_index = None
        
        # VAD Parameters
        self.vad_enabled = False
        
        # Dynamic Noise Adaptation - TUNED
        self.noise_floor = 300.0   # Higher initial guess
        self.speech_threshold_ratio = 2.0 
        self.min_amplitude = 500   # Hard minimum threshold (prevents 0-level silence triggers)
        self.adaptation_rate = 0.05 
        
        self.silence_blocks = 0
        self.max_silence_blocks = 10  # Reduced to ~0.6s for snappier response
        self.max_recording_blocks = 150 
        self.is_speaking = False
        
        # Callbacks
        self.on_speech_end = None 
        self.on_visualizer = None

    def list_devices(self):
        """Returns a list of input devices: [(index, name), ...]"""
        devices = sd.query_devices()
        inputs = []
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                inputs.append((i, dev['name']))
        return inputs

    def set_device(self, index):
        self.input_device_index = index
        print(f"Set input device to index {index}")

    def start_listening(self, on_speech_end_callback, on_visualizer_callback=None):
        """Starts the VAD loop."""
        if self.recording:
            return
        self.recording = True
        self.vad_enabled = True
        self.frames = []
        self.is_speaking = False
        self.silence_blocks = 0
        
        self.on_speech_end = on_speech_end_callback
        self.on_visualizer = on_visualizer_callback
        
        def record_thread():
            try:
                # Block size: 1024 samples ~ 64ms
                with sd.InputStream(samplerate=self.sample_rate, 
                                  channels=self.channels, 
                                  dtype='int16', 
                                  blocksize=1024,
                                  device=self.input_device_index) as stream:
                    
                    print(f"Microphone listening (Device: {self.input_device_index or 'Default'})...")
                    
                    while self.recording:
                        data, overflowed = stream.read(1024)
                        if overflowed:
                            pass
                        
                        # Data processing - Fix Overflow by casting to float
                        data_float = data.astype(np.float32)
                        rms = np.sqrt(np.mean(data_float**2))
                        peak_amp = np.max(np.abs(data)) # int16 is fine for max abs check
                        
                        # Dynamic Threshold Calculation
                        threshold = max(self.noise_floor * self.speech_threshold_ratio, self.min_amplitude)
                        
                        # Visualization
                        MAX_EXPECTED_AMP = 3000.0
                        norm_amp = min(rms / MAX_EXPECTED_AMP, 1.0)
                        norm_thresh = min(threshold / MAX_EXPECTED_AMP, 1.0)
                        
                        waveform_view = data[::20].flatten()
                        
                        if self.on_visualizer:
                            self.on_visualizer(norm_amp, waveform_view, self.is_speaking, norm_thresh)
                        
                        # VAD Logic
                        if not self.is_speaking:
                            # START CONDITION: Peak > Threshold AND Peak > Hard Min
                            if peak_amp > threshold:
                                print(f"Speech start! Peak: {peak_amp:.0f} > Thresh: {threshold:.0f}")
                                self.is_speaking = True
                                self.frames = [data]
                                self.silence_blocks = 0
                            else:
                                # Adapt noise floor fast when silent
                                self.noise_floor = (1 - self.adaptation_rate) * self.noise_floor + self.adaptation_rate * peak_amp
                        else:
                            # Speaking -> record and check for silence or timeout
                            self.frames.append(data)

                            
                            # Check if current chunk is silent
                            if peak_amp < threshold:
                                self.silence_blocks += 1
                            else:
                                self.silence_blocks = 0 
                            
                            # Stop conditions: (1) Silence timeout OR (2) Max duration
                            should_stop = False
                            stop_reason = ""
                            
                            if self.silence_blocks > self.max_silence_blocks:
                                should_stop = True
                                stop_reason = "Silence"
                            elif len(self.frames) > self.max_recording_blocks:
                                should_stop = True
                                stop_reason = "Max Duration"
                                
                            if should_stop:
                                print(f"Speech ended ({stop_reason}). Frames: {len(self.frames)}")
                                self.is_speaking = False
                                
                                # Process if meaningful length > 0.5s
                                if len(self.frames) > 8: 
                                    recording_data = np.concatenate(self.frames, axis=0)
                                    fd, path = tempfile.mkstemp(suffix=".wav")
                                    os.close(fd)
                                    write(path, self.sample_rate, recording_data)
                                    if self.on_speech_end:
                                        self.on_speech_end(path)
                                
                                self.frames = [] 
                                self.silence_blocks = 0
            except Exception as e:
                print(f"Recording error: {e}")
                self.recording = False

        self.thread = threading.Thread(target=record_thread, daemon=True)
        self.thread.start()

    def stop_recording(self):
        self.recording = False
        # Clear callbacks to stop sending data immediately
        self.on_visualizer = None
        self.on_speech_end = None
        
        if self.thread and self.thread.is_alive():
            # Don't join if called from the record thread itself (deadlock precaution)
            if threading.current_thread() != self.thread:
                self.thread.join(timeout=1.0) # Timeout to prevent UI freeze
        return None
