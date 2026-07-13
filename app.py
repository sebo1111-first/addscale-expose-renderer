"""Exposé-Render-Dienst. n8n ruft POST /render mit Daten + Foto-URLs -> bekommt PDF zurück."""
import base64, io, os, subprocess, tempfile
from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel
from PIL import Image
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

@app.get("/")
def health():
    return {"status": "ok", "service": "addscale-expose-renderer"}

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

@app.post("/render")
def render(req: RenderRequest):
    photos = [_load(p) for p in req.photos]
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
