import whisper
from rapidfuzz import fuzz
import os
import numpy as np


class PronunciationScorer:
    def __init__(self, model_size="base"):
        print(f"Loading Whisper model ({model_size})...")
        # Ensure we are using CPU if CUDA is not available, or let torch decide (Whisper handles this usually)
        # We can enforce cpu if needed: device="cpu"
        self.model = whisper.load_model(model_size)
        print("Model loaded.")

    def score(self, audio_path, target_word):
        """
        Transcribes the audio and compares it to the target word.
        Returns a tuple (score, transcription).
        """
        if not audio_path or not os.path.exists(audio_path):
            return 0, ""

        try:
            # Bypass ffmpeg by loading with scipy
            # Whisper expects 16kHz audio. Our recorder is already 16kHz.
            from scipy.io import wavfile
            
            sample_rate, data = wavfile.read(audio_path)
            
            # Convert to float32 between -1 and 1 (Whisper expects this)
            # data is int16 from our recorder
            audio_np = data.astype(np.float32) / 32768.0
            
            # Transcribe using the numpy array instead of file path
            result = self.model.transcribe(audio_np, fp16=False) # fp16=False for CPU
            text = result["text"].strip().lower()
            
            # Clean up punctuation
            text_clean = ''.join(c for c in text if c.isalnum() or c.isspace())
            target_clean = ''.join(c for c in target_word.lower() if c.isalnum() or c.isspace())

            print(f"Target: {target_clean}, Transcribed: {text_clean}")

            # Calculate score using Levenshtein distance ratio
            # fuzz.ratio returns 0-100
            raw_score = fuzz.ratio(target_clean, text_clean)
            
            # Normalize to 0-10 integer
            score = int(round(raw_score / 10.0))
            
            return score, text_clean
        except Exception as e:
            print(f"Scoring error: {e}")
            return 0, f"Error: {str(e)}"
