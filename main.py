from extractor import process_videos_in_directory
from database_manager import create_table
import logging
from compare import compare_hashes
from config import DISTANCE_THRESHOLD

# Configurazione del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Funzione principale per creare la tabella nel database e processare i video in una directory specificata."""
    try:
        create_table()  # Crea la tabella nel database se non esiste già
        directory_to_process = "D:/Download/Test"  # Sostituisci con il percorso della tua cartella

        logging.info(f"Inizio dell'elaborazione dei video nella directory: {directory_to_process}")
        process_videos_in_directory(directory_to_process)
        logging.info("Elaborazione completata.")

        # Confronta gli hash dei video
        compare_hashes(DISTANCE_THRESHOLD)

    except Exception as e:
        logging.error(f"Si è verificato un errore durante l'elaborazione: {e}")

if __name__ == "__main__":
    main()
