from moduli.extractor import process_videos_in_directory
from moduli.database_manager import create_table
import logging
from moduli.compare import compare_hashes
import configparser
from pathlib import Path

# Load configuration
config = configparser.ConfigParser()

# Check if the config file exists
config_file = Path('config.ini')
if not config_file.exists():
    raise FileNotFoundError(f"Il file di configurazione 'config.ini' non è stato trovato.")

config.read(config_file)

# Load directory and threshold values
DIR_TO_PROCESS = config['Paths']['DIR_TO_PROCESS']
DISTANCE_THRESHOLD = int(config['Settings']['DISTANCE_THRESHOLD'])

# Print the loaded values for verification
print(f"DIRECTORY TO PROCESS: {DIR_TO_PROCESS}")
print(f"DISTANCE THRESHOLD: {DISTANCE_THRESHOLD}")

# Check if the directory exists
if not Path(DIR_TO_PROCESS).exists() or not Path(DIR_TO_PROCESS).is_dir():
    print(f"Attenzione: La directory '{DIR_TO_PROCESS}' non esiste o non è una directory valida.")
else:
    print(f"La directory '{DIR_TO_PROCESS}' esiste e sarà elaborata.")

# Check if the distance threshold is a valid integer
if not isinstance(DISTANCE_THRESHOLD, int):
    print("Attenzione: DISTANCE_THRESHOLD non è un numero intero valido.")
else:
    print(f"Il valore di DISTANCE_THRESHOLD è valido: {DISTANCE_THRESHOLD}")

# Configurazione del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Funzione principale per creare la tabella nel database e processare i video in una directory specificata."""
    try:
        create_table()  # Crea la tabella nel database se non esiste già
        

        logging.info(f"Inizio dell'elaborazione dei video nella directory: {DIR_TO_PROCESS}")
        process_videos_in_directory(DIR_TO_PROCESS)
        logging.info("Elaborazione completata.")

        # Confronta gli hash dei video
        compare_hashes(DISTANCE_THRESHOLD)

    except Exception as e:
        logging.error(f"Si è verificato un errore durante l'elaborazione: {e}")

if __name__ == "__main__":
    main()
