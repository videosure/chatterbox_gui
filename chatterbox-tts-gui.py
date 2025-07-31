import torch
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import winsound  # built-in on Windows for WAV playback

class TTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chatterbox TTS")
        self.root.geometry("600x400")

        # Device selection
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")

        # Model loading
        threading.Thread(target=self.load_model, daemon=True).start()

        # State
        self.voice_file = None
        self.recent_files = []

        # GUI layout
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top controls
        ctrl_frame = tk.Frame(main_frame)
        ctrl_frame.pack(fill=tk.X)

        tk.Button(ctrl_frame, text="Select Voice Sample", command=self.select_voice).pack(side=tk.LEFT)
        self.voice_label = tk.Label(ctrl_frame, text="No voice sample selected.")
        self.voice_label.pack(side=tk.LEFT, padx=5)

        # Text input
        self.text_entry = tk.Text(main_frame, height=5)
        self.text_entry.pack(fill=tk.BOTH, expand=False, pady=10)

        # Generate button and progress bar
        gen_frame = tk.Frame(main_frame)
        gen_frame.pack(fill=tk.X)

        self.generate_btn = tk.Button(gen_frame, text="Generate Speech", state=tk.DISABLED, command=self.generate)
        self.generate_btn.pack(side=tk.LEFT)
        self.status_label = tk.Label(gen_frame, text="Loading model...")
        self.status_label.pack(side=tk.LEFT, padx=10)

        self.progress = ttk.Progressbar(gen_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, expand=True, padx=10)

        # Playback controls
        play_frame = tk.Frame(main_frame)
        play_frame.pack(fill=tk.X, pady=5)

        self.play_btn = tk.Button(play_frame, text="Play", state=tk.DISABLED, command=self.play_audio)
        self.play_btn.pack(side=tk.LEFT)
        self.stop_btn = tk.Button(play_frame, text="Stop", state=tk.DISABLED, command=self.stop_audio)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Recent files list
        recent_frame = tk.LabelFrame(main_frame, text="Recent Outputs")
        recent_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.recent_listbox = tk.Listbox(recent_frame)
        self.recent_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = tk.Scrollbar(recent_frame, command=self.recent_listbox.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.recent_listbox.config(yscrollcommand=scrollbar.set)
        self.recent_listbox.bind('<Double-1>', self.play_selected)

    def load_model(self):
        try:
            self.model = ChatterboxTTS.from_pretrained(device=self.device)
            self.root.after(0, lambda: self.status_label.config(text="Model loaded."))
            self.root.after(0, lambda: self.generate_btn.config(state=tk.NORMAL))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load model: {e}")
            self.root.after(0, lambda: self.status_label.config(text="Load failed."))

    def select_voice(self):
        path = filedialog.askopenfilename(
            title="Select voice sample",
            filetypes=[("Audio Files", "*.wav *.mp3 *.flac"), ("All Files", "*")]
        )
        if path:
            self.voice_file = path
            self.voice_label.config(text=os.path.basename(path))

    def generate(self):
        text = self.text_entry.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Input required", "Please type some text.")
            return
        if not self.voice_file or not os.path.exists(self.voice_file):
            messagebox.showwarning("Voice sample", "Select a valid voice sample.")
            return

        self.generate_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Generating...")
        self.progress.start()
        threading.Thread(target=self._generate_thread, args=(text,), daemon=True).start()

    def _generate_thread(self, text):
        try:
            wav = self.model.generate(text, audio_prompt_path=self.voice_file)
            output_file = filedialog.asksaveasfilename(
                title="Save output as",
                defaultextension=".wav",
                filetypes=[("WAV Files", "*.wav")]
            )
            if output_file:
                ta.save(output_file, wav, self.model.sr)
                self.add_recent(output_file)
                self.status_label.config(text=f"Saved {os.path.basename(output_file)}")
                self.root.after(0, lambda: self.play_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.stop_btn.config(state=tk.NORMAL))
            else:
                self.status_label.config(text="Canceled.")
        except Exception as e:
            messagebox.showerror("Error", f"Generation failed: {e}")
            self.status_label.config(text="Error.")
        finally:
            self.progress.stop()
            self.generate_btn.config(state=tk.NORMAL)

    def add_recent(self, filepath):
        if filepath not in self.recent_files:
            self.recent_files.insert(0, filepath)
            self.recent_listbox.insert(0, os.path.basename(filepath))
            if len(self.recent_files) > 10:
                self.recent_files.pop()
                self.recent_listbox.delete(tk.END)

    def play_audio(self):
        if self.recent_files:
            winsound.PlaySound(self.recent_files[0], winsound.SND_FILENAME | winsound.SND_ASYNC)

    def stop_audio(self):
        winsound.PlaySound(None, winsound.SND_PURGE)

    def play_selected(self, event):
        idx = self.recent_listbox.curselection()
        if idx:
            filepath = self.recent_files[idx[0]]
            winsound.PlaySound(filepath, winsound.SND_FILENAME | winsound.SND_ASYNC)

if __name__ == "__main__":
    root = tk.Tk()
    app = TTSApp(root)
    root.mainloop()
