import subprocess
import re
import imagehash
import logging
import io
import time
import cv2
import shutil
import configparser

from PIL import Image
from pathlib import Path
from tqdm import tqdm

from database_manager import insert_video, video_exists_in_db
from concurrent.futures import ThreadPoolExecutor
from hash_utils import combine_hashes_mode  # Importa la funzione per combinare gli hash
from pathlib import Path

# Load configuration
config = configparser.ConfigParser()

# Check if the config file exists
config_file = Path('config.ini')
if not config_file.exists():
    raise FileNotFoundError(f"Il file di configurazione 'config.ini' non è stato trovato.")

config.read(config_file)

# Load paths
FFMPEG_PATH = config['Paths']['FFMPEG_PATH']
FFPROBE_PATH = config['Paths']['FFPROBE_PATH']
FRAMES_DIR = config['Paths']['FRAMES_DIR']

# Print the loaded paths for verification
print(f"FFMPEG_PATH: {FFMPEG_PATH}")
print(f"FFPROBE_PATH: {FFPROBE_PATH}")
print(f"FRAMES_DIR: {FRAMES_DIR}")

# Check if the paths exist
for path in [FFMPEG_PATH, FFPROBE_PATH, FRAMES_DIR]:
    if not Path(path).exists():
        print(f"Attenzione: Il percorso '{path}' non esiste.")
        
# Configurazione del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename="video_processing.log")

def sanitize_filename(filename: str) -> str:
    """Rimuove caratteri non validi dal nome del file."""
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', filename)

