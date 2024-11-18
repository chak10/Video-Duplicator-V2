import json
import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from moduli.database_manager import delete_video  # Presupponendo che ci sia una funzione per cancellare i video dal database
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


class VideoComparerApp(tk.Tk):
    def __init__(self, similarities_file):
        super().__init__()
        self.similarities_file = similarities_file
        
        # Controlla se il file JSON esiste e non è vuoto
        if not os.path.exists(self.similarities_file) or os.path.getsize(self.similarities_file) == 0:
            messagebox.showerror("Errore", f"Il file {self.similarities_file} non esiste o è vuoto.")
            self.quit()
            return
        
        self.similarities = self.load_similarities()
        self.current_index = 0
        
        self.title("Confronto Video")
        width = int(self.winfo_screenwidth())
        height = int(self.winfo_screenheight()*0.80)
        self.geometry(f"{width}x{height}+{0}+{0}")
        
        # Colore di sfondo scuro
        self.configure(bg='#121212')
        
        # Configura la griglia
        self.configure_grid()

        # Frame per la navigazione e i pulsanti principali
        self.nav_frame = tk.Frame(self, bg='#121212')
        self.nav_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky="ew")

        # Label per il conteggio dei file rimanenti
        self.remaining_files_label = tk.Label(self.nav_frame, text="", font=("Arial", 14), bg='#121212', fg='#FFFFFF')
        self.remaining_files_label.pack(pady=10)

        # Mostra il primo confronto
        self.show_comparison()

    def configure_grid(self):
        """Configura il layout della finestra per adattarsi."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

    def load_similarities(self):
        with open(self.similarities_file, 'r') as file:
            return json.load(file)

    def show_comparison(self):
        """Mostra i dettagli e i frame dei due video correnti."""
        if self.current_index >= len(self.similarities):
            messagebox.showinfo("Fine", "Non ci sono più video da confrontare.")
            self.destroy()  # Chiude l'intera finestra
            return

        similarity = self.similarities[self.current_index]
        video1_info = similarity["video1"]
        video2_info = similarity["video2"]
        hamming_distance = similarity["hamming_distance"]
        
        # Mostra il nome dei video come titolo
        n1 = Path(video1_info['video_path'])
        video1_name =  n1.name  # Estrae il nome del file dal percorso
        n2 = Path(video2_info['video_path'])
        video2_name = n2.name  # Estrae il nome del file dal percorso

        # Frame per i video e le informazioni in due colonne
        self.display_video_column(video1_info, 0, video1_name)  # Passa il nome del video 1
        self.display_video_column(video2_info, 1, video2_name)  # Passa il nome del video 2
        self.display_navigation(hamming_distance)

        # Aggiorna il conteggio dei file rimanenti
        remaining_files = len(self.similarities) - self.current_index - 1
        self.remaining_files_label.config(text=f"File rimanenti: {remaining_files}")

    def display_video_column(self, video_info, column, title):
        """Mostra i frame e le informazioni di un video in una colonna specifica."""
        column_frame = tk.Frame(self, bg="#121212")
        column_frame.grid(row=0, column=column, sticky="nsew", padx=10, pady=10)
        self.grid_columnconfigure(column, weight=1)

        # Titolo centrato
        tk.Label(column_frame, text=title, font=("Arial", 14, "bold"), bg="#121212", fg="#FFFFFF").pack(pady=5)

        # Frame per mostrare i 3 frame del video
        frames_frame = tk.Frame(column_frame, bg="#121212")
        frames_frame.pack(pady=10)

        # Mantiene i percorsi e le label per visualizzare i frame
        self.frames_data = []
        for frame_path in video_info["frame_paths"]:
            img_label = tk.Label(frames_frame, bg="#121212")
            #img_label.pack(pady=5)
            img_label.pack(side="left", padx=5)  # Usa side="left" per disporre orizzontalmente
            self.frames_data.append((frame_path, img_label))
        
        # Carica e visualizza le immagini con dimensioni fisse
        self.update_frame_images()
        
        # Informazioni centrate
        info_label = tk.Label(column_frame, text=f"Path: {video_info['video_path']}", wraplength=400, anchor="center", bg="#121212", fg="#FFFFFF",font=("Arial", 14))
        info_label.pack(fill="x", pady=5)

        detail_label = tk.Label(column_frame, text=f"Risoluzione: {video_info['resolution']}, "
                                                f"Dimensione: {video_info['size']}, Durata: {video_info['duration']}",
                                bg="#121212", fg="#FFFFFF", font=("Arial", 14))
        detail_label.pack(anchor="center", pady=5)

    def update_frame_images(self):
        """Aggiorna le immagini dei frame."""
        fixed_size = (300, 300)  # Dimensioni fisse per le immagini

        for frame_path, img_label in self.frames_data:
            if not os.path.exists(frame_path):
                print(f"Il file non esiste: {frame_path}")
                continue  # Salta se il file non esiste

            try:
                image = Image.open(frame_path)

                # Controllo se l'immagine ha dimensioni valide
                if image.size[0] <= 0 or image.size[1] <= 0:
                    print(f"L'immagine ha dimensioni non valide: {frame_path}")
                    continue  # Salta se l'immagine ha dimensioni non valide

                image = image.resize(fixed_size, Image.LANCZOS)  # Usa LANCZOS per un ridimensionamento di alta qualità
                image_tk = ImageTk.PhotoImage(image)
                img_label.config(image=image_tk, bg='#121212')
                img_label.image = image_tk  # Mantiene un riferimento per evitare la garbage collection
            except Exception as e:
                print(f"Errore nel caricamento dell'immagine {frame_path}: {e}")

    def display_navigation(self, hamming_distance):
        """Crea i pulsanti di navigazione e mostra la distanza Hamming."""
        for widget in self.nav_frame.winfo_children():
            if widget != self.remaining_files_label:
                widget.destroy()

        tk.Label(self.nav_frame, text=f"Distanza Hamming: {hamming_distance}", bg='#121212', fg='#FFFFFF', font=("Arial", 14)).pack()

        # Pulsanti per eliminare uno dei due video
        button_frame = tk.Frame(self.nav_frame, bg='#121212')
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Elimina Video 1", command=lambda: self.delete_video(self.similarities[self.current_index]["video1"]), bg='#cb3234', fg='#FFFFFF', width=15, height=2, font=("Arial", 14)).grid(row=0, column=0, padx=10)
        tk.Button(button_frame, text="Elimina Video 2", command=lambda: self.delete_video(self.similarities[self.current_index]["video2"]), bg='#cb3234', fg='#FFFFFF', width=15, height=2, font=("Arial", 14)).grid(row=0, column=1, padx=10)
        tk.Button(button_frame, text="Salta", command=self.skip_comparison, bg='#337AB7', fg='#FFFFFF', width=15, height=2, font=("Arial", 14)).grid(row=0, column=2, padx=10)

    def delete_video(self, video_info):
        """Elimina il video selezionato e i relativi frame dalla directory e dal database, e aggiorna il file JSON."""
        video_path = video_info["video_path"]
        video_id = video_info["id"]
        frames_directory = os.path.join("frames", os.path.splitext(os.path.basename(video_path))[0])

        if messagebox.askyesno("Conferma Eliminazione", f"Sei sicuro di voler eliminare il video: {video_path}?"):
            try:
                os.remove(video_path)
                if os.path.exists(frames_directory):
                    import shutil
                    shutil.rmtree(frames_directory)
                
                delete_video(video_id)
                self.update_similarities_json(video_id)

                # Aggiorna l'indice corrente se necessario
                if self.current_index >= len(self.similarities):
                    self.current_index = len(self.similarities) - 1
                
                # Se non ci sono più video, chiudi l'app
                if self.current_index < 0:
                    messagebox.showinfo("Eliminazione", "Non ci sono più video da confrontare.")
                    self.destroy()
                    return

                #messagebox.showinfo("Eliminazione", "Video eliminato con successo.")
                self.show_comparison()
            except Exception as e:
                messagebox.showerror("Errore", f"Errore durante l'eliminazione: {e}")

    def update_similarities_json(self, video_id):
        """Aggiorna il file JSON rimuovendo le somiglianze associate al video eliminato."""
        self.similarities = [sim for sim in self.similarities if sim["video1"]["id"] != video_id and sim["video2"]["id"] != video_id]
        with open(self.similarities_file, 'w') as file:
            json.dump(self.similarities, file, indent=4)

    def skip_comparison(self):
        """Salta il confronto corrente e passa al successivo."""
        self.current_index += 1
        self.show_comparison()

if __name__ == "__main__":
    app = VideoComparerApp(JSON_FILE)
    app.mainloop()
