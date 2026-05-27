"""Convert all menu_pictures to WebP at consistent quality and size."""
import pathlib
from PIL import Image

SRC = pathlib.Path(__file__).parent.parent / "frontend" / "menu_pictures"
DST = pathlib.Path(__file__).parent.parent / "frontend" / "menu_pictures" / "compressed"
MAX_W, MAX_H = 800, 600
QUALITY = 82

DST.mkdir(exist_ok=True)

MAPPING = {
    "garlic-wings":       "Garlic Butter Chicken Wings.avif",
    "shrimp-tempura":     "Shrimp Tempura.avif",
    "gyoza":              "Fried Gyoza.jpg",
    "veggie-rolls":       "Veggie Spring Rolls.avif",
    "fried-calamari":     "Fried_Calamari.png",
    "onion-rings":        "Onion_Rings.png",
    "garlic-shrimp":      "Garlic Butter Shrimp.avif",
    "bbq-chicken":        "BBQ Chicken.avif",
    "kalbi":              "Kalbi.avif",
    "salted-egg-shrimp":  "Salted Egg Yolk Shrimp.jpg",
    "pork-chop":          "Pork Chop.avif",
    "salt-pepper-shrimp": "Salt & Pepper Shrimp.avif",
    "steak":              "Steak.avif",
    "shaking-beef":       "Shaking_Beef.png",
    "fish-fillet":        "Garlic Butter Fish Fillet.jpg",
    "fried-rice":         "Fried Rice.avif",
}

for slug, src_name in MAPPING.items():
    src_path = SRC / src_name
    if not src_path.exists():
        print(f"MISSING: {src_name}")
        continue
    img = Image.open(src_path).convert("RGB")
    img.thumbnail((MAX_W, MAX_H), Image.LANCZOS)
    out = DST / f"{slug}.webp"
    img.save(out, "WEBP", quality=QUALITY, method=6)
    src_kb = src_path.stat().st_size // 1024
    out_kb = out.stat().st_size // 1024
    print(f"{slug}: {src_kb} KB -> {out_kb} KB")
