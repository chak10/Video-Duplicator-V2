import json
import logging
from moduli.database_manager import fetch_videos
from moduli.utils import format_size, format_duration
from moduli.hash_utils import hamming_distance
from tqdm import tqdm
import hashlib
import configparser
from pathlib import Path

# Load configuration
config = configparser.ConfigParser()

# Check if the config file exists
config_file = Path('config.ini')
if not config_file.exists():
    raise FileNotFoundError(f"Il file di configurazione 'config.ini' non è stato trovato.")

config.read(config_file)

# Load directory to process
try:
    DIR_TO_PROCESS = config['Paths']['DIR_TO_PROCESS']
except KeyError:
    raise KeyError("La configurazione 'DIR_TO_PROCESS' non è stata trovata nel file 'config.ini'.")

# Calcola il nome del file del database usando un hash Blake2b a 128 bit, se non è definito nel file di configurazione
DB_FILE = config['Database'].get('DB_FILE', None)
JSON_FILE = "similarities.json"
if not DB_FILE:
    # Calcola hash Blake2b con output di 128 bit per creare il nome del DB
    JSON_FILE = hashlib.blake2b(DIR_TO_PROCESS.encode(), digest_size=16).hexdigest() + '.json'

# Crea la directory per il database se non esiste
db_path = Path("database")
db_path.mkdir(parents=True, exist_ok=True)

# Costruisci il percorso completo del file del database

JSON_FILE = db_path / JSON_FILE
# Converte il nome del file del database in un percorso assoluto e stampa
JSON_FILE = str(Path(JSON_FILE).resolve())
print(f"JSON_FILE: {JSON_FILE}")

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
        with open(JSON_FILE, 'w') as json_file:
            json.dump(similarities, json_file, indent=4)
        logging.info(f"File {JSON_FILE} creato con successo.")
    except Exception as e:
        logging.error(f"Errore durante la scrittura del file {JSON_FILE}: {e}")

