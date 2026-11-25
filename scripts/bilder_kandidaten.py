#!/usr/bin/env python3
"""Lädt für jedes Rezept Foto-Kandidaten von Wikimedia Commons (nur zur Auswahl)."""
import json, os, re, sys, time, urllib.parse, urllib.request

UA = {"User-Agent": "Familien-Dashboard/1.0 (github.com/Postmen1971/chanan)"}
OUT = "kandidaten"
SUCHE = {
 "menemen": ["Menemen", "Menemen Turkish breakfast"],
 "mercimek": ["Mercimek çorbası", "Turkish red lentil soup"],
 "koefte": ["Izgara köfte", "Köfte grilled Turkish"],
 "coban": ["Çoban salatası", "Shepherd salad Turkish"],
 "imam": ["İmam bayıldı", "Imam bayildi dish"],
 "tavuk": ["Tavuk şiş", "Chicken shish kebab skewers"],
 "cacik": ["Cacık", "Cacik yogurt cucumber"],
 "fasulye": ["Zeytinyağlı taze fasulye", "Taze fasulye"],
 "karniyarik": ["Karnıyarık", "Karniyarik stuffed eggplant"],
 "levrek": ["Levrek ızgara", "Grilled sea bass fillet"],
 "ezogelin": ["Ezogelin çorbası", "Ezogelin soup"],
 "dolma": ["Biber dolması", "Stuffed peppers Turkish"],
 "linsen": ["Linseneintopf", "Lentil stew German"],
 "lachs": ["Baked salmon with vegetables", "Lachsfilet Gemüse"],
 "frikadellen": ["Frikadellen", "Frikadelle Teller"],
 "gurkensalat": ["Gurkensalat", "Cucumber salad dill"],
 "kohlrouladen": ["Kohlrouladen", "Cabbage rolls German"],
 "haehnchen": ["Chicken breast broccoli", "Grilled chicken breast broccoli plate"],
 "frikassee": ["Hühnerfrikassee", "Chicken fricassee"],
 "zucchinipuffer": ["Zucchini fritters", "Zucchinipuffer"],
 "erbsen": ["Erbseneintopf", "Erbsensuppe Würstchen"],
 "blumenkohl": ["Roasted cauliflower", "Roasted cauliflower florets"],
 "roulade": ["Rinderrouladen Rotkohl", "Rinderroulade"],
 "sucuk": ["Sucuklu yumurta", "Sucuk eggs pan"],
}

def get(url, timeout=40):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()

def commons(q, n=5):
    api = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrnamespace=6"
           f"&gsrlimit={n}&gsrsearch={urllib.parse.quote(q + ' filetype:bitmap')}"
           "&prop=imageinfo&iiprop=url|extmetadata|size&iiurlwidth=800")
    d = json.loads(get(api))
    pages = sorted((d.get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
    out = []
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]
        if not ii.get("thumburl") or ii.get("width", 0) < 500:
            continue
        md = ii.get("extmetadata") or {}
        val = lambda k: re.sub(r"<[^>]+>", "", (md.get(k) or {}).get("value", "")).strip()
        out.append({"title": p["title"], "thumb": ii["thumburl"], "page": ii.get("descriptionurl"),
                    "artist": val("Artist")[:80], "license": val("LicenseShortName")})
    return out

os.makedirs(OUT, exist_ok=True)
index = {}
for key, qs in SUCHE.items():
    seen, k = set(), 0
    index[key] = []
    for q in qs:
        try:
            cands = commons(q)
        except Exception as e:
            print("Fehler", key, q, e, file=sys.stderr); continue
        for c in cands:
            if c["title"] in seen or k >= 6:
                continue
            seen.add(c["title"])
            fn = f"{key}_{k}.jpg"
            try:
                open(os.path.join(OUT, fn), "wb").write(get(c["thumb"]))
            except Exception as e:
                print("Download", fn, e, file=sys.stderr); continue
            c["file"] = fn
            index[key].append(c)
            k += 1
            time.sleep(0.3)
    print(key, k, file=sys.stderr)
json.dump(index, open(os.path.join(OUT, "index.json"), "w"), ensure_ascii=False, indent=1)
