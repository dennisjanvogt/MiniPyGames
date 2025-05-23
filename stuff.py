import os
from PIL import Image, ImageDraw, ImageFont

# Verzeichnis für Assets anlegen

# Verzeichnis für Assets anlegen
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

# Definition der Platzhalter-Assets
assets = {
    "kart.png": {"size": (64, 64), "color": (200, 0, 0), "text": "KART"},
    "item_box.png": {"size": (48, 48), "color": (255, 215, 0), "text": "?"},
    "banana.png": {"size": (32, 32), "color": (255, 255, 0), "text": ""},
    "banana_obstacle.png": {"size": (32, 32), "color": (255, 255, 0), "text": ""},
    "red_shell.png": {"size": (32, 32), "color": (255, 0, 0), "text": ""},
    "shell.png": {"size": (32, 32), "color": (200, 0, 200), "text": ""},
    "mushroom.png": {"size": (32, 32), "color": (255, 0, 255), "text": ""},
}

# Funktion zum Erzeugen eines einfachen Platzhalter-Bilds
for filename, props in assets.items():
    size = props["size"]
    color = props["color"]
    text = props["text"]

    # RGBA-Bild mit Transparenz
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Ellipse als Form
    draw.ellipse([0, 0, size[0], size[1]], fill=color)

    # Optional Text zentriert
    if text:
        font = ImageFont.load_default()
        # Berechne Textgröße
        w, h = font.getsize(text)
        draw.text(
            ((size[0] - w) // 2, (size[1] - h) // 2), text, fill="black", font=font
        )

    img.save(os.path.join(ASSETS_DIR, filename))

# Track und Track-Maske erzeugen
track_size = (1024, 768)
margin = 100

# Track (grüner Hintergrund + grauer Streckenbelag)
track_img = Image.new("RGB", track_size, (34, 139, 34))
draw = ImageDraw.Draw(track_img)
draw.ellipse(
    [margin, margin, track_size[0] - margin, track_size[1] - margin],
    fill=(128, 128, 128),
)
track_img.save(os.path.join(ASSETS_DIR, "track.png"))

# Track-Maske (weiße Strecke, schwarzer Rest)
mask_img = Image.new("L", track_size, 0)
draw = ImageDraw.Draw(mask_img)
draw.ellipse([margin, margin, track_size[0] - margin, track_size[1] - margin], fill=255)
mask_img.save(os.path.join(ASSETS_DIR, "track_mask.png"))
