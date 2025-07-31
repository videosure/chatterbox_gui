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
        self.root.geometry("820x500")

        # Device selection
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")

        # Load model in background
        threading.Thread(target=self.load_model, daemon=True).start()

        # State
        self.voice_file = None
        self.recent_files = []

        # GUI layout
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top controls: voice + CFG weight + exaggeration + help
        ctrl_frame = tk.Frame(main_frame)
        ctrl_frame.pack(fill=tk.X)

        tk.Button(ctrl_frame, text="Select Voice Sample", command=self.select_voice).pack(side=tk.LEFT)
        self.voice_label = tk.Label(ctrl_frame, text="No voice sample selected.")
        self.voice_label.pack(side=tk.LEFT, padx=5)

        # CFG weight slider
        tk.Label(ctrl_frame, text="CFG Weight:").pack(side=tk.LEFT, padx=(20,0))
        self.cfg_scale = tk.Scale(ctrl_frame, from_=0.0, to=1.0, resolution=0.1,
                                  orient=tk.HORIZONTAL, length=150)
        self.cfg_scale.set(0.5)
        self.cfg_scale.pack(side=tk.LEFT)

        # Exaggeration slider
        tk.Label(ctrl_frame, text="Exaggeration:").pack(side=tk.LEFT, padx=(20,0))
        self.exag_scale = tk.Scale(ctrl_frame, from_=0.0, to=1.0, resolution=0.1,
                                   orient=tk.HORIZONTAL, length=150)
        self.exag_scale.set(0.5)
        self.exag_scale.pack(side=tk.LEFT)

        # Help button
        help_btn = tk.Button(ctrl_frame, text="?", command=self.show_help)
        help_btn.pack(side=tk.LEFT, padx=(10,0))

        # Text input
        self.text_entry = tk.Text(main_frame, height=6)
        self.text_entry.pack(fill=tk.BOTH, expand=False, pady=10)

        # Generate button & progress bar
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

    def show_help(self):
        help_win = tk.Toplevel(self.root)
        help_win.title("Parameter Help")
        help_text = (
            "1. Exaggeration (Emotion Intensity)\n"
            "   - Range: 0.0 (minimal) → 1.0 (highly dramatic)\n"
            "   - Amplifies intonation, stress, emotion for livelier or subdued speech.\n"
            "     * 0.3–0.5: natural, conversational tone\n"
            "     * 0.6–0.8: energetic, animated\n\n"
            "2. CFG Weight (Guidance Scale)\n"
            "   - Range: 0.0 (loose adherence) → 1.0 (strict adherence)\n"
            "   - Balances between text encoder output and reference style.\n"
            "     * 0.3: slower pacing, deliberate delivery\n"
            "     * 0.5: balanced output\n"
            "     * 0.7–1.0: closer mimic of reference speaker rhythm\n"
        )
        lbl = tk.Label(help_win, text=help_text, justify=tk.LEFT, padx=10, pady=10)
        lbl.pack()

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
            cfg = self.cfg_scale.get()
            exag = self.exag_scale.get()
            wav = self.model.generate(
                text,
                audio_prompt_path=self.voice_file,
                cfg_weight=cfg,
                exaggeration=exag
            )
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
