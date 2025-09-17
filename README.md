# chatterbox_gui
A simple Python 3 desktop application that lets you generate speech using the ChatterboxTTS voice-cloning model.

## Chatterbox TTS GUI

A simple Python 3 desktop application that lets you generate speech using the [ChatterboxTTS](https://github.com/resemble-ai/chatterbox) voice-cloning model. It provides:

* **Voice sample selection** (wav, mp3, flac)
* **Text input** for synthesis
* **Progress bar** during generation
* **Recent outputs** list (double-click to play any file)
* **Play** and **Stop** controls
* **CFG Weight** and **Exaggeration** sliders
---

### 🚀 Features

1. **Automatic device selection**: uses `cuda` if available else falls back to `cpu`.
2. **Responsive UI**: model loading and synthesis run in background threads.
3. **Built-in playback**: Windows `winsound` module plays WAVs without extra dependencies.
4. **History**: keeps up to 10 recent output files.

---

### 🛠️ Prerequisites

* Python 3.8 or newer
* Windows OS (uses built-in `winsound` for audio playback)


  Steps inside the app:
   - Click **Select Voice Sample** and pick a WAV/MP3/FLAC file.
   - Enter text to speak in the text box.
   - Click **Generate Speech**.
   - Save the output WAV when prompted. Playback controls and recent list will activate.

---

### ⚠️ Troubleshooting

- **Model load fails**: check your internet connection and CUDA toolkit installation if on GPU.
- **`tkinter` not found**: ensure your Python installation includes GUI support.
- **Audio doesn’t play**: this uses `winsound`, which only supports WAV. Ensure you saved as `.wav` and are on Windows.


