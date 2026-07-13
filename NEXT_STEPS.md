# Exposé-Automatisierung — Stand & nächste Schritte (Stand 08.07.2026, 23:47)

## 🚀 SONNTAG-SPRINT 12.07 — Text-Kette FERTIG machen (Reihenfolge!)

**Definition „fertig": Formular → KI-Text → PDF im Does-Design → landet als Mail im Postfach.**
(Foto-KI = Phase B, NICHT heute. Kosmetik-Punkte = später.)

### Schritt 1 — Formular: 3 neue Felder (Node 1 „On form submission")
Text-Felder mit EXAKT diesen Labels anlegen:
- `Ansprechpartner`
- `Telefon`
- `E-Mail`
(Grund: mehrere Leute in der Firma → pro Exposé änderbar. Firma/Adresse bleiben fix im Code.)

### Schritt 2 — Node 3 (Code) KOMPLETT ersetzen mit:
```javascript
const FIRMA = {
  firma: "Immobilienberatung Thorsten Does",
  firma_strasse: "Im Bachgarten 40",
  firma_ort: "50259 Pulheim",
  firma_email: "info@immobilienberatung-does.de",
  firma_web: "www.immobilienberatung-does.de",
  fax: ""
};

const f = $('On form submission').first().json;
let raw = $json.content[0].text;
raw = raw.slice(raw.indexOf('{'), raw.lastIndexOf('}') + 1);
const ki = JSON.parse(raw);

// Kaufpreis/m² automatisch rechnen (falls beide Zahlen da)
const kp = parseFloat((f['Kaufpreis'] || '').toString().replace(/\./g, '').replace(',', '.'));
const wf = parseFloat((f['Wohnfläche'] || '').toString().replace(',', '.'));

const variables = {
  titel: f['Titel'] || '',
  objektnummer: f['Objektnummer'] || '',
  objekttyp: f['Objekttyp'] || '',
  wohnflaeche: f['Wohnfläche'] || '',
  nutzflaeche: f['Nutzfläche'] || '',
  grundstueck: f['Grundstück'] || '',
  heizungsart: f['Heizungsart'] || '',
  verfuegbar_ab: f['Verfügbar_Ab'] || '',
  energieausweis: f['Energieausweis'] || '',
  kaufpreis: f['Kaufpreis'] || '',
  kaufpreis_qm: (kp && wf) ? Math.round(kp / wf).toLocaleString('de-DE') : '',
  provision: f['Provision'] || '',
  endenergie: f['Endenergie'] || '',
  primaerenergie: f['Primärenergie'] || '',
  co2: f['co2'] || '',
  // variabel pro Exposé (NEU aus dem Formular):
  betreuer: f['Ansprechpartner'] || '',
  ansprechpartner: f['Ansprechpartner'] || '',
  telefon: f['Telefon'] || '',
  email: f['E-Mail'] || '',
  ...FIRMA,
  // KI-Texte:
  lage: ki.lage || '',
  beschreibung: ki.beschreibung || '',
  ausstattung_wohnzimmer: ki.ausstattung_wohnzimmer || '',
  ausstattung_bad: ki.ausstattung_bad || '',
  ausstattung_schlafzimmer: ki.ausstattung_schlafzimmer || '',
  ausstattung_kueche: ki.ausstattung_kueche || '',
  ausstattung_allgemein: ki.ausstattung_allgemein || '',
  hinweise: ki.hinweise || '',
  highlight_1: ki.highlight_1 || '',
  highlight_2: ki.highlight_2 || '',
  highlight_3: ki.highlight_3 || ''
};

const photos = [];
return [{ json: { variables, photos } }];
```

