# n8n-Updates v1.2 (14.07.) — 3 Blöcke einfügen, dann Publish

Behebt: abgeschnittene Texte (Längen-Limits), doppelte Einheiten (€€, m²², kWh kWh),
Flur-als-Wohnzimmer u. ä. Fehlzuordnungen, Galerie-Vielfalt, Außenfoto auf Daten-Seite.
Vorher: neues Template deployen (git push + Render Manual Deploy)!

---

## Block 1 — Knoten „HTTP Request" (Text-KI): JSON-Body KOMPLETT ersetzen

```
{
  "model": "claude-sonnet-4-5",
  "max_tokens": 1500,
  "messages": [{ "role": "user", "content": {{ JSON.stringify(`Du bist erfahrener Immobilien-Texter. Antworte AUSSCHLIESSLICH mit einem JSON-Objekt mit exakt diesen Feldern: lage, beschreibung, ausstattung_wohnzimmer, ausstattung_bad, ausstattung_schlafzimmer, ausstattung_kueche, ausstattung_allgemein, hinweise, highlight_1, highlight_2, highlight_3.
HARTE LAENGEN-LIMITS in Zeichen inkl. Leerzeichen, NIE ueberschreiten (die Texte muessen in feste Design-Boxen passen): lage max 550, beschreibung max 650, ausstattung_wohnzimmer max 200, ausstattung_bad max 200, ausstattung_schlafzimmer max 180, ausstattung_kueche max 180, ausstattung_allgemein max 300, hinweise max 260, highlight_1/2/3 je max 55.
Stil: professionell, konkret, keine Uebertreibungen, keine erfundenen Fakten - nur was in den Stichpunkten steht.
Objekt: ${$json.Objekttyp}, Wohnflaeche ${$json['Wohnfläche']}, Kaufpreis ${$json.Kaufpreis} EUR
Lage: ${$json.Lage_Stichpunkte}
Objekt-Stichpunkte: ${$json.Beschreibung_Stichpunkte}
Ausstattung: ${$json.Ausstattung_Stichpunkte}`) }} }]
}
```

---

## Block 2 — Knoten „VIsion Body": Code KOMPLETT ersetzen

```javascript
const thumbs = $('On form submission').first().json.thumbs_b64 || [];
const content = [];
thumbs.forEach((t, i) => {
  if (!t) return;
  content.push({ type: 'text', text: `Foto ${i}:` });
  content.push({ type: 'image', source: { type: 'base64', media_type: 'image/jpeg', data: t } });
});
content.push({ type: 'text', text:
  'Du bist Immobilien-Foto-Analyst. Klassifiziere JEDES Foto oben. ' +
  'Antworte AUSSCHLIESSLICH mit einem JSON-Array, ein Objekt pro Foto: ' +
  '[{"index":0,"typ":"aussen","qualitaet":8}] ' +
  'Erlaubte typ-Werte: aussen, garten, terrasse, wohnzimmer, kueche, bad, schlafzimmer, buero, flur, garage, grundriss, sonstiges. ' +
  'REGELN: Flur/Diele/Treppenhaus = flur (NIE wohnzimmer). Raum mit Sofa/Couch = wohnzimmer. ' +
  'Raum mit Bett oder Kinderbett = schlafzimmer. Schreibtisch/Monitore = buero. ' +
  'Ueberdachte Terrasse/Balkon = terrasse. Garagentor = garage. ' +
  'Technische Zeichnung/Grundriss-Scan = grundriss. ' +
  'qualitaet 1-10: Schaerfe, Licht, Aufgeraeumtheit, Repraesentativitaet; schiefe Fotos und enge Detail-Ausschnitte abwerten.' });
return [{ json: { body: {
  model: 'claude-sonnet-4-5',
  max_tokens: 2000,
  messages: [{ role: 'user', content }]
} } }];
```

---

## Block 3 — Knoten „Code in JavaScript": Code KOMPLETT ersetzen

