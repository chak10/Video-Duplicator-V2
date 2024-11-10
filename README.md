Grazie per l'aggiornamento! Ecco il README aggiornato con **config.ini** al posto di **config.py**:

---

# Video Duplicator V2

**Video Duplicator V2** is a powerful tool designed for identifying and managing duplicate video files on your system. Leveraging advanced hashing algorithms, the application extracts frame-level information to accurately detect identical or nearly identical videos, saving storage and ensuring an organized video library.

## Features

- **Precise Duplicate Detection**: Uses frame hashing to detect identical or highly similar videos, even with slight differences.
- **Customizable Similarity Threshold**: Set a custom similarity threshold to filter videos by visual resemblance.
- **Material Design GUI**: A sleek, dark-themed GUI built with Material Design principles for a user-friendly experience.
- **Detailed Video Comparison**: Offers a side-by-side comparison and provides detailed information on similar videos, making it easy to decide which one to keep or delete.
- **Progress and Elapsed Time Tracking**: Track real-time processing status with a progress bar and elapsed time display in the console.
- **Flexible Settings**: Configure various parameters, such as frame extraction frequency, CRF (Constant Rate Factor) for compression, and more.
- **Multi-format Compatibility**: Supports a wide range of video formats for easy integration into any workflow.

## Prerequisites

To run Video Duplicator V2, ensure you have the following installed:

- **Python** 3.8+
- **FFmpeg**: Required for frame extraction and video processing.
- Additional dependencies, listed in `requirements.txt`.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/Chak10/Video-Duplicator-V2.git
   cd Video-Duplicator-V2
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Make sure **FFmpeg** is accessible in your system’s PATH.

## Usage

1. **Configure Settings**:
   - Edit the `config.ini` file to set parameters, including the `distance_threshold`, CRF value for video compression, and other options.

2. **Run the Application**:
   - Start the application with the command:

     ```bash
     python main.py
     ```

3. **Using the GUI**:
   - Use the GUI to scan your video folders, view similar videos, and delete duplicates as needed.
   - The GUI also shows the similarity percentage and allows for comparison.
  
     ```bash
     python video_similarity_gui.py
     ```

## Customization

### Frame Extraction
To optimize frame extraction, adjust the frame extraction frequency in `config.ini`. For faster processing, GPU acceleration is also supported.

### CRF Setting
Set the CRF (Constant Rate Factor) value in `config.ini` to control video quality. Lower values mean higher quality but larger file sizes.

### Similarity Threshold
Modify the `distance_threshold` in `config.ini` to control the tolerance level for similarity between videos.

## Notes

- **Performance Optimization**: This application avoids unnecessary parallel processing to enhance stability.
- **Backup Support**: Includes incremental backup capabilities, allowing you to maintain backups of your video library.
- **Error Handling**: Provides informative console output without interruptive PHP error messages.

## Contributing

We welcome contributions! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Se desideri ulteriori modifiche o approfondimenti, fammi sapere!
