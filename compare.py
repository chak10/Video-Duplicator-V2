import json
from database_manager import fetch_videos
from config import DISTANCE_THRESHOLD
from utils import format_size
from utils import format_duration
from hash_utils import hamming_distance


def compare_hashes(distance_threshold):
    """Confronta gli hash dei frame di tutti i video e genera un file JSON con i risultati."""
    videos = fetch_videos()
    similarities = []

    for i, video1 in enumerate(videos):
        id1, resolution1, size1, duration1, video_path1, combined_hash1, *frame_paths1 = video1

        for j, video2 in enumerate(videos):
            if i >= j:
                continue  # Evita confronti duplicati e se stesso

            id2, resolution2, size2, duration2, video_path2, combined_hash2, *frame_paths2 = video2
            
            # Calcola la distanza Hamming tra gli hash combinati
            distance = hamming_distance(combined_hash1, combined_hash2)
            
            if distance < distance_threshold:
                similarity = {
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
                similarities.append(similarity)

    # Salva i risultati in un file JSON
    with open('similarities.json', 'w') as json_file:
        json.dump(similarities, json_file, indent=4)
