from extractor import process_videos_in_directory
from database_manager import create_table
import logging
from compare import compare_hashes
from config import DISTANCE_THRESHOLD
from config import DIR_TO_PROCESS

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
