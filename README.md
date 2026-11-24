# Familien-Dashboard (Tablet)

Dashboard für das Samsung Galaxy Tab S6 im Querformat, angezeigt im Vollbild mit **Fully Kiosk Browser**.

**Inhalt**
- Wetter Ebersbach an der Fils: jetzt, 5-Tage-Vorhersage, Sonnenaufgang/-untergang (Open-Meteo, kostenlos, ohne Schlüssel)
- Abfuhrtermine (AWB Landkreis Göppingen): Blaue Tonne, Restmüll, Bio, Gelber Sack, Grüngut – nächster Termin zuerst
- Die nächsten 5 Veranstaltungen in Ebersbach (aus dem Veranstaltungskalender der Stadt)
- Rezept des Tages, türkisch & deutsch, leicht und sättigend, mit Airfryer-Rezepten und Tipps
- App-Leiste: YouTube, YouTube Music, Netflix, Spotify, Chrome
- Hintergrund ändert sich mit der Tageszeit, nachts wird das Bild gedimmt

## Einrichten (einmalig)

### 1. Seite online stellen (GitHub Pages)
Repository → **Settings** → **Pages** → *Branch*: `main`, Ordner `/ (root)` → **Save**.
Nach ein bis zwei Minuten ist das Dashboard erreichbar unter:
`https://postmen1971.github.io/chanan/`

### 2. Abfuhrtermine
Läuft automatisch: Ebersbach hat keine Abfuhrbezirke, die Termine kommen für die ganze Stadt
direkt vom AWB (abfall.io) – wie beim MORGEN-KNALLER. Nichts einzurichten.

### 3. Tablet
1. **Fully Kiosk Browser** aus dem Play Store installieren.
2. *Start URL*: `https://postmen1971.github.io/chanan/`
3. Empfohlen: *Web Content Settings* → Zoom aus · *Device Management* → *Keep Screen On* an.

Die Apps vom Tablet bleiben normal nutzbar – mit der Home-Taste oder über die App-Leiste im Dashboard.

## Automatisch
Jede Nacht holt GitHub Actions (`.github/workflows/daten.yml`) neue Abfuhr- und Veranstaltungstermine nach `data/`.
Das Dashboard lädt Wetter alle 20 Minuten und alles andere stündlich nach und lädt sich nachts um 4:30 Uhr einmal neu.

## Anpassen
- **Rezepte und Tipps:** `data/rezepte.json`
- **Apps in der Leiste:** `APPS` oben im Skript in `index.html`
- **Ort für das Wetter:** `ORT` in `index.html`
