import json
import logging
from database_manager import fetch_videos
from config import DISTANCE_THRESHOLD
from utils import format_size, format_duration
from hash_utils import hamming_distance
from tqdm import tqdm

# Configurazione del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename="video_comparison.log")

def compare_video_pair(video1, video2, distance_threshold):
    """Confronta una coppia di video e restituisce un dizionario con i dettagli se la somiglianza è sotto la soglia."""
    id1, resolution1, size1, duration1, video_path1, combined_hash1, *frame_paths1 = video1
    id2, resolution2, size2, duration2, video_path2, combined_hash2, *frame_paths2 = video2

    # Calcola la distanza Hamming tra gli hash combinati
    try:
        distance = hamming_distance(combined_hash1, combined_hash2)
    except Exception as e:
        logging.warning(f"Errore nel calcolo della distanza Hamming tra {video_path1} e {video_path2}: {e}")
        return None

    if distance < distance_threshold:
        return {
            "video1": {
                "id": id1,
                "video_path": video_path1,
                "resolution": resolution1,
                "size": format_size(size1),
                "duration": format_duration(duration1),
                "frame_paths": frame_paths1,
                "combined_hash": str(combined_hash1)
            },
            "video2": {
                "id": id2,
                "video_path": video_path2,
                "resolution": resolution2,
                "size": format_size(size2),
                "duration": format_duration(duration2),
                "frame_paths": frame_paths2,
                "combined_hash": str(combined_hash2)
            },
            "hamming_distance": distance
        }
    return None

def compare_hashes(distance_threshold: int) -> None:
    """Confronta gli hash dei frame di tutti i video e genera un file JSON con i risultati di video simili."""
    try:
        videos = fetch_videos()
    except Exception as e:
        logging.error(f"Errore nel recupero dei video dal database: {e}")
        return

    similarities = []
    total_comparisons = (len(videos) * (len(videos) - 1)) // 2

    # Iterazione senza parallelismo
    with tqdm(total=total_comparisons, desc="Confronto dei video", unit="confronti") as pbar:
        for i in range(len(videos)):
            for j in range(i + 1, len(videos)):
                result = compare_video_pair(videos[i], videos[j], distance_threshold)
                if result:
                    similarities.append(result)
                pbar.update(1)

    # Salva i risultati in un file JSON
    try:
        with open('similarities.json', 'w') as json_file:
            json.dump(similarities, json_file, indent=4)
        logging.info("File 'similarities.json' creato con successo.")
    except Exception as e:
        logging.error(f"Errore durante la scrittura del file similarities.json: {e}")