```javascript
// ---------- Eingänge ----------
const f = $('On form submission').first().json;
const fotos = f.fotos_b64 || [];

// Einheiten säubern (das Template ergänzt €, ², kWh usw. selbst)
const ohneEuro = (s) => (s || '').toString().replace(/\s*€\s*$/, '').trim();
const ohneHoch2 = (s) => (s || '').toString().replace(/²\s*$/, '').trim();
const nurZahl = (s) => (((s || '').toString().match(/[\d.,]+/) || [''])[0]);

// Text-KI aus dem Knoten "HTTP Request"
let traw = $('HTTP Request').first().json.content[0].text;
traw = traw.slice(traw.indexOf('{'), traw.lastIndexOf('}') + 1);
const ki = JSON.parse(traw);

// Vision-Analyse (Input dieses Knotens)
let analyse = [];
try {
  let vraw = $json.content[0].text;
  vraw = vraw.slice(vraw.indexOf('['), vraw.lastIndexOf(']') + 1);
  analyse = JSON.parse(vraw);
} catch (e) { analyse = []; }

// ---------- KI-Foto-Zuordnung ----------
const SLOT_PLAN = [
  { slot: 1,  will: ['aussen', 'garten'] },
  { slot: 14, will: ['grundriss'], nurTyp: true },
  { slot: 7,  will: ['wohnzimmer'], nicht: ['flur', 'garage', 'buero'] },
  { slot: 10, will: ['schlafzimmer'], nicht: ['kueche', 'garage'] },
  { slot: 9,  will: ['bad'], nicht: ['garage'] },
  { slot: 4,  will: ['garten', 'terrasse', 'aussen'] },
  { slot: 5,  will: ['wohnzimmer', 'schlafzimmer', 'kueche'] },
  { slot: 6,  will: ['aussen', 'garten'] },
  { slot: 2,  will: ['aussen', 'terrasse', 'garten'] },
  { slot: 3,  will: ['garten', 'terrasse', 'aussen'] },
  { slot: 11, will: ['terrasse', 'garten', 'flur'] },
  { slot: 12, will: ['kueche', 'buero', 'bad'] },
  { slot: 13, will: ['terrasse', 'garten', 'flur'] },
  { slot: 8,  will: [] },
];
const GALERIE_SLOTS = [15, 16, 17, 18, 19, 20];
const GALERIE_MIX = ['wohnzimmer', 'kueche', 'aussen', 'terrasse', 'bad', 'schlafzimmer', 'garten', 'buero', 'flur', 'garage'];

const kand = analyse
  .filter(a => fotos[a.index] !== undefined)
  .map(a => ({ i: a.index, typ: a.typ || 'sonstiges', q: a.qualitaet || 5 }));
const benutzt = new Set();

function nimm(will, nurTyp, nicht) {
  let pool = kand.filter(k => !benutzt.has(k.i));
  if (!will.includes('grundriss')) pool = pool.filter(k => k.typ !== 'grundriss');
  if (nicht && nicht.length) pool = pool.filter(k => !nicht.includes(k.typ));
  if (will.length) {
    const passend = pool.filter(k => will.includes(k.typ));
    if (passend.length) pool = passend;
    else if (nurTyp) return null;
  }
  if (!pool.length) return null;
  pool.sort((a, b) => b.q - a.q);
  benutzt.add(pool[0].i);
  return pool[0].i;
}

const slotFoto = {};
for (const p of SLOT_PLAN) {
  const idx = nimm(p.will, p.nurTyp, p.nicht);
  if (idx !== null) slotFoto[p.slot] = idx;
}

// Galerie: bewusst gemischte Raum-Typen statt 4x Außenansicht
let mixStart = 0;
for (const g of GALERIE_SLOTS) {
  let idx = null;
  for (let t = 0; t < GALERIE_MIX.length && idx === null; t++) {
    const typ = GALERIE_MIX[(mixStart + t) % GALERIE_MIX.length];
    const pool = kand.filter(k => !benutzt.has(k.i) && k.typ === typ);
    if (pool.length) {
      pool.sort((a, b) => b.q - a.q);
      idx = pool[0].i; benutzt.add(idx);
      mixStart = (mixStart + t + 1) % GALERIE_MIX.length;
    }
  }
  if (idx === null) idx = nimm([], false, []);
  if (idx !== null) slotFoto[g] = idx;
}

let photos = [];
for (let s = 1; s <= 20; s++) photos.push(slotFoto[s] !== undefined ? fotos[slotFoto[s]] : '');
if (!kand.length && fotos.length) photos = fotos.slice(0, 20);

// ---------- Variablen ----------
const FIRMA = {
  firma: "Immobilienberatung Thorsten Does",
  firma_kurz: "THORSTEN DOES",
  firma_strasse: "Im Bachgarten 40",
  firma_ort: "50259 Pulheim",
  firma_email: "info@immobilienberatung-does.de",
  firma_web: "www.immobilienberatung-does.de",
  fax: ""
};

const kp = parseFloat(ohneEuro(f['Kaufpreis']).replace(/\./g, '').replace(',', '.'));
const wfl = parseFloat(ohneHoch2(f['Wohnfläche']).replace(',', '.'));

const variables = {
  titel: f['Titel'] || '', objektnummer: f['Objektnummer'] || '',
  objekttyp: f['Objekttyp'] || '',
  wohnflaeche: ohneHoch2(f['Wohnfläche']),
  nutzflaeche: ohneHoch2(f['Nutzfläche']),
  grundstueck: ohneHoch2(f['Grundstück']),
  zimmer: f['Zimmer'] || '', schlafzimmer: f['Schlafzimmer'] || '',
  badezimmer: f['Badezimmer'] || '',
  befeuerung: ((f['Heizungsart'] || '').split(/[- ]/)[0] || '')
    + (((f['Kamin'] || '').trim().toLowerCase().startsWith('j')) ? ' + Kamin' : ''),
  heizungsart: f['Heizungsart'] || '', verfuegbar_ab: f['Verfügbar_Ab'] || '',
  energieausweis: f['Energieausweis'] || '',
  kaufpreis: ohneEuro(f['Kaufpreis']),
  kaufpreis_qm: (kp && wfl) ? Math.round(kp / wfl).toLocaleString('de-DE') : '',
  provision: f['Provision'] || '',
  endenergie: nurZahl(f['Endenergie']),
  primaerenergie: nurZahl(f['Primärenergie']),
  co2: nurZahl(f['co2']),
  betreuer: f['Ansprechpartner'] || '', ansprechpartner: f['Ansprechpartner'] || '',
  telefon: f['Telefon'] || '', email: f['E-Mail'] || '',
  ...FIRMA,
  lage: ki.lage || '', beschreibung: ki.beschreibung || '',
  ausstattung_wohnzimmer: ki.ausstattung_wohnzimmer || '',
  ausstattung_bad: ki.ausstattung_bad || '',
  ausstattung_schlafzimmer: ki.ausstattung_schlafzimmer || '',
  ausstattung_kueche: ki.ausstattung_kueche || '',
  ausstattung_allgemein: ki.ausstattung_allgemein || '',
  hinweise: ki.hinweise || '',
  highlight_1: ki.highlight_1 || '', highlight_2: ki.highlight_2 || '',
  highlight_3: ki.highlight_3 || ''
};

return [{ json: { variables, photos } }];
```

---

## Danach
1. **Publish** in n8n
2. Neuer Voll-Lauf über die Upload-Seite (Original-Fotos, egal welche Reihenfolge)
3. Noch offen von Sebastian zu besorgen: **Grundriss-Scan** (war NICHT in den 29 Fotos —
   verifiziert per Kontaktbogen) + **Marco-Porträtfoto** (Slot 21)
