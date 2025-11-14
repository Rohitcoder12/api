import re
from typing import List

def fmt_size(size_bytes: int) -> str:
    if size_bytes is None: return "N/A"
    try: size_bytes = int(size_bytes)
    except (ValueError, TypeError): return "N/A"
    if size_bytes >= 1024**3: return f"{size_bytes / 1024**3:.2f} GB"
    if size_bytes >= 1024**2: return f"{size_bytes / 1024**2:.2f} MB"
    if size_bytes >= 1024: return f"{size_bytes / 1024:.2f} KB"
    return f"{size_bytes} B"

def get_urls_from_string(string: str) -> List[str] | None:
    if not string: return None
    return re.findall(r"(?:https?://|www\.)[^\s]+", string)

def determine_file_type(filename: str):
    lower_filename = filename.lower()
    video_formats = ('.mp4', '.mkv', '.avi', '.mov', '.webm', '.ts', '.m2ts')
    if lower_filename.endswith(('.jpg', '.jpeg', '.png')):
        return 'photo'
    if lower_filename.endswith(video_formats):
        return 'video'
    return 'document'
