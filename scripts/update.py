#!/usr/bin/env python3
"""
Holt täglich die Daten für das Dashboard und schreibt sie nach data/:

  data/abfall.json  – Abfuhrtermine Ebersbach (AWB Landkreis Göppingen, über abfall.io)
  data/events.json  – Veranstaltungen in Ebersbach an der Fils (Veranstaltungskalender-PDF der Stadt)

Läuft in GitHub Actions. Wenn eine Quelle nicht erreichbar ist oder nichts
Brauchbares liefert, bleibt die vorhandene Datei unverändert.

Abfall: Ebersbach hat keine Abfuhrbezirke – die Termine gelten für die ganze Stadt
und kommen direkt aus der abfall.io-Schnittstelle des AWB (wie beim MORGEN-KNALLER).
Optional kann ein eigener ICS-Link als Secret ABFALL_ICS_URL hinterlegt werden.
"""
import datetime as dt
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
TODAY = dt.date.today()
UA = {"User-Agent": "Mozilla/5.0 (Familien-Dashboard; GitHub Actions)"}

EVENTS_PDF = ("https://www.ebersbach.de/resources/02%20Datenobjekte/PDF-Dateien/"
              "Ebersbacher%20Veranstaltungskalender.pdf")


def log(*a):
    print(*a, file=sys.stderr)


