# addscale Exposé Renderer

Kleiner Web-Dienst, der die Immobilien-Exposé-Vorlage automatisch füllt.
Aufgerufen aus n8n per HTTP → gibt fertiges **PDF** zurück.

## Endpunkt
`POST /render`

```json
{
  "variables": { "titel": "...", "lage": "...", "kaufpreis": "399.000,00", "...": "..." },
  "photos": ["https://url-zu-foto-1.jpg", "https://url-zu-foto-2.jpg"]
}
```
→ Antwort: `application/pdf` (das fertige Exposé).

`GET /` → Health-Check.

## Wie es funktioniert
1. `{{variablen}}` in `template.docx` werden durch die Werte ersetzt.
2. Fotos werden auf die Design-Bild-Slots skaliert eingesetzt (Design bleibt erhalten).
3. LibreOffice wandelt das docx in PDF.

## Deploy (Render.com, gratis)
- New → **Web Service** → dieses Repo wählen.
- Render erkennt das `Dockerfile` automatisch → Deploy.
- Ergebnis-URL: `https://<name>.onrender.com`

Gebaut mit [Claude Code](https://claude.com/claude-code).