### Schritt 3 — Node 5: Gmail „Send a message" ans Ende hängen
1. Node „Gmail" → Operation „Send" → bei Credentials „Sign in with Google" (Klick-Flow in n8n cloud)
2. **To:** `{{ $('On form submission').first().json['E-Mail'] }}`  ← Exposé geht an den, der das Formular ausgefüllt hat
3. **Subject:** `{{ 'Exposé: ' + $('On form submission').first().json['Titel'] }}`
4. **Message:** kurzer Fixtext („Anbei das fertige Exposé. Automatisch erstellt.")
5. **Options → Attachments:** Binary-Property `data` (= PDF aus Node 4)

### Schritt 4 — End-to-End-Test
1. Render aufwecken: Browser → `https://addscale-expose-renderer.onrender.com/` → warten bis `{"status":"ok"}`
2. Formular mit den echten Barbarastraße-18-Daten ausfüllen (Google Sheet „Expose Daten"), Ansprechpartner: Marco Eschbach + seine Nummer/Mail, Fotos LEER lassen
3. Mail im Postfach → PDF prüfen (Kontaktdaten auf der letzten Seite!)

### Schritt 5 — SOFORT danach: Demo-Video (60–90 Sek, Screenrecording)
Formular ausfüllen (Zeitraffer) → Mail ploppt auf → PDF durchscrollen. **Das ist ab Montag dein Outreach-Speer für Makler.** Kein Gesicht nötig, Stimme reicht.


## ✅ Fertig
- **Render-Dienst LIVE + getestet:** `https://addscale-expose-renderer.onrender.com/render`
  (POST {variables, photos} → PDF zurück; Health: GET / → {"status":"ok"})
- **Variablen-Vorlage** (`template.docx`) mit ~35 `{{tags}}` — im Repo.
- **n8n-Flow „Exposé Automatisierung" (n8n.cloud):** Knoten 1 = Form-Trigger FERTIG.

## n8n Form-Felder (EXAKTE Labels = Daten-Schlüssel, mit Umlauten/Groß)
Text: Titel, Objektnummer, Objekttyp, Wohnfläche, Nutzfläche, Grundstück, Zimmer,
Schlafzimmer, Badezimmer, Kamin, Heizungsart, Verfügbar_Ab, Energieausweis,
Kaufpreis, Provision, Endenergie, Primärenergie, co2
Textarea: Lage_Stichpunkte, Beschreibung_Stichpunkte, Ausstattung_Stichpunkte
File: Fotos (Multiple)

## Flow-Status (09.07.2026)
2. **Anthropic** ✅ FERTIG + getestet. model=claude-sonnet-4-5. JSON-Body:
   {model, max_tokens, messages:[{role:user, content: {{ JSON.stringify(`...prompt...`) }} }]}.
   KI packt Antwort in ```json-Fence → Code-Node schneidet raus.
3. **Code** ✅ FERTIG + getestet. Mappt Form-Labels → Vorlage-Keys, parst KI-JSON
   (raw.slice(indexOf('{'), lastIndexOf('}')+1)), FIRMA-Block oben (Platzhalter „HIER…").
   photos = [] (Fotos bewusst später). Holt Form via $('On form submission').
4. **HTTP Request** ⏳ gebaut, Body {variables, photos} als JSON.stringify, Response=File,
   Timeout 120000. PROBLEM: Render-Cold-Start (503 „Application loading").
   FIX: Settings → Retry On Fail AN (Max 5, Wait 20000) + Server vorher per GET / aufwecken.
5. **Send Email** ❌ offen — PDF-Anhang an Stiefvater. LETZTER Knoten der Text-Kette.

## ✅ Phase-B-Server-Teil FERTIG (13.07., lokal verifiziert — muss noch DEPLOYED werden!)
- Galerie-Dedup gefixt: Kacheln 01–06 haben eigene Media-Dateien (image22–25 neu, rId100–103).
- fill.py: PHOTO_SLOTS jetzt 21 Slots in visueller Reihenfolge (Galerie 02/03 waren im XML
  vertauscht — per Testrender verifiziert). Leerer Foto-Eintrag ("") => Slot wird übersprungen.
- Logo-Box: {{firma}} → {{firma_kurz}} (alle 4 Kopien), Schrift 65→40 (20pt).
  „THORSTEN DOES" passt jetzt. Node 3 muss firma_kurz liefern!
- app.py: NEU POST /thumbs {photos:[base64]} → {thumbs:[base64 klein]} für Vision-Analyse.
- DEPLOY: git add -A && git commit && git push → Render Dashboard → Manual Deploy.

## v1.1 — EIGENE UPLOAD-SEITE (gebaut 13.07., ersetzt n8n-Formular)
- GET / = gebrandetes Formular (alle Felder + Multi-Foto-Upload, Originalgrößen ok).
  POST /submit = verkleinert serverseitig (1600px + 512px-Thumbs, EXIF-Rotation),
  schickt {Felder, fotos_b64, thumbs_b64} an Env-Var N8N_WEBHOOK_URL. /health = JSON-Check.
- GRUND: n8n-Form kann max ~16 MB und die Cloud-Instanz stirbt an Base64 großer Fotos (OOM 13.07.).
- n8n-UMBAU dazu: Webhook-Node (POST, Respond Immediately) → Code-Node `return [{json: $json.body}]`
  UMBENANNT in "On form submission" (hält alle bestehenden Expressions am Leben!) → Rest-Kette.
  Nodes "Fotos zu Base64" + "Thumbs" entfallen. Vision Body liest thumbs_b64, Node 3 fotos_b64
  via $('On form submission'). requirements.txt: +python-multipart.
- OFFEN: Porträt-Foto Marco (Slot 21) fix hinterlegen, sobald Foto da.

## Phase B — Foto-KI (nach Text-Kette; Sebastians Kern-Wunsch 09.07)
- ZIEL: Nutzer lädt ~20 beliebige Fotos hoch → KEINE manuelle Auswahl/Zuordnung.
  Claude Vision bewertet jedes Foto (Raum-Typ + Qualität) und ordnet die besten
  den Bild-Slots zu (Titelbild = bestes repräsentatives, dann Räume passend).
  Nicht genutzte Fotos fallen raus. Vollautomatisch.
- ✅ SLOT-KARTE ERSTELLT (13.07., via nummerierte Testbilder lokal gerendert):
  | Pos | Slot-Datei | Wo im Exposé | Was reingehört |
  |---|---|---|---|
  | 1 | image1 | Titelseite Hexagon-Mosaik (+ letzte Seite wiederholt) | BESTES Außenfoto |
  | 2 | image3 | Inhaltsseite rechte Bildspalte | gutes Foto (Außen/Wohnen) |
  | 3 | image4 | Inhaltsseite Hexagon-Akzente (3× gleiches Bild) | Detail-/Deko-Foto |
  | 4 | image5 | Lage-Seite groß links | Außen/Umgebung/Garten |
  | 5 | image6 | Beschreibung großes Hexagon links | Wohnbereich |
  | 6 | image7 | „Daten im Überblick" rechts | beliebig gutes Foto |
  | 7 | image8 | Ausstattung S.6 links (Wohnzimmer) | WOHNZIMMER |
  | 8 | image9 | Ausstattung S.6 rechts oben (Akzent, kaum sichtbar) | egal |
  | 9 | image10 | Ausstattung S.6 rechts groß | Wohnraum/Bad |
  | 10 | image11 | Ausstattung S.7 links unten | SCHLAFZIMMER oder KÜCHE |
  | 11 | image13 | Ausstattung S.8 unten breit | Allgemein (Flur/Garten) |
  | 12 | image14 | Sonstige Angaben S.9 rechts oben | gutes Restfoto |
  | 13 | image15 | Sonstige Angaben S.9 rechts unten | gutes Restfoto |
  | 14 | image16 | GRUNDRISS S.10 ganzseitig | GRUNDRISS-Scan (KI muss erkennen!) |
  | 15 | image17 | Bildergalerie Kacheln 02–05 (⚠️ 4× GLEICHES Bild) | s. Dedup-Problem |
  | 16 | image18 | Bildergalerie Kacheln 01+06 (⚠️ 2× gleiches Bild) | s. Dedup-Problem |
  | 17 | image21 | ANSPRECHPARTNER-Porträt (Kreis, letzte Seite) | PORTRÄT — NICHT aus Objekt-Upload! Pro Mitarbeiter fix hinterlegen |
- ⚠️ GALERIE-DEDUP-PROBLEM entdeckt: Die 6 Galerie-Kacheln teilen sich nur 2 Media-Dateien
  (InDesign hat identische Platzhalter dedupliziert). Fix: document.xml.rels umschreiben,
  damit jede Kachel eine eigene Media-Datei bekommt → dann 6 verschiedene Galerie-Fotos möglich.
- ⚠️ Slot 17 (Porträt) + Slot 14 (Grundriss) sind KEINE normalen Objektfotos → Foto-KI braucht
  3 Kategorien: Objektfotos / Grundriss / (Porträt kommt fix aus Mitarbeiter-Stammdaten).
- Bestätigt: Einbettung ist deterministisch sauber — Center-Crop + exakte Slotgröße, Design bleibt 1:1.
- TODO: n8n Multi-File-Binary → base64 (fummelig, eigener Schritt).
- WICHTIG: ZIP/große Uploads sprengen n8n-Form-Limit (25,7 MB ZIP = Submit-Fail).
  Nutzer müssen EINZELNE JPGs hochladen, nicht gezippt.

## Vorlagen-Render lokal (WICHTIG für künftige Template-Arbeit)
- LibreOffice ist lokal installiert (`brew install --cask libreoffice`, soffice unter
  /opt/homebrew/bin/soffice). Fonts liegen in ~/Library/Fonts (= wie Server).
- Vorlage lokal rendern statt deployen:
  `/opt/homebrew/bin/soffice --headless --convert-to pdf --outdir /tmp/lo /pfad/template.docx`
  → PDF prüfen, iterieren, ERST DANN deployen. Kein Blind-Raten mehr.

## Vorlagen-Fixes ERLEDIGT (09.07, lokal getestet)
- Überschriften abgeschnitten → gefixt: explizite Run-Größe injizieren (Style-Vererbung
  ignoriert LibreOffice!). Titel1 + Titel10 = sz 36 (18pt), Untertitel10 = sz 28 (14pt).
  ⚠️ Es gibt 2 Kopien je Überschrift (mc:Choice + Fallback) — BEIDE bearbeiten.
- Alle 4 Lorem-Blöcke raus (Küche, Ausstattung, Uciamus/S.9, Sunt). Anker müssen
  ZUSAMMENHÄNGENDE Roh-XML-Fragmente sein (Wörter oft durch proofErr zerhackt).

## Offen / später (klein, kosmetisch)
- Winziger „." Rest S.8 (Ausstattung) · leerer Highlight-Slot 02 (S.9) ·
  Doppel-Punkt „.." wo KI-Text endet (Template hat Trailing-„." nach Prosa-Tags).
- Vorlage hat noch KEINE Slots für: Zimmer/Schlafzimmer/Badezimmer/Kamin(Befeuerung),
  Energie-Text-Block, Highlight_4.
- Firmen-/Kontaktdaten (Node 3 FIRMA-Block): Betreuer = Marco Eschbach ✓;
  noch offen: Firmenname, Tel, E-Mail, Adresse, Web.
- Echte Objektdaten liegen vor (Google Sheet „Expose Daten"): Barbarastraße 18,
  50321 Brühl, Reihenendhaus, 399.000 €, ObjektNr 013/2026. Fehlen im Sheet:
  Grundstück, Provision, Endenergie, Primärenergie, co2.
- Repo ist aktuell PUBLIC (wegen Render-Deploy ohne Konto-Login sebo1111-first).
