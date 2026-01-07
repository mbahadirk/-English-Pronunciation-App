import tkinter as tk
from tkinter import messagebox
import json
import random
import threading
import os
import sys

# Add the current directory to path to find local modules if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio_recorder import AudioRecorder
from scorer import PronunciationScorer


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("English Pronunciation Coach")
        self.geometry("600x600")
        
        # Data
        self.levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        self.words_data = self.load_words()
        self.unlocked_level_index = 0
        
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
        # Top Bar for settings
        self.top_bar = tk.Frame(self, bg="#eeeeee", height=40)
        self.top_bar.pack(fill="x", side="top")
        
        tk.Label(self.top_bar, text="Mic:", bg="#eeeeee").pack(side="left", padx=5)
        
        self.device_var = tk.StringVar()
        self.devices = self.recorder.list_devices()
        device_names = [d[1] for d in self.devices]
        
        if not device_names:
            device_names = ["Default"]
        
        self.device_menu = tk.OptionMenu(self.top_bar, self.device_var, *device_names, command=self.change_device)
        self.device_menu.pack(side="left", padx=5)
        self.device_var.set(device_names[0])
        self.change_device(device_names[0]) # Init default

        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.show_loading_screen()
        
        # Start loading model in background
        self.load_model_thread()

    def change_device(self, selection):
        # Find index
        idx = None
        for i, name in self.devices:
            if name == selection:
                idx = i
                break
        self.recorder.set_device(idx)
        # Restart listener if active
        if self.recorder.recording:
            self.start_auto_listen()

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
                # Switch to "tiny" for speed on CPU
                self.scorer = PronunciationScorer(model_size="tiny")
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
        # Stop listening if we were
        self.recorder.stop_recording()
        
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
        # 1. Safety: Stop listening and detach callbacks immediately
        # This prevents the background thread from trying to update the UI while we destroy it
        if self.recorder:
            self.recorder.stop_recording()
            self.recorder.on_visualizer = None
            self.recorder.on_speech_end = None
            
        # 2. Clear UI
        for widget in self.container.winfo_children():
            widget.destroy()
            
        if self.current_word_index >= len(self.session_words):
            self.show_results_screen()
            return

        target_word = self.session_words[self.current_word_index]
        self.current_word_best = 0 # Track best score for this specific word
        
        # Header
        tk.Label(self.container, text=f"Level {self.current_level} - Word {self.current_word_index + 1}/{len(self.session_words)}", 
                 font=("Helvetica", 12)).pack(pady=10)
        
        # Target Word
        tk.Label(self.container, text=target_word, font=("Helvetica", 36, "bold"), fg="#333").pack(pady=20)
        
        # Instructions
        self.status_label = tk.Label(self.container, text="Listening...", font=("Helvetica", 12, "italic"), fg="blue")
        self.status_label.pack(pady=5)
        
        # VAD Status & Audio Visualizer
        self.mic_label = tk.Label(self.container, text="Mic Ready", font=("Helvetica", 10), fg="grey")
        self.mic_label.pack(pady=0)
        
        # Canvas for visualization using black background for contrast
        self.canvas = tk.Canvas(self.container, width=400, height=100, bg="#222222", highlightthickness=0)
        self.canvas.pack(pady=10)
        # Initialize line
        self.line_id = self.canvas.create_line(0, 50, 400, 50, fill="#00ff00", width=2)
        
        # Feedback area
        self.feedback_label = tk.Label(self.container, text="(Try saying the word)", font=("Helvetica", 12), fg="#666666")
        self.feedback_label.pack(pady=10)
        
        self.score_label = tk.Label(self.container, text="Best Score: 0/10", font=("Helvetica", 14, "bold"))
        self.score_label.pack(pady=5)
        
        self.next_btn = tk.Button(self.container, text="Next Word", state="normal", command=self.next_word)
        self.next_btn.pack(pady=10)
        
        # Restart listening
        self.start_auto_listen()

    def start_auto_listen(self):
        self.recorder.stop_recording()
        self.recorder.start_listening(self.on_speech_detected, self.on_visualizer_data)

    def on_visualizer_data(self, level, waveform, is_speaking, threshold_norm):
        self.container.after(0, lambda: self._update_visualizer(level, waveform, is_speaking, threshold_norm))
        
    def _update_visualizer(self, level, waveform, is_speaking, threshold_norm):
        try:
            if not self.canvas.winfo_exists():
                return

            w = 400
            h = 100
            mid = h / 2
            scale = 0.005
            
            # 1. Draw Waveform
            coords = []
            step = w / len(waveform)
            
            for i, val in enumerate(waveform):
                x = i * step
                y = mid - (val * scale) 
                coords.extend([x, y])
                
            self.canvas.coords(self.line_id, *coords)
            color = "#00ff00" if is_speaking else "#555555"
            self.canvas.itemconfig(self.line_id, fill=color, width=2)
            
            # 2. Draw Threshold (Red Line)
            thresh_pixels = (threshold_norm * 3000.0) * scale 
            top_y = mid - thresh_pixels
            bottom_y = mid + thresh_pixels
            
            if not hasattr(self, 'thresh_line_top'):
                self.thresh_line_top = self.canvas.create_line(0, top_y, 400, top_y, fill="#aa0000", dash=(2, 2))
                self.thresh_line_bot = self.canvas.create_line(0, bottom_y, 400, bottom_y, fill="#aa0000", dash=(2, 2))
            else:
                self.canvas.coords(self.thresh_line_top, 0, top_y, 400, top_y)
                self.canvas.coords(self.thresh_line_bot, 0, bottom_y, 400, bottom_y)

            # Status text update
            status_text = "Speaking..." if is_speaking else "Listening..."
            status_color = "green" if is_speaking else "grey"
            if self.mic_label.cget("text") != status_text:
                self.mic_label.config(text=status_text, fg=status_color)
        except Exception:
            # Ignore errors during shutdown/transition
            pass

    def on_speech_detected(self, audio_path):
        """Callback from recorder thread when speech ends"""
        # Ensure we don't process if the screen changed
        if not self.container.winfo_exists():
            return
        self.container.after(0, lambda: self.process_auto_recording(audio_path))

    def process_auto_recording(self, audio_path):
        if not self.status_label.winfo_exists():
            return
        self.status_label.config(text="Processing...", fg="orange")
        # Don't freeze UI
        threading.Thread(target=self.score_thread, args=(audio_path,), daemon=True).start()

    def score_thread(self, audio_path):
        # Check index to ensure we are still on the same word (basic concurrency check)
        current_idx = self.current_word_index
        target_word = self.session_words[current_idx]
        
        if self.scorer:
            score, transcription = self.scorer.score(audio_path, target_word)
            # Pass the index back to ensure validity
            self.container.after(0, lambda: self.show_score(score, transcription, current_idx))
        else:
            self.container.after(0, lambda: self.reset_record_ui("Scorer error"))

    def show_score(self, score, transcription, origin_index=None):
        try:
            # Safety check: if user moved to next word, ignore this old result
            if origin_index is not None and origin_index != self.current_word_index:
                print("Ignoring result from previous word.")
                return

            # Logic: Continuous retry. 
            # We keep the BEST result for this word.
            
            improved = False
            if score > self.current_word_best:
                self.current_word_best = score
                improved = True
            
            # Update UI
            # Score is now 0-10. Threshold for "Good" is 7.
            color = "green" if score >= 7 else "red"
            msg = f"Last Try: {score}/10\nYou said: '{transcription}'"
            
            if self.feedback_label.winfo_exists():
                self.feedback_label.config(text=msg, fg=color)
            
            if self.score_label.winfo_exists():
                best_color = "green" if self.current_word_best >= 7 else "orange"
                self.score_label.config(text=f"Best Score: {self.current_word_best}/10", fg=best_color)
            
            if self.status_label.winfo_exists():
                if improved:
                    self.status_label.config(text="New Personal Best!", fg="green")
                else:
                    self.status_label.config(text="Listening for retry...", fg="#333333")
                
            # Do NOT stop recording. Just let it adapt and listen again.
            
        except Exception as e:
            print(f"Error in show_score: {e}")

    def next_word(self):
        # Commit the best score to the session
        # Score is now 0-10
        if self.current_word_best >= 7:
             pass # Passing grade

        self.total_score += self.current_word_best
        self.results.append((self.session_words[self.current_word_index], self.current_word_best, "Best Result"))
        
        self.recorder.stop_recording() # Stop briefly while switching screens
        
        self.current_word_index += 1
        self.show_practice_screen()

    def show_results_screen(self):
        for widget in self.container.winfo_children():
            widget.destroy()
            
        # Stop everything
        self.recorder.stop_recording()
            
        avg_score = self.total_score / len(self.session_words) if self.session_words else 0
        success = avg_score >= 7.0 # 7 out of 10
        
        title = "Level Complete!" if success else "Keep Practicing"
        color = "green" if success else "orange"
        
        tk.Label(self.container, text=title, font=("Helvetica", 24, "bold"), fg=color).pack(pady=20)
        tk.Label(self.container, text=f"Average Score: {avg_score:.1f}/10", font=("Helvetica", 18)).pack(pady=10)
        
        if success:
            tk.Label(self.container, text="Unlocked next level!", font=("Helvetica", 12)).pack(pady=5)
            # Unlock next level logic
            current_idx = self.levels.index(self.current_level)
            if current_idx < len(self.levels) - 1:
                if self.unlocked_level_index <= current_idx:
                    self.unlocked_level_index = current_idx + 1
        else:
            tk.Label(self.container, text="Need 7.0+ average to unlock next level.", font=("Helvetica", 12)).pack(pady=5)

        tk.Button(self.container, text="Back to Menu", font=("Helvetica", 14), command=self.show_level_selection).pack(pady=30)

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
