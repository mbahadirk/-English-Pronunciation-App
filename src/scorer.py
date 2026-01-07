import whisper
from rapidfuzz import fuzz
import os
import numpy as np


class PronunciationScorer:
    def __init__(self, model_size="medium.en"):
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
            
            # Calculate score using "Best Match" logic
            # If the user says "Um... fish... okay", and target is "fish", we should find "fish".
            
            target_clean = target_word.lower().strip()
            text_clean = result['text'].lower().strip()
            
            # Remove punctuation for better tokenization
            import string
            text_no_punct = text_clean.translate(str.maketrans('', '', string.punctuation))
            tokens = text_no_punct.split()
            
            best_score = 0
            
            if not tokens:
                 # usage case: empty or just noise
                 best_score = 0
            else:
                # Check each word in the phrase against the target
                for token in tokens:
                    # Calculate similarity for looking up the word
                    # fuzz.ratio is good for direct comparison
                    current_score = fuzz.ratio(target_clean, token)
                    if current_score > best_score:
                        best_score = current_score
                        
                # Also check the whole phrase just in case (e.g. multi-word targets like "ice cream")
                phrase_score = fuzz.ratio(target_clean, text_no_punct)
                if phrase_score > best_score:
                    best_score = phrase_score

            # Normalize to 0-10 integer
            score = int(round(best_score / 10.0))
            
            return score, text_clean
        except Exception as e:
            print(f"Scoring error: {e}")
            return 0, f"Error: {str(e)}"
