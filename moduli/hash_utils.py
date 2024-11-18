import imagehash
import numpy as np
from PIL import Image

def combine_hashes_mode(*hashes):
    """
    Combina più hash di immagini utilizzando la modalità per ciascun bit.
    Controlla anche se un'immagine è completamente nera o bianca.

    Parameters:
    *hashes (ImageHash): Gli oggetti hash da combinare.

    Returns:
    ImageHash: Un nuovo hash combinato secondo la modalità dei bit.

    Raises:
    ValueError: Se gli hash non hanno la stessa dimensione o se nessun hash è fornito.
    TypeError: Se un input non è un oggetto ImageHash.
    """
    
    # Controlla che ci siano hash forniti
    if not hashes:
        raise ValueError("Almeno un hash deve essere fornito per la combinazione.")

    # Controlla che tutti gli hash siano oggetti ImageHash
    if not all(isinstance(h, imagehash.ImageHash) for h in hashes):
        raise TypeError("Tutti gli input devono essere oggetti ImageHash.")

    # Controlla che tutti gli hash abbiano la stessa dimensione
    hash_shape = hashes[0].hash.shape
    if not all(h.hash.shape == hash_shape for h in hashes):
        raise ValueError("Tutti gli hash devono avere la stessa dimensione.")

    # Converte gli hash in un array di interi
    hash_arrays = np.array([h.hash.flatten() for h in hashes], dtype=int)

    # Verifica se uno degli hash è di un'immagine nera o bianca
    for idx, img_hash in enumerate(hashes):
        if np.all(img_hash.hash == 0):
            print(f"Hash per il frame {idx + 1} è Nera.")
        elif np.all(img_hash.hash == 1):
            print(f"Hash per il frame {idx + 1} è Bianca.")

    # Calcola la modalità dei bit usando un approccio più veloce
    combined_bits = (np.mean(hash_arrays, axis=0) > 0.5).astype(int)

    # Ricrea l'hash come ImageHash nella forma originale
    combined_hash = imagehash.ImageHash(combined_bits.reshape(hash_shape))
    return combined_hash


def calculate_phash(image):
    """Calcola l'hash perceptuale dell'immagine."""
    return imagehash.phash(image)


def calculate_dhash(image):
    """Calcola l'hash differenziale dell'immagine."""
    return imagehash.dhash(image)


def calculate_ahash(image):
    """Calcola l'hash medio dell'immagine."""
    return imagehash.average_hash(image)


def hamming_distance(hash1, hash2):
    """Calcola la distanza Hamming tra due hash."""
    int_hash1 = int(hash1, 16)
    int_hash2 = int(hash2, 16)
    return bin(int_hash1 ^ int_hash2).count('1')


def filter_similar_images(reference_hash, hash_list, threshold):
    """Restituisce una lista di hash simili a riferimento."""
    return [h for h in hash_list if hamming_distance(reference_hash, h) < threshold]


def visualize_similar_images(similar_images):
    """Visualizza le immagini simili."""
    for img in similar_images:
        img.show()  # o usa una libreria di visualizzazione per creare un collage


def is_unique_hash(new_hash, existing_hashes):
    """Controlla se l'hash è unico rispetto a un elenco di hash esistenti."""
    return all(hamming_distance(new_hash, h) > 8 for h in existing_hashes)


def image_to_hash(image_path):
    """Carica un'immagine e restituisce il suo hash."""
    image = Image.open(image_path)
    return calculate_phash(image)
