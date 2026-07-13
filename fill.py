"""Füllt die Exposé-Variablen-Vorlage: {{tags}} -> Text, Fotos -> Design-Slots."""
import io, zipfile
from PIL import Image

# Foto-Slots in VISUELLER Reihenfolge (siehe Slot-Karte in NEXT_STEPS.md).
# Galerie-Kacheln 01-06 sind seit dem Dedup-Fix eigene Dateien (image22-25 = Kopien).
# Leerer Eintrag ("" / None) im photos-Array => Slot wird übersprungen.
PHOTO_SLOTS = [
    "image1.jpeg",   # 1  Titelbild (Hexagon-Mosaik, vorne + hinten)
    "image3.jpeg",   # 2  Inhaltsseite Bildspalte
    "image4.jpeg",   # 3  Inhaltsseite Hexagon-Akzente (3x gleiches Bild)
    "image5.jpeg",   # 4  Lage groß links
    "image6.jpeg",   # 5  Beschreibung Hexagon links
    "image7.jpeg",   # 6  Daten im Überblick rechts
    "image8.jpeg",   # 7  Ausstattung S.6 links (Wohnzimmer)
    "image9.jpeg",   # 8  Ausstattung S.6 rechts oben (Akzent)
    "image10.jpeg",  # 9  Ausstattung S.6 rechts groß
    "image11.jpeg",  # 10 Ausstattung S.7 (Schlafzimmer/Küche)
    "image13.jpeg",  # 11 Ausstattung S.8 unten breit
    "image14.jpeg",  # 12 Sonstige Angaben rechts oben
    "image15.jpeg",  # 13 Sonstige Angaben rechts unten
    "image16.jpeg",  # 14 GRUNDRISS ganzseitig
    "image18.jpeg",  # 15 Galerie Kachel 01
    "image22.jpeg",  # 16 Galerie Kachel 02 (XML-Reihenfolge != visuell, per Testrender verifiziert)
    "image17.jpeg",  # 17 Galerie Kachel 03
    "image23.jpeg",  # 18 Galerie Kachel 04
    "image24.jpeg",  # 19 Galerie Kachel 05
    "image25.jpeg",  # 20 Galerie Kachel 06
    "image21.jpeg",  # 21 PORTRÄT Ansprechpartner (Kreis, letzte Seite)
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
        if not photo:
            continue  # leerer Eintrag => Slot behält Platzhalter (z. B. kein Grundriss geliefert)
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
