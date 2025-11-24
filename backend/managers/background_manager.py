import json
import re
import os
from pathlib import Path
from datetime import datetime

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent # /backend/
CSS_FILE_PATH = BASE_DIR / "static" / "index.css"
STATIC_IMAGES_DIR = BASE_DIR / "static" / "assets" / "images"

def path_url_to_fs(path_url: str) -> Path | None:
    if not path_url:
        return None
    cleaned = path_url.lstrip("/")
    fs_path = BASE_DIR / cleaned  
    return fs_path

def parse_slots_from_css_json(css_path: Path):
    if not css_path.exists():
        return []
    try:
        content = css_path.read_text(encoding="utf-8")
    except Exception:
        return []
    m = re.search(r"/\*\s*MULTISLOT:\s*(\[\s*[\s\S]*?\])\s*\*/", content, re.DOTALL | re.IGNORECASE)
    if not m:
        return []
    try:
        return json.loads(m.group(1))
    except Exception:
        return []

def write_slots_to_css_json(css_path: Path, slots):
    block = "/* MULTISLOT:\n" + json.dumps(slots, indent=2) + "\n*/"
    if not css_path.exists():
        css_path.write_text(block + "\n", encoding="utf-8")
        return
    content = css_path.read_text(encoding="utf-8")
    updated, count = re.subn(
        r"/\*\s*MULTISLOT:\s*\[[\s\S]*?\]\s*\*/",
        block,
        content,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if count:
        css_path.write_text(updated, encoding="utf-8")
    else:
        with open(css_path, "a", encoding="utf-8") as f:
            f.write("\n\n" + block + "\n")

def list_images():
    """List all images in the static images directory."""
    if not STATIC_IMAGES_DIR.exists():
        return []
    
    images = []
    for f in STATIC_IMAGES_DIR.iterdir():
        if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
            images.append({
                "name": f.name,
                "url": f"/static/assets/images/{f.name}",
                "size": f.stat().st_size,
                "date": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
    return images