def get_video_duration(video_path: Path) -> float:
    """Restituisce la durata del video in secondi."""
    command = [FFPROBE_PATH, '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(video_path)]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, text=True, check=True, stderr=subprocess.DEVNULL)
        return float(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        logging.error(f"Errore nel recuperare la durata del video {video_path}: {e}")
        return 0.0  # Restituisci 0.0 per indicare un errore

def get_video_resolution(video_path: Path) -> str:
    """Ottiene la risoluzione del video usando ffprobe."""
    command = [FFPROBE_PATH, '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', str(video_path)]
    try:
        resolution = subprocess.check_output(command, stderr=subprocess.DEVNULL).strip().decode('utf-8').split(',')
        return f"{resolution[0]}x{resolution[1]}"
    except subprocess.CalledProcessError as e:
        logging.error(f"Errore nel recuperare la risoluzione del video {video_path}: {e}")
        return "N/A"

def move_video_to_problematic(video_path: Path) -> None:
    """Sposta il video in una cartella 'problematic' se si verifica un errore."""
    problem_dir = video_path.parent / "problematic"
    problem_dir.mkdir(exist_ok=True)  # Crea una singola cartella "problematic" se non esiste già
    moved_video_path = problem_dir / video_path.name

    if not moved_video_path.exists():
        shutil.move(str(video_path), moved_video_path)
        logging.info(f"Video spostato in problematico: {moved_video_path}")

def attempt_frame_extraction(video_path: Path, timestamp: float, output_frame_path: Path) -> imagehash.ImageHash:
    """Tenta di estrarre un frame usando ffmpeg o OpenCV e calcola l'hash."""
    try:
        # Prova con ffmpeg
        command = [
            FFMPEG_PATH, '-ss', str(timestamp), '-i', str(video_path),
            '-vframes', '1', '-f', 'image2pipe', '-vcodec', 'png', '-y', 'pipe:1'
        ]
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            image_data, err = proc.communicate()
            if proc.returncode == 0:
                pil_image = Image.open(io.BytesIO(image_data))
                pil_image.save(output_frame_path)
                return imagehash.phash(pil_image)

            # Log dell'errore di ffmpeg
            logging.warning(f"ffmpeg ha restituito un errore: {err.decode().strip()}")

        # Se ffmpeg fallisce, prova con OpenCV
        cap = cv2.VideoCapture(str(video_path))
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        success, frame = cap.read()
        cap.release()

        if success:
            pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            pil_image.save(output_frame_path)
            return imagehash.phash(pil_image)
        logging.error(f"OpenCV ha fallito per il video {video_path}")

    except Exception as e:
        logging.error(f"Errore durante l'estrazione del frame: {e}")

    return None

def extract_frame(video_path: Path, timestamp: float, output_frame_path: Path) -> imagehash.ImageHash:
    """Prova l'estrazione di frame e gestisce errori spostando video problematici."""
    phash = attempt_frame_extraction(video_path, timestamp, output_frame_path)
    if phash is not None:
        return phash

    # Se fallisce, logga il video problematico e sposta il video
    logging.error(f"Errore irreversibile: impossibile estrarre frame da {video_path}")
    move_video_to_problematic(video_path)

    with open("error_videos.log", "a") as log_file:
        log_file.write(f"{video_path}\n")
    
    return None

def extract_video_info(video_path: Path) -> bool:
    """Estrae informazioni dal video e le inserisce nel database."""
    if video_exists_in_db(str(video_path)):
        return False

    resolution = get_video_resolution(video_path)
    size = video_path.stat().st_size
    duration = get_video_duration(video_path)

    if duration == 0.0 or resolution == "N/A":
        return False

    sanitized_folder_name = sanitize_filename(video_path.stem)
    frames_folder = Path(FRAMES_DIR) / sanitized_folder_name
    frames_folder.mkdir(parents=True, exist_ok=True)

    timestamps = [duration * (i + 1) / 4 for i in range(3)]
    frame_hashes = []
    frame_paths = []

    for idx, timestamp in enumerate(timestamps):
        output_frame_path = frames_folder / f"frame_{idx + 1}.jpg"
        
        # Controlla se il frame esiste già
        if output_frame_path.exists():
            # Se esiste, calcola l'hash dal file esistente
            pil_image = Image.open(output_frame_path)
            frame_hash = imagehash.phash(pil_image)
            frame_hashes.append(frame_hash)
            frame_paths.append(str(output_frame_path))
        else:
            frame_hash = extract_frame(video_path, timestamp, output_frame_path)
            if frame_hash is not None:
                frame_hashes.append(frame_hash)
                frame_paths.append(str(output_frame_path))

    # Controlla se ci sono hash non validi
    if len(frame_hashes) < 3:
        logging.warning(f"Errore: uno o più hash dei frame sono None per {video_path}.")
        return False

    combined_hash = combine_hashes_mode(*frame_hashes)  # Combina gli hash
    insert_video(resolution, size, duration, str(video_path), str(combined_hash), *frame_paths)  # Passa anche i percorsi dei frame

    return True

def process_video(video_path: Path) -> None:
    """Processa il video per estrarre e controllare i frame.""" 
    sanitized_video_name = sanitize_filename(video_path.name)
    sanitized_video_path = video_path.parent / sanitized_video_name

    # Rinomina il video se necessario
    if sanitized_video_name != video_path.name:
        video_path.rename(sanitized_video_path)
        video_path = sanitized_video_path

    # Controlla se i frame esistono già
    frames_folder = Path(FRAMES_DIR) / sanitized_video_name
    if frames_folder.exists() and any(frames_folder.glob("*.jpg")):
        extract_video_info(video_path)  # Inserisci le informazioni del video
    else:
        # Se non ci sono frame esistenti, procedi all'estrazione
        extract_video_info(video_path)

def process_videos_in_directory(directory: str) -> None:
    """Processa tutti i video in una cartella e nelle sue sottocartelle usando multithreading.""" 
    video_extensions = (
        '.mp4', '.avi', '.mov', '.mkv', '.wmv', 
        '.flv', '.webm', '.mpeg', '.mpg', '.m4v', '.3gp'
    )
    
    if not Path(directory).exists():
        logging.error(f"La directory specificata non esiste: {directory}")
        return
    
    video_files = list(Path(directory).rglob('*'))
    total_files = sum(1 for file in video_files if file.suffix.lower() in video_extensions)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        start_time = time.time()  # Inizia il timer totale
        with tqdm(total=total_files, desc="Elaborazione video", unit="file") as pbar:
            for video_path in video_files:
                if video_path.suffix.lower() in video_extensions:
                    futures.append(executor.submit(process_video, video_path))

            for processed_files, future in enumerate(futures, start=1):
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Errore nel processare il video {video_path}: {e}")

                # Calcola il tempo rimanente e il tempo totale trascorso
                #elapsed_time = time.time() - start_time
                #time_remaining = (total_files - processed_files) * (elapsed_time / processed_files) if processed_files > 0 else 0
                #elapsed_time_str = format_duration(elapsed_time)
                #logging.info(f"File processati: {processed_files}/{total_files}, Tempo rimanente stimato: {format_duration(time_remaining)}, Tempo trascorso: {elapsed_time_str}")

                pbar.update(1)

    logging.info("Elaborazione video completata.")
