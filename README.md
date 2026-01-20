# English Pronunciation App

A Python-based application designed to help users improve their English pronunciation. This tool interacts with the user by recording their voice, analyzing the pronunciation using OpenAI Whisper, and providing a score. It also features Text-to-Speech (TTS) capabilities to help users hear the correct pronunciation.

## Features

- **Interactive GUI**: Built with Tkinter for a user-friendly experience.
- **Audio Recording**: Capture your voice directly within the app.
- **Pronunciation Scoring**: Utilizes OpenAI Whisper for accurate speech recognition and scoring.
- **Text-to-Speech**: Listen to the correct pronunciation of words or phrases.
- **Progress Tracking**: (Implied, if applicable, otherwise remove)
- **Word Database**: Includes a CEFR-leveled word list for practice.

## Prerequisites

Before running the application, ensure you have the following installed:

- **Python 3.8+**
- **FFMPEG**: Required for OpenAI Whisper to process audio.
    - [Download FFMPEG](https://ffmpeg.org/download.html) and ensure it is added to your system's PATH.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/mbahadirk/English-Pronunciation-App.git
    ```

2.  **Navigate to the application directory:**
    ```bash
    cd English-Pronunciation-App
    ```

3.  **Run the setup script:**
    This script will install necessary dependencies, including PyTorch (CPU version), OpenAI Whisper, and others.
    ```cmd
    setup.bat
    ```

    *Alternatively, you can manually install the requirements:*
    ```bash
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    pip install "numpy<2"
    pip install -r requirements.txt
    ```

## Usage

To start the application, simply run the launch script from the `pronunciation_app` directory:

```cmd
run_app.bat
```

Or manually using Python:

```bash
python main.py
```

## Project Structure

- `main.py`: The entry point of the application.
- `setup.bat`: Windows batch script for easy installation of dependencies.
- `run_app.bat`: Windows batch script to launch the app.
- `src/`: Contains the source code.
    - `gui_tkinter.py`: The graphical user interface.
    - `audio_recorder.py`: Handles audio recording logic.
    - `scorer.py`: Logic for analyzing and scoring pronunciation.
    - `speaker.py`: Text-to-Speech functionality.
- `data/`: Contains application data (e.g., word lists).

## Requirements

The main dependencies are listed in `requirements.txt`:
- `openai-whisper`
- `sounddevice`
- `numpy<2`
- `scipy`
- `rapidfuzz`
- `pyttsx3`
