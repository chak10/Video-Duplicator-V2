import subprocess
import re
import imagehash
import logging
import io
import time
from PIL import Image
from pathlib import Path
from tqdm import tqdm
from config import FFMPEG_PATH, FFPROBE_PATH, FRAMES_DIR
from database_manager import insert_video, video_exists_in_db
from concurrent.futures import ThreadPoolExecutor
from hash_utils import combine_hashes_mode  # Importa la funzione per combinare gli hash
from utils import format_duration

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

def extract_frame(video_path: Path, timestamp: float, output_frame_path: Path) -> imagehash.ImageHash:
    """Estrae un frame dal video a un dato timestamp e calcola l'hash senza caricarlo in memoria."""
    command = [
        FFMPEG_PATH, 
        '-ss', str(timestamp), 
        '-i', str(video_path), 
        '-vframes', '1', 
        '-f', 'image2pipe', 
        '-vcodec', 'png', 
        '-y', 'pipe:1'
    ]

    try:
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as proc:
            image_data = proc.stdout.read()

        pil_image = Image.open(io.BytesIO(image_data))  # Apri l'immagine da byte
        phash = imagehash.phash(pil_image)  # Calcola l'hash

        # Salva l'immagine nel file di output
        with open(output_frame_path, "wb") as f:
            f.write(image_data)

        return phash  # Restituisci l'hash calcolato

    except subprocess.CalledProcessError as e:
        logging.error(f"Errore nell'estrarre il frame {output_frame_path}: {e}")
        return None

def extract_video_info(video_path: Path) -> bool:
    """Estrae informazioni dal video e le inserisce nel database."""
    if video_exists_in_db(str(video_path)):
        logging.info(f"Video già presente nel database: {video_path}")
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
    logging.info(f"Informazioni del video inserite nel database: {video_path}")

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
        logging.info(f"I frame esistono già per il video: {video_path}. Procedendo con l'inserimento nel database.")
        extract_video_info(video_path)  # Inserisci le informazioni del video
    else:
        # Se non ci sono frame esistenti, procedi all'estrazione
        logging.info(f"Elaborazione del video: {video_path}")
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
                future.result()  # Attendi il completamento del task

                # Calcola il numero di file rimanenti
                remaining_files = total_files - processed_files
                estimated_time_per_video = (time.time() - start_time) / processed_files if processed_files > 0 else 0
                time_remaining = remaining_files * estimated_time_per_video
                elapsed_time = time.time() - start_time  # Tempo trascorso
                #time_remaining_hum = format_duration(time_remaining)
                #elapsed_time_hum = format_duration(elapsed_time)
                # Aggiorna la barra di stato
                pbar.update(1)
                pbar.set_postfix({
                    'File elaborati': processed_files,
                    'File rimanenti': remaining_files,
                    'Tempo stimato rimanente': time_remaining,
                    'Tempo trascorso': elapsed_time
                })

    print()  # Stampa una nuova riga dopo il completamento
