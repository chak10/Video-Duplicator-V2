# VideoDuplicatorV2

VideoDuplicatorV2 is a Python-based application designed to detect and manage duplicate video files. The application utilizes frame hashing to analyze similarities between videos, presenting results in a user-friendly graphical interface. Users can review detected duplicates and select videos for deletion to optimize storage space.

## Features

- **Frame Hashing**: Extracts and hashes frames to identify duplicate or similar videos based on content.
- **Customizable Threshold**: Configurable similarity threshold for fine-tuning duplicate detection.
- **Video Comparison GUI**: Displays duplicate videos with information to assist in managing duplicates.
- **Dark Theme GUI**: A modern, Material Design-inspired GUI with a dark theme.
- **Progress Tracking**: Console displays processed files, remaining files, and estimated time remaining.
- **Configurable Parameters**: Customizable parameters, including `distance_threshold` in `config.py`.

## Requirements

- Python 3.8+
- Libraries: Listed in `requirements.txt`

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Chak10/VideoDuplicatorV2.git
   cd VideoDuplicatorV2

## Usage
1. Modify the config File
   ```py
   # config.py
   DIR_TO_PROCESS = "F:\\FRA-PR"  # Sostituisci con il percorso della tua cartella
   # Percorsi per ffmpeg e ffprobe
   FFMPEG_PATH = "ffmpeg.exe"  # Sostituisci con il percorso completo se necessario
   FFPROBE_PATH = "ffprobe.exe"  # Sostituisci con il percorso completo se necessario
   FRAMES_DIR = "frames"  # Directory dove verranno salvati i frame estratti
   # Configurazione del database
   DB_FILE = "video_data.db"  # Nome del file del database SQLite
   # Soglia di distanza Hamming
   DISTANCE_THRESHOLD = 8

2. Start main function
   ```bash
   py main.py
3. Wait the end of the main function and start video_gui
   ```bash
   py video_similarity_gui.py
