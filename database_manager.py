import sqlite3
import os
import configparser
from pathlib import Path

# Load configuration
config = configparser.ConfigParser()

# Check if the config file exists
config_file = Path('config.ini')
if not config_file.exists():
    raise FileNotFoundError(f"Il file di configurazione 'config.ini' non è stato trovato.")

config.read(config_file)

# Load database file path
DB_FILE = config['Database']['DB_FILE']

# Print the loaded DB file path for verification
print(f"DB_FILE: {DB_FILE}")


def connect_db():
    """Crea una connessione al database SQLite."""
    return sqlite3.connect(DB_FILE)

def create_table():
    """Crea la tabella 'videos' nel database se non esiste già."""
    with connect_db() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resolution TEXT,
                size INTEGER,
                duration REAL,
                video_path TEXT UNIQUE,
                combined_hash TEXT,
                frame_path1 TEXT,
                frame_path2 TEXT,
                frame_path3 TEXT
            )
        """
        )
        conn.commit()

def video_exists_in_db(video_path):
    """Controlla se un video esiste già nel database in base al percorso."""
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM videos WHERE video_path = ?", (video_path,))
        return cursor.fetchone() is not None

def insert_video(resolution, size, duration, video_path, combined_hash, frame_path1, frame_path2, frame_path3):
    """Inserisce le informazioni del video nel database, inclusi i percorsi dei frame."""
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO videos (resolution, size, duration, video_path, combined_hash, frame_path1, frame_path2, frame_path3)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (resolution, size, duration, video_path, combined_hash, frame_path1, frame_path2, frame_path3),
        )
        conn.commit()

def clean_database():
    """Pulisce i dati nel database (rimuove tutti i record)."""
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM videos")
        conn.commit()

def optimize_database():
    """Ottimizza il database rimuovendo spazio non utilizzato."""
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("VACUUM")
        conn.commit()

def fetch_videos():
    """Recupera tutti i record dei video dal database."""
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM videos")
        return cursor.fetchall()

def fetch_video_by_id(video_id):
    """Recupera un video specifico dal database in base all'ID."""
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
        return cursor.fetchone()

def delete_video(video_id):
    """Elimina un video dal database in base all'ID."""
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))
        conn.commit()
