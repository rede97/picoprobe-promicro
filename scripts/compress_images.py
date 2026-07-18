"""Resize images in hardware/picture/ to 1080P (max 1920px long edge) and recompress as JPEG.

Usage: python scripts/compress_images.py
Overwrites files in place.
"""

from pathlib import Path

from PIL import Image

MAX_EDGE = 1920  # 1080P: 1920x1080
QUALITY = 85

src_dir = Path(__file__).resolve().parent.parent / "hardware" / "picture"

for path in sorted(src_dir.glob("*")):
    if path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
        continue
    img = Image.open(path)
    w, h = img.size
    scale = MAX_EDGE / max(w, h)
    if scale < 1.0:
        new_size = (round(w * scale), round(h * scale))
        img = img.resize(new_size, Image.LANCZOS)
    img = img.convert("RGB")
    img.save(path, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    print(f"{path.name}: {w}x{h} -> {img.size[0]}x{img.size[1]}, {path.stat().st_size // 1024} KB")
