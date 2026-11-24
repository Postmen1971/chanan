# Familien-Dashboard (Tablet)

Dashboard für das Samsung Galaxy Tab S6 im Querformat, angezeigt im Vollbild mit **Fully Kiosk Browser**.

**Inhalt**
- Wetter Ebersbach an der Fils: jetzt, 5-Tage-Vorhersage, Sonnenaufgang/-untergang (Open-Meteo, kostenlos, ohne Schlüssel)
- Abfuhrtermine (AWB Landkreis Göppingen): Blaue Tonne, Restmüll, Bio, Gelber Sack, Grüngut – nächster Termin zuerst
- Die nächsten 5 Veranstaltungen in Ebersbach (aus dem Veranstaltungskalender der Stadt)
- Rezept des Tages, türkisch & deutsch, leicht und sättigend, mit Airfryer-Rezepten und Tipps
- App-Leiste: YouTube, YouTube Music, Netflix, WhatsApp, Chrome
- Hintergrund ändert sich mit der Tageszeit, nachts wird das Bild gedimmt

## Einrichten (einmalig)

### 1. Seite online stellen (GitHub Pages)
Repository → **Settings** → **Pages** → *Branch*: `main`, Ordner `/ (root)` → **Save**.
Nach ein bis zwei Minuten ist das Dashboard erreichbar unter:
`https://postmen1971.github.io/chanan/`

### 2. Abfuhrtermine verbinden
1. Auf **awb-gp.de → Abfallabholung → Abfuhrtermine** Ebersbach, Straße und Hausnummer wählen.
2. Beim Knopf **ICS / Kalender** lange drücken → *Link kopieren*.
3. Repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
   Name: `ABFALL_ICS_URL` – Wert: der kopierte Link.
4. Unter **Actions** → *Daten aktualisieren* → **Run workflow**.

Der Link steht damit nicht öffentlich im Repository (er enthält die Adresse).

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
