import tkinter as tk
from tkinter import messagebox
import json
import random
import threading
import os
import sys

# Add the current directory to path to find local modules if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.audio_recorder import AudioRecorder
from src.scorer import PronunciationScorer

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("English Pronunciation Coach")
        self.geometry("600x500")
        
        # Data
        self.levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        self.words_data = self.load_words()
        self.unlocked_level_index = 0 # Start at A1
        
        # Session state
        self.current_level = None
        self.session_words = []
        self.current_word_index = 0
        self.total_score = 0
        self.results = []
        
        # Backend
        self.recorder = AudioRecorder()
        self.scorer = None
        self.model_loading = False
        
        # UI Setup
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.show_loading_screen()
        
        # Start loading model in background
        self.load_model_thread()

    def load_words(self):
        try:
            path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "words.json")
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Could not load words.json: {e}")
            return {}

    def load_model_thread(self):
        def _load():
            try:
                self.scorer = PronunciationScorer(model_size="base")
                self.after(0, self.on_model_loaded)
            except Exception as e:
                print(f"Error loading model: {e}")
                self.after(0, lambda: messagebox.showerror("Error", f"Failed to load Whisper model: {e}"))
        
        self.model_loading = True
        threading.Thread(target=_load, daemon=True).start()

    def on_model_loaded(self):
        self.model_loading = False
        self.show_level_selection()

    def show_loading_screen(self):
        for widget in self.container.winfo_children():
            widget.destroy()
        
        tk.Label(self.container, text="Loading AI Model...", font=("Helvetica", 16)).pack(expand=True)
        tk.Label(self.container, text="(This may take a moment)", font=("Helvetica", 10)).pack()

    def show_level_selection(self):
        for widget in self.container.winfo_children():
            widget.destroy()
            
        tk.Label(self.container, text="Select Level", font=("Helvetica", 24, "bold")).pack(pady=20)
        
        for i, level in enumerate(self.levels):
            state = "normal" if i <= self.unlocked_level_index else "disabled"
            color = "green" if i <= self.unlocked_level_index else "grey"
            
            btn = tk.Button(self.container, text=f"Level {level}", 
                            font=("Helvetica", 14), 
                            state=state,
                            width=15,
                            command=lambda l=level: self.start_level(l))
            btn.pack(pady=5)

    def start_level(self, level):
        self.current_level = level
        # Pick 10 random words
        all_words = self.words_data.get(level, [])
        if len(all_words) < 10:
            self.session_words = all_words # Fallback if not enough words
        else:
            self.session_words = random.sample(all_words, 10)
            
        self.current_word_index = 0
        self.total_score = 0
        self.results = []
        
        self.show_practice_screen()

    def show_practice_screen(self):
        for widget in self.container.winfo_children():
            widget.destroy()
            
        if self.current_word_index >= len(self.session_words):
            self.show_results_screen()
            return

        target_word = self.session_words[self.current_word_index]
        
        # Header
        tk.Label(self.container, text=f"Level {self.current_level} - Word {self.current_word_index + 1}/{len(self.session_words)}", 
                 font=("Helvetica", 12)).pack(pady=10)
        
        # Target Word
        tk.Label(self.container, text=target_word, font=("Helvetica", 36, "bold"), fg="#333").pack(pady=30)
        
        # Instructions
        self.status_label = tk.Label(self.container, text="Listening... Speak the word!", font=("Helvetica", 12, "italic"), fg="blue")
        self.status_label.pack(pady=10)
        
        # Visual indicator (Mic Status)
        self.mic_label = tk.Label(self.container, text="🎤 Active", font=("Helvetica", 10), fg="green")
        self.mic_label.pack(pady=5)
        
        # Feedback area
        self.feedback_label = tk.Label(self.container, text="", font=("Helvetica", 12))
        self.feedback_label.pack(pady=20)
        
        self.next_btn = tk.Button(self.container, text="Next Word", state="disabled", command=self.next_word)
        self.next_btn.pack(pady=10)
        
        # Start VAD immediately
        self.start_auto_listen()

    def start_auto_listen(self):
        # Stop any existing recording first
        self.recorder.stop_recording()
        
        # Start listening with callback
        self.recorder.start_listening(self.on_speech_detected)

    def on_speech_detected(self, audio_path):
        """Callback from recorder thread when speech ends"""
        self.container.after(0, lambda: self.process_auto_recording(audio_path))

    def process_auto_recording(self, audio_path):
        self.status_label.config(text="Processing...", fg="orange")
        self.mic_label.config(text="Analyzing...", fg="orange")
        
        # Run scoring in thread to not freeze UI
        threading.Thread(target=self.score_thread, args=(audio_path,), daemon=True).start()

    def score_thread(self, audio_path):
        target_word = self.session_words[self.current_word_index]
        if self.scorer:
            score, transcription = self.scorer.score(audio_path, target_word)
            self.container.after(0, lambda: self.show_score(score, transcription))
        else:
            self.container.after(0, lambda: self.reset_record_ui("Scorer error"))

    def show_score(self, score, transcription):
        # Only update score if we haven't already moved on (simple check)
        # In a real app we'd use IDs, but this is fine for now
        
        self.total_score += score
        self.results.append((self.session_words[self.current_word_index], score, transcription))
        
        color = "green" if score >= 70 else "red"
        msg = f"Score: {score}/100\nYou said: '{transcription}'"
        
        self.feedback_label.config(text=msg, fg=color)
        self.status_label.config(text="Done!", fg="black")
        self.mic_label.config(text="Stopped", fg="grey")
        
        self.next_btn.config(state="normal")
        
        # Stop listening since we are done with this word
        self.recorder.stop_recording()

    def next_word(self):
        self.current_word_index += 1
        self.show_practice_screen()

    def show_results_screen(self):
        for widget in self.container.winfo_children():
            widget.destroy()
            
        avg_score = self.total_score / len(self.session_words) if self.session_words else 0
        success = avg_score >= 70
        
        title = "Level Complete!" if success else "Keep Practicing"
        color = "green" if success else "orange"
        
        tk.Label(self.container, text=title, font=("Helvetica", 24, "bold"), fg=color).pack(pady=20)
        tk.Label(self.container, text=f"Average Score: {avg_score:.1f}/100", font=("Helvetica", 18)).pack(pady=10)
        
        if success:
            tk.Label(self.container, text="Unlocked next level!", font=("Helvetica", 12)).pack(pady=5)
            # Unlock next level logic
            current_idx = self.levels.index(self.current_level)
            if current_idx < len(self.levels) - 1:
                if self.unlocked_level_index <= current_idx:
                    self.unlocked_level_index = current_idx + 1
        else:
            tk.Label(self.container, text="Need 70+ average to unlock next level.", font=("Helvetica", 12)).pack(pady=5)

        tk.Button(self.container, text="Back to Menu", font=("Helvetica", 14), command=self.show_level_selection).pack(pady=30)
