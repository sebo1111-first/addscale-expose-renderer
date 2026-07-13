"""Exposé-Render-Dienst + Upload-Seite. n8n ruft POST /render -> PDF; Makler nutzt GET / (Formular)."""
import base64, io, os, subprocess, tempfile
from fastapi import FastAPI, Request
from fastapi.responses import Response, HTMLResponse
from pydantic import BaseModel
from PIL import Image, ImageOps
import requests
from fill import fill

app = FastAPI(title="addscale Exposé Renderer")
TEMPLATE = open(os.path.join(os.path.dirname(__file__), "template.docx"), "rb").read()

class RenderRequest(BaseModel):
    variables: dict = {}          # {"lage": "...", "kaufpreis": "399.000,00", ...}
    photos: list[str] = []        # Foto-URLs ODER base64-Strings, in Slot-Reihenfolge

def _load(p: str) -> bytes:
    if p.startswith("http"):
        return requests.get(p, timeout=30).content
    return base64.b64decode(p.split(",")[-1])   # data:...;base64,XXXX oder reines base64

@app.get("/health")
def health():
    return {"status": "ok", "service": "addscale-expose-renderer"}

# ---------------------------------------------------------------------------
# Upload-Seite: Makler füllt Formular + wirft BELIEBIG große Fotos rein.
# Server verkleinert sofort (1600px fürs Exposé, 512px für die KI-Analyse)
# und schickt alles kompakt an den n8n-Webhook (Env-Var N8N_WEBHOOK_URL).
# ---------------------------------------------------------------------------

FELDER = [
    ("Titel", "text", "Charmantes Reihenendhaus in ruhiger Lage"),
    ("Objektnummer", "text", "013/2026"),
    ("Objekttyp", "text", "Reihenendhaus"),
    ("Wohnfläche", "text", "125 m²"),
    ("Nutzfläche", "text", "145 m²"),
    ("Grundstück", "text", "210 m²"),
    ("Zimmer", "text", "5"),
    ("Schlafzimmer", "text", "3"),
    ("Badezimmer", "text", "2"),
    ("Kamin", "text", "Nein"),
    ("Heizungsart", "text", "Gas-Zentralheizung"),
    ("Verfügbar_Ab", "text", "nach Absprache"),
    ("Energieausweis", "text", "Verbrauchsausweis"),
    ("Kaufpreis", "text", "399.000 €"),
    ("Provision", "text", "3,57 % inkl. MwSt."),
    ("Endenergie", "text", "142,5 kWh/(m²·a)"),
    ("Primärenergie", "text", "156,3 kWh/(m²·a)"),
    ("co2", "text", "38 kg/(m²·a)"),
    ("Ansprechpartner", "text", "Marco Eschbach"),
    ("Telefon", "text", "0170 1234567"),
    ("E-Mail", "email", "name@firma.de"),
]
TEXTAREAS = [
    ("Lage_Stichpunkte", "Stichpunkte zur Lage (Anbindung, Umgebung, Entfernungen ...)"),
    ("Beschreibung_Stichpunkte", "Stichpunkte zum Objekt (Baujahr, Etagen, Garten, Garage ...)"),
    ("Ausstattung_Stichpunkte", "Stichpunkte zur Ausstattung (Küche, Bäder, Böden ...)"),
]