def fetch(url, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def write_json(name, obj):
    path = os.path.join(DATA, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    log("geschrieben:", path)


# ---------------------------------------------------------------- Abfall

WASTE_TYPES = [
    # (Schlüssel, Anzeigename, Suchwörter im Kalendertext)
    ("papier", "Blaue Tonne · Papier", ["papier", "blaue", "pappe"]),
    ("gelb", "Gelber Sack", ["gelb", "wertstoff", "verpackung"]),
    ("bio", "Biotonne", ["bio"]),
    ("gruen", "Grüngut", ["grün", "gruen", "garten", "baum", "strauch"]),
    ("rest", "Restmüll", ["rest", "haus"]),
]


def classify(summary):
    s = summary.lower()
    for key, _, words in WASTE_TYPES:
        if any(w in s for w in words):
            return key
    return None


def fix_period(url):
    """Zeitraum in der abfall.io-URL auf heute bis +13 Monate setzen."""
    start = TODAY.replace(day=1)
    end = (start + dt.timedelta(days=400))
    period = f"{start:%Y%m%d}-{end:%Y%m%d}"
    url = url.replace("{%Y}", str(TODAY.year)).replace("{YEAR}", str(TODAY.year))
    if "timeperiod=" in url:
        url = re.sub(r"timeperiod=[0-9]{8}-[0-9]{8}", "timeperiod=" + period, url)
    elif "api.abfall.io" in url and "mode=export" in url:
        url += "&timeperiod=" + period
    return url


def parse_ics(text):
    text = re.sub(r"\r?\n[ \t]", "", text)  # gefaltete Zeilen zusammenfügen
    out = []
    for block in text.split("BEGIN:VEVENT")[1:]:
        m_date = re.search(r"^DTSTART[^:\n]*:(\d{8})", block, re.M)
        m_sum = re.search(r"^SUMMARY[^:\n]*:(.*)$", block, re.M)
        if not m_date or not m_sum:
            continue
        summary = m_sum.group(1).strip().replace("\\,", ",").replace("\\;", ";")
        d = dt.datetime.strptime(m_date.group(1), "%Y%m%d").date()
        out.append((d, summary))
    return out


ABFALL_GQL = "https://widgets.abfall.io/graphql"
ABFALL_KEY = "7a4730955599a7e7c0ceb39c548b6abbae874dc7e6a0afc5"
EBERSBACH_HAUSNR_ID = "4021"   # Hauptstraße – gilt für ganz Ebersbach (keine Bezirke)
WASTE_IDS = {"18": "rest", "19": "papier", "17": "gelb", "20": "bio", "59": "gruen"}


def abfall_graphql():
    body = json.dumps({
        "query": "query($id:ID!){appointments(idHouseNumber:$id){date time location note wasteType{id name}}}",
        "variables": {"id": EBERSBACH_HAUSNR_ID},
    }).encode()
    req = urllib.request.Request(ABFALL_GQL, data=body, method="POST", headers={
        **UA, "Content-Type": "application/json", "Accept": "application/json",
        "x-abfallplus-api-key": ABFALL_KEY,
        "Origin": "https://awb-gp.de", "Referer": "https://awb-gp.de/",
    })
    with urllib.request.urlopen(req, timeout=40) as r:
        data = json.loads(r.read().decode("utf-8"))
    items = []
    for a in (data.get("data") or {}).get("appointments") or []:
        wt = a.get("wasteType") or {}
        key = WASTE_IDS.get(str(wt.get("id"))) or classify(wt.get("name") or "")
        if not key or not a.get("date"):
            continue
        d = dt.date.fromisoformat(a["date"][:10])
        items.append((d, key, wt.get("name") or ""))
    return items


def abfall_ics(url):
    raw = fetch(fix_period(url)).decode("utf-8", "replace")
    out = []
    for d, summary in parse_ics(raw):
        key = classify(summary)
        if key:
            out.append((d, key, summary))
    return out


def update_abfall():
    url = os.environ.get("ABFALL_ICS_URL", "").strip()
    items = []
    try:
        items = abfall_ics(url) if url else abfall_graphql()
    except Exception as e:  # noqa: BLE001
        log("Abfall: Abruf fehlgeschlagen:", e)
    if not items and url:
        try:
            items = abfall_graphql()
        except Exception as e:  # noqa: BLE001
            log("Abfall: GraphQL fehlgeschlagen:", e)
    items = [{"date": d.isoformat(), "type": k, "title": t}
             for d, k, t in items if d >= TODAY - dt.timedelta(days=1)]
    if not items:
        log("Abfall: keine Termine erhalten – alte Datei bleibt")
        return
    items.sort(key=lambda x: (x["date"], x["type"]))
    log(f"Abfall: {len(items)} Termine")
    write_json("abfall.json", {"updated": dt.datetime.now().isoformat(timespec="minutes"),
                               "source": "AWB Landkreis Göppingen", "items": items})


# ---------------------------------------------------------------- Veranstaltungen

IMPORTANT_WORDS = [
    "markt", "fest", "konzert", "advent", "weihnacht", "nikolaus", "zauber", "fasching",
    "theater", "martini", "laterne", "ausstellung", "putzete", "basar", "stadtfest",
    "glühen", "kinder", "winterwasen", "herbst", "musik", "lauf", "flohmarkt", "kino",
    "vortrag", "lesung", "eröffnung", "dorfweihnacht", "silvester", "open air",
]
ROUTINE_WORDS = [
    "spieleabend", "kaffeetreff", "mäschlestreff", "linux-café", "treff im bürgerhaus",
    "kaffee- und kuchen", "hauptversammlung", "mitgliederversammlung", "generalversammlung",
    "jugendhauptversammlung", "wkd ", "mittagstisch", "cafe asyl", "café asyl",
]


def importance(title):
    t = title.lower()
    if any(w in t for w in ROUTINE_WORDS):
        return 0
    if any(w in t for w in IMPORTANT_WORDS):
        return 2
    return 1


DATE_RE = re.compile(r"^(\d{1,2})\.(\d{1,2})\.?$")


def parse_events_pdf(blob):
    import pdfplumber  # in der Action installiert

    events = []
    year = TODAY.year
    with pdfplumber.open(io.BytesIO(blob)) as pdf:
        first_text = (pdf.pages[0].extract_text() or "")
        m = re.search(r"(20\d\d)", first_text)
        if m:
            year = int(m.group(1))
        cols = None  # x-Grenzen der Spalten
        for page in pdf.pages:
            words = page.extract_words(keep_blank_chars=False, use_text_flow=False, x_tolerance=2)
            # Kopfzeile suchen
            head = {w["text"].lower(): w["x0"] for w in words
                    if w["text"].lower() in ("am", "bis", "veranstaltung", "veranstalter", "ort")}
            if all(k in head for k in ("am", "veranstaltung", "veranstalter", "ort")):
                cols = sorted([head["am"], head.get("bis", head["am"] + 25), head["veranstaltung"],
                               head["veranstalter"], head["ort"]])
            if not cols:
                continue
            # Wörter zu Zeilen gruppieren
            lines = {}
            for w in words:
                key = round(w["top"] / 3)
                lines.setdefault(key, []).append(w)
            for key in sorted(lines):
                ws = sorted(lines[key], key=lambda w: w["x0"])
                cells = ["", "", "", "", ""]
                for w in ws:
                    idx = 0
                    for i, x in enumerate(cols):
                        if w["x0"] >= x - 3:
                            idx = i
                    cells[idx] = (cells[idx] + " " + w["text"]).strip()
                if cells[2].lower() == "veranstaltung":
                    continue
                m1 = DATE_RE.match(cells[0])
                if m1:
                    start = dt.date(year, int(m1.group(2)), int(m1.group(1)))
                    end = None
                    m2 = DATE_RE.match(cells[1])
                    if m2:
                        end = dt.date(year, int(m2.group(2)), int(m2.group(1)))
                        if end < start:
                            end = end.replace(year=year + 1)
                    events.append({"start": start, "end": end, "title": cells[2],
                                   "org": cells[3], "place": cells[4]})
                elif events and not cells[0] and not cells[1]:
                    # umbrochene Zeile: an vorigen Eintrag anhängen
                    ev = events[-1]
                    for i, k in ((2, "title"), (3, "org"), (4, "place")):
                        if cells[i]:
                            ev[k] = (ev[k] + " " + cells[i]).strip()
    return events


def update_events():
    try:
        blob = fetch(EVENTS_PDF)
        events = parse_events_pdf(blob)
    except Exception as e:  # noqa: BLE001
        log("Veranstaltungen: fehlgeschlagen:", e)
        return
    events = [e for e in events if e["title"]]
    if len(events) < 20:
        log(f"Veranstaltungen: nur {len(events)} Einträge erkannt – alte Datei bleibt")
        return
    out = []
    for e in events:
        last = e["end"] or e["start"]
        if last < TODAY:
            continue
        out.append({"start": e["start"].isoformat(),
                    "end": e["end"].isoformat() if e["end"] else None,
                    "title": e["title"], "org": e["org"], "place": e["place"],
                    "importance": importance(e["title"])})
    out.sort(key=lambda x: x["start"])
    write_json("events.json", {"updated": dt.datetime.now().isoformat(timespec="minutes"),
                               "source": "Veranstaltungskalender Stadt Ebersbach an der Fils",
                               "items": out})


# ---------------------------------------------------------------- Nachrichten

import html as htmlmod
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

GN_QUERIES = [
    ("Ebersbach", '"Ebersbach an der Fils"'),
    ("Göppingen", "Göppingen"),
    ("Göppingen", '"Landkreis Göppingen"'),
    ("Göppingen", "Uhingen OR Eislingen OR Faurndau OR Filstal"),
]
NEWS_BLOCK = ["blitzer", "wetter", "stellenangebot", "job", "immobilie", "wohnung", "zu verkaufen", "mieten",
              "stau", "verkehrsmeldung", "baustelle a8", "tierseuchenkasse", "öffentliche zustellung",
              "horoskop", "gewinnspiel", "prospekt", "angebote", "todesanzeige", "traueranzeige",
              "frost", "glätte", "unwetter", "warnung vor", "kammerjäger", "schlüsseldienst", "entrümpelung",
              "umzugsfirma", "reinigungsfirma", "handwerker in", "seo ", "bestatter"]
SPAM_SOURCES = ["businessportal24", "tixio", "openpr", "firmenpresse", "pr-gateway", "prnews24", "pressebox",
                "lokalo24", "news.de", "meinestadt", "dastelefonbuch", "werbung"]
GOOD_SOURCES = ["nwz", "swp", "südwest presse", "swr", "stuttgarter zeitung", "stuttgarter nachrichten",
                "filstalexpress", "stadt ebersbach", "landkreis göppingen", "staatsanzeiger", "esslinger zeitung"]
BLAULICHT = ["unfall", "zusammenstoß", "kollidier", "kollision", "polizei", "feuerwehr", "brand", "verletzt",
             "eisplatten", "lkw", "festgenommen", "einbruch", "diebstahl", "betrunken", "fahrerflucht", "blaulicht"]
SPORT_SOURCES = ["fupa", "kicker", "transfermarkt"]
SPORT = ["frisch auf", "fußball", "handball", "sv ", "fc ", "tsv", "tabelle", "liga", "spieltag", "trainer",
         "torjäger", "derby", "punktspiel", " sieg", "niederlage"]
CITY_NEWS = "https://www.ebersbach.de/nachrichten"


def strip_tags(s):
    return re.sub(r"\s+", " ", htmlmod.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def google_news(query):
    url = ("https://news.google.com/rss/search?q=" + urllib.parse.quote(query + " when:7d")
           + "&hl=de&gl=DE&ceid=DE:de")
    root = ET.fromstring(fetch(url))
    out = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        src_el = it.find("source")
        source = (src_el.text if src_el is not None else "") or ""
        if source and title.endswith(" - " + source):
            title = title[: -len(source) - 3].strip()
        try:
            when = parsedate_to_datetime(it.findtext("pubDate"))
        except Exception:  # noqa: BLE001
            when = None
        out.append({"title": title, "source": source.strip(), "link": it.findtext("link") or "",
                    "date": when.astimezone(dt.timezone.utc).isoformat(timespec="minutes") if when else None})
    return out


def city_news():
    page = fetch(CITY_NEWS).decode("utf-8", "replace")
    m = re.search(r'document="([^"]+)"', page)
    if not m:
        return []
    api = ("https://www.ebersbach.de/api/news/list/news-article?document="
           + urllib.parse.quote(m.group(1)) + "&limit=12&page=1")
    req = urllib.request.Request(api, headers={**UA, "Accept": "application/json",
                                               "X-Requested-With": "XMLHttpRequest"})
    with urllib.request.urlopen(req, timeout=40) as r:
        data = json.loads(r.read().decode("utf-8"))
    out = []
    for art in re.split(r"<article\b", data.get("results") or "")[1:]:
        t = re.search(r"<h[23][^>]*>(.*?)</h[23]>", art, re.S)
        href = re.search(r'href="([^"]+)"', art)
        if not t:
            continue
        link = href.group(1) if href else CITY_NEWS
        # Die Stadt-Links haben absichtlich einen doppelten Schrägstrich (…de//Name-news-article123)
        if link.startswith("//"):
            link = "https://www.ebersbach.de" + link
        elif link.startswith("/"):
            link = "https://www.ebersbach.de/" + link
        out.append({"title": strip_tags(t.group(1)), "source": "Stadt Ebersbach", "link": link, "date": None})
    return out


def words(t):
    return set(w for w in re.findall(r"\w{4,}", t.lower()))


def similar(a, b):
    wa, wb = words(a), words(b)
    if not wa or not wb:
        return False
    return len(wa & wb) / min(len(wa), len(wb)) >= 0.5


def resolve_google_link(link):
    """Google-News-Umleitung in die echte Artikel-Adresse umwandeln (sonst Original behalten)."""
    m = re.search(r"news\.google\.com/(?:rss/)?articles/([^?/]+)", link or "")
    if not m:
        return link
    aid = m.group(1)
    try:
        sig = ts = None
        for url in (f"https://news.google.com/articles/{aid}", f"https://news.google.com/rss/articles/{aid}"):
            page = fetch(url).decode("utf-8", "replace")
            ms = re.search(r'data-n-a-sg="([^"]+)"', page)
            mt = re.search(r'data-n-a-ts="([^"]+)"', page)
            if ms and mt:
                sig, ts = ms.group(1), mt.group(1)
                break
        if not sig:
            return link
        inner = ('["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],'
                 f'"X","X",1,[1,1,1],1,1,null,0,0,null,0],"{aid}",{ts},"{sig}"]')
        body = "f.req=" + urllib.parse.quote(json.dumps([[["Fbv4je", inner, None, "generic"]]]))
        req = urllib.request.Request("https://news.google.com/_/DotsSplashUi/data/batchexecute",
                                     data=body.encode(), method="POST",
                                     headers={**UA, "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"})
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read().decode("utf-8", "replace")
        part = json.loads(text.split("\n\n")[1])
        real = json.loads(part[0][2])[1]
        if isinstance(real, str) and real.startswith("http"):
            return real
    except Exception as e:  # noqa: BLE001
        log("News: Link nicht auflösbar:", e)
    return link


def update_news():
    cands = []
    for region, q in GN_QUERIES:
        try:
            for n in google_news(q):
                n["region"] = region
                cands.append(n)
        except Exception as e:  # noqa: BLE001
            log("News:", q, "fehlgeschlagen:", e)
    try:
        for n in city_news():
            n["region"] = "Ebersbach"
            cands.append(n)
    except Exception as e:  # noqa: BLE001
        log("News: Stadtnachrichten fehlgeschlagen:", e)

    now = dt.datetime.now(dt.timezone.utc)

    def ok(n):
        t = n["title"].lower()
        src = n["source"].lower()
        return (len(n["title"].split()) >= 4 and len(n["title"]) >= 25
                and not any(b in t for b in NEWS_BLOCK)
                and not any(x in src for x in SPAM_SOURCES))

    LOCAL = ["ebersbach", "göpping", "filstal", "fils", "uhingen", "eisling", "faurndau", "schlierbach",
             "plochingen", "roßwälden", "weiler", "bünzwangen", "sulpach", "büchenbronn", "landkreis"]
    # Treffer der Ebersbach-Suche ohne Ortsbezug im Titel (z. B. Unfall bei Ulm) weglassen
    cands = [n for n in cands if n["source"] == "Stadt Ebersbach" or n["region"] != "Ebersbach"
             or any(w in n["title"].lower() for w in LOCAL)]
    for n in cands:
        # „Ebersbach“ nur, wenn es wirklich um Ebersbach geht
        n["region"] = "Ebersbach" if "ebersbach" in n["title"].lower() or n["source"] == "Stadt Ebersbach" \
            else "Göppingen"

    def score(n):
        age_h = 48.0
        if n["date"]:
            age_h = (now - dt.datetime.fromisoformat(n["date"])).total_seconds() / 3600
        s = -age_h
        if n["region"] == "Ebersbach" or "ebersbach" in n["title"].lower():
            s += 36   # Ebersbach vor Göppingen
        if n["source"] == "Stadt Ebersbach":
            s += 6
        if any(x in n["source"].lower() for x in GOOD_SOURCES):
            s += 18   # echte Zeitungen vor Sammelseiten
        return s

    cands = [n for n in cands if ok(n)]
    cands.sort(key=score, reverse=True)
    picked, sport, blau, ebers = [], 0, 0, 0
    goe_left = sum(1 for n in cands if n["region"] == "Göppingen")
    for n in cands:
        if any(similar(n["title"], p["title"]) for p in picked):
            continue
        t = " " + n["title"].lower() + " "
        is_sport = any(w in t for w in SPORT) or any(x in n["source"].lower() for x in SPORT_SOURCES)
        is_blau = any(w in t for w in BLAULICHT)
        if (is_sport and sport >= 1) or (is_blau and blau >= 1):
            continue
        if n["region"] == "Ebersbach" and ebers >= 3 and goe_left:
            continue   # Platz für Göppingen lassen
        sport += is_sport
        blau += is_blau
        ebers += n["region"] == "Ebersbach"
        picked.append(n)
        if len(picked) == 5:
            break
    picked.sort(key=lambda n: (n["region"] != "Ebersbach", -score(n)))
    if len(picked) < 3:
        log(f"News: nur {len(picked)} Meldungen – alte Datei bleibt")
        return
    for p in picked:
        p["link"] = resolve_google_link(p["link"])
    log("News-Links:", [p["link"][:80] for p in picked])
    write_json("news.json", {"updated": dt.datetime.now().isoformat(timespec="minutes"), "items": picked})


if __name__ == "__main__":
    os.makedirs(DATA, exist_ok=True)
    update_abfall()
    update_events()
    update_news()
