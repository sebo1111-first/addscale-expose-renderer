"""Füllt die Exposé-Variablen-Vorlage: {{tags}} -> Text, Fotos -> Design-Slots."""
import io, zipfile
from PIL import Image

# Foto-Slots der Vorlage in numerischer Reihenfolge (Titel/Galerie kommen zuerst)
PHOTO_SLOTS = [
    "image1.jpeg", "image3.jpeg", "image4.jpeg", "image5.jpeg", "image6.jpeg",
    "image7.jpeg", "image8.jpeg", "image9.jpeg", "image10.jpeg", "image11.jpeg",
    "image13.jpeg", "image14.jpeg", "image15.jpeg", "image16.jpeg", "image17.jpeg",
    "image18.jpeg", "image21.jpeg",
]

def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def _crop_resize(img, w, h):
    """Center-Crop auf Ziel-Seitenverhältnis, dann auf Slot-Größe skalieren."""
    img = img.convert("RGB")
    sw, sh = img.size
    target = w / h
    if sw / sh > target:            # zu breit -> Seiten beschneiden
        nw = int(sh * target)
        img = img.crop(((sw - nw) // 2, 0, (sw - nw) // 2 + nw, sh))
    else:                            # zu hoch -> oben/unten beschneiden
        nh = int(sw / target)
        img = img.crop((0, (sh - nh) // 2, sw, (sh - nh) // 2 + nh))
    return img.resize((w, h), Image.LANCZOS)

def fill(docx_bytes, variables, photos=None):
    """variables: {tag: wert}; photos: [bytes,...] in Slot-Reihenfolge. -> gefüllte docx-bytes"""
    zin = zipfile.ZipFile(io.BytesIO(docx_bytes))

    # 1) Text: {{tag}} -> Wert
    xml = zin.read("word/document.xml").decode("utf-8")
    for key, val in (variables or {}).items():
        xml = xml.replace("{{" + key + "}}", _esc(val))

    # 2) Fotos: Slot-Bilder ersetzen (auf Original-Slotgröße skaliert -> Design bleibt)
    new_media = {}
    for slot, photo in zip(PHOTO_SLOTS, photos or []):
        try:
            orig = Image.open(io.BytesIO(zin.read("word/media/" + slot)))
            w, h = orig.size
            buf = io.BytesIO()
            _crop_resize(Image.open(io.BytesIO(photo)), w, h).save(buf, "JPEG", quality=85)
            new_media["word/media/" + slot] = buf.getvalue()
        except Exception:
            pass  # defektes Foto -> Slot bleibt, Rest läuft weiter

    # 3) neu verpacken
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.namelist():
            if item == "word/document.xml":
                zout.writestr(item, xml.encode("utf-8"))
            elif item in new_media:
                zout.writestr(item, new_media[item])
            else:
                zout.writestr(item, zin.read(item))
    return out.getvalue()