def _form_html() -> str:
    inputs = "".join(
        f'<label>{name}{"*" if name in ("Titel", "E-Mail") else ""}'
        f'<input type="{typ}" name="{name}" placeholder="{ph}"{" required" if name in ("Titel", "E-Mail") else ""}></label>'
        for name, typ, ph in FELDER
    )
    areas = "".join(
        f'<label class="wide">{name.replace("_Stichpunkte", "")} – Stichpunkte'
        f'<textarea name="{name}" rows="3" placeholder="{ph}"></textarea></label>'
        for name, ph in TEXTAREAS
    )
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Exposé-Automat</title>
<style>
 body{{font-family:-apple-system,'Segoe UI',sans-serif;background:#f4f5f7;margin:0;color:#1d2733}}
 .box{{max-width:860px;margin:32px auto;background:#fff;border-radius:14px;padding:36px;box-shadow:0 4px 24px rgba(0,0,0,.07)}}
 h1{{margin:0 0 4px;font-size:26px}} .sub{{color:#6b7683;margin:0 0 28px}}
 form{{display:grid;grid-template-columns:1fr 1fr;gap:14px 18px}}
 label{{display:flex;flex-direction:column;font-size:13px;font-weight:600;gap:5px}}
 .wide{{grid-column:1/-1}}
 input,textarea{{border:1px solid #d4dae1;border-radius:8px;padding:10px;font-size:15px;font-family:inherit}}
 input:focus,textarea:focus{{outline:2px solid #4a5fc1;border-color:#4a5fc1}}
 .foto{{grid-column:1/-1;border:2px dashed #b9c2cc;border-radius:10px;padding:22px;text-align:center;background:#fafbfc}}
 button{{grid-column:1/-1;background:#1d2733;color:#fff;border:0;border-radius:10px;padding:15px;font-size:17px;font-weight:700;cursor:pointer}}
 button:hover{{background:#31405a}} .hint{{font-size:12px;color:#6b7683;font-weight:400}}
</style></head><body><div class="box">
<h1>Exposé-Automat</h1>
<p class="sub">Daten eintragen, Fotos hochladen – das fertige Exposé kommt in wenigen Minuten per E-Mail. <b>Fotos in Originalgröße sind okay</b>, Reihenfolge egal, Grundriss einfach mit dazu.</p>
<form action="/submit" method="post" enctype="multipart/form-data" onsubmit="document.getElementById('go').textContent='Wird hochgeladen – bitte warten…';">
{inputs}{areas}
<div class="foto"><label style="font-size:15px">📷 Fotos auswählen (mehrfach nacheinander möglich, inkl. Grundriss)
<input type="file" id="fotoinp" name="Fotos" accept="image/*" multiple style="border:0;padding:10px 0"></label>
<div class="hint" id="cnt">Noch keine Fotos ausgewählt.</div>
<div class="hint">Die KI wählt automatisch die besten Bilder und ordnet sie den richtigen Seiten zu.</div></div>
<button id="go" type="submit">Exposé erstellen ➜</button>
</form>
<script>
// Fotos SAMMELN statt ersetzen: jede neue Auswahl kommt dazu
const inp = document.getElementById('fotoinp');
const dt = new DataTransfer();
inp.addEventListener('change', () => {{
  for (const f of inp.files) dt.items.add(f);
  inp.files = dt.files;
  document.getElementById('cnt').textContent = dt.files.length + ' Foto(s) ausgewählt ✓';
}});
</script>
</div></body></html>"""

OK_HTML = """<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Exposé wird erstellt</title>
<style>body{font-family:-apple-system,'Segoe UI',sans-serif;background:#f4f5f7;display:grid;place-items:center;height:100vh;margin:0}
.card{background:#fff;border-radius:14px;padding:48px;text-align:center;box-shadow:0 4px 24px rgba(0,0,0,.07);max-width:460px}
h1{font-size:44px;margin:0 0 12px}</style></head><body><div class="card">
<h1>✅</h1><h2>Exposé wird erstellt</h2>
<p>Die KI schreibt jetzt die Texte, wählt die besten Fotos aus und baut das PDF.<br><br>
<b>Das fertige Exposé kommt in 2–5 Minuten per E-Mail.</b></p>
<a href="/">Noch ein Exposé erstellen</a></div></body></html>"""

@app.get("/", response_class=HTMLResponse)
def formular():
    return _form_html()

@app.post("/submit", response_class=HTMLResponse)
async def submit(request: Request):
    form = await request.form()
    fields = {k: v for k, v in form.multi_items() if isinstance(v, str)}

    fotos_b64, thumbs_b64 = [], []
    for up in form.getlist("Fotos")[:30]:                     # Obergrenze 30 Fotos
        if isinstance(up, str) or not getattr(up, "filename", ""):
            continue
        raw = await up.read()
        if not raw:
            continue
        try:
            img = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
            big = img.copy(); big.thumbnail((1600, 1600))
            b = io.BytesIO(); big.save(b, "JPEG", quality=80)
            th = img.copy(); th.thumbnail((512, 512))
            t = io.BytesIO(); th.save(t, "JPEG", quality=60)
            fotos_b64.append(base64.b64encode(b.getvalue()).decode())
            thumbs_b64.append(base64.b64encode(t.getvalue()).decode())
        except Exception:
            continue                                          # kaputte Datei -> überspringen

    hook = os.environ.get("N8N_WEBHOOK_URL", "")
    if not hook:
        return HTMLResponse("<h3>Konfig-Fehler: N8N_WEBHOOK_URL ist nicht gesetzt.</h3>", status_code=500)
    payload = {**fields, "fotos_anzahl": len(fotos_b64),
               "fotos_b64": fotos_b64, "thumbs_b64": thumbs_b64}
    requests.post(hook, json=payload, timeout=60)
    return OK_HTML

class ThumbsRequest(BaseModel):
    photos: list[str] = []        # base64-Strings (Original-Fotos)

@app.post("/thumbs")
def thumbs(req: ThumbsRequest):
    """Kleine Vorschau-Bilder für die KI-Foto-Analyse (spart Tokens + Upload-Größe)."""
    out = []
    for p in req.photos:
        try:
            img = Image.open(io.BytesIO(_load(p))).convert("RGB")
            img.thumbnail((512, 512))
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=60)
            out.append(base64.b64encode(buf.getvalue()).decode())
        except Exception:
            out.append("")
    return {"thumbs": out}

# Ansprechpartner-Porträts (Slot 21, Kreis auf der letzten Seite) — fix hinterlegt
PORTRAITS = {
    "marco eschbach": "portraits/marco-eschbach.jpg",
}

@app.post("/render")
def render(req: RenderRequest):
    photos = [_load(p) for p in req.photos]
    # Porträt automatisch in Slot 21 legen, wenn für den Ansprechpartner hinterlegt
    pfile = PORTRAITS.get((req.variables or {}).get("ansprechpartner", "").strip().lower())
    if pfile:
        ppath = os.path.join(os.path.dirname(__file__), pfile)
        if os.path.exists(ppath):
            while len(photos) < 20:
                photos.append(b"")
            photos.append(open(ppath, "rb").read())
    docx = fill(TEMPLATE, req.variables, photos)
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "expose.docx")
        with open(src, "wb") as f:
            f.write(docx)
        subprocess.run(
            ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", d, src],
            check=True, timeout=180,
        )
        with open(os.path.join(d, "expose.pdf"), "rb") as f:
            pdf = f.read()
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="expose.pdf"'},
    )
