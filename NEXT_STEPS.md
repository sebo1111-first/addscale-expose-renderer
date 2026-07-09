# Exposé-Automatisierung — Stand & nächste Schritte (Stand 08.07.2026, 23:47)

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

## Phase B — Foto-KI (nach Text-Kette; Sebastians Kern-Wunsch 09.07)
- ZIEL: Nutzer lädt ~20 beliebige Fotos hoch → KEINE manuelle Auswahl/Zuordnung.
  Claude Vision bewertet jedes Foto (Raum-Typ + Qualität) und ordnet die besten
  den Bild-Slots zu (Titelbild = bestes repräsentatives, dann Räume passend).
  Nicht genutzte Fotos fallen raus. Vollautomatisch.
- TODO Claude: Vorlage-Bild-Slots kartieren (fill.py PHOTO_SLOTS = 17 Slots) —
  welcher Slot zeigt was (Titel/Grundriss/Räume)? Sonst kann KI nicht „was wohin".
- TODO: n8n Multi-File-Binary → base64 (fummelig, eigener Schritt).
- WICHTIG: ZIP/große Uploads sprengen n8n-Form-Limit (25,7 MB ZIP = Submit-Fail).
  Nutzer müssen EINZELNE JPGs hochladen, nicht gezippt.

## Offen / später
- Vorlage hat noch KEINE Slots für: Zimmer/Schlafzimmer/Badezimmer/Kamin(Befeuerung),
  Energie-Text-Block, Highlight_4.
- Firmen-/Kontaktdaten (Node 3 FIRMA-Block): Betreuer = Marco Eschbach ✓;
  noch offen: Firmenname, Tel, E-Mail, Adresse, Web.
- Echte Objektdaten liegen vor (Google Sheet „Expose Daten"): Barbarastraße 18,
  50321 Brühl, Reihenendhaus, 399.000 €, ObjektNr 013/2026. Fehlen im Sheet:
  Grundstück, Provision, Endenergie, Primärenergie, co2.
- Repo ist aktuell PUBLIC (wegen Render-Deploy ohne Konto-Login sebo1111-first).
