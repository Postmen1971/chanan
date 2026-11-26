#!/usr/bin/env python3
"""Lädt für jedes Rezept Foto-Kandidaten von Wikimedia Commons (nur zur Auswahl)."""
import json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

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
 'mercimekkoefte': ['Mercimek köftesi', 'Turkish lentil balls'],
 'kisir': ['Kısır', 'Kisir bulgur salad'],
 'pirasa': ['Zeytinyağlı pırasa', 'Pırasa yemeği'],
 'enginar': ['Zeytinyağlı enginar', 'Artichoke Turkish olive oil'],
 'ispanak': ['Ispanak yemeği', 'Spinach with minced meat Turkish'],
 'kurufasulye': ['Kuru fasulye', 'Turkish white bean stew'],
 'nohut': ['Nohut yemeği', 'Chickpea stew Turkish'],
 'tuerlue': ['Türlü', 'Turkish vegetable stew'],
 'musakka': ['Patlıcan musakka', 'Turkish moussaka eggplant'],
 'muecver': ['Mücver', 'Mucver zucchini fritters'],
 'tavuksote': ['Tavuk sote', 'Chicken sauté Turkish'],
 'cilbir': ['Çılbır', 'Cilbir poached eggs yogurt'],
 'saksuka': ['Şakşuka', 'Turkish saksuka eggplant'],
 'yayla': ['Yayla çorbası', 'Turkish yogurt soup'],
 'domatescorba': ['Domates çorbası', 'Tomato soup bowl'],
 'tavukcorba': ['Tavuk çorbası', 'Chicken soup bowl lemon'],
 'huenkar': ['Hünkâr beğendi', 'Hunkar begendi'],
 'izmirkoefte': ['İzmir köfte', 'Izmir kofte'],
 'kuzusis': ['Kuzu şiş', 'Lamb shish kebab'],
 'adana': ['Adana kebabı', 'Adana kebab'],
 'piyaz': ['Piyaz', 'Piyaz bean salad'],
 'gavurdagi': ['Gavurdağı salatası', 'Gavurdagi salad'],
 'patlicansalata': ['Patlıcan salatası', 'Turkish eggplant salad'],
 'haydari': ['Haydari', 'Haydari yogurt dip'],
 'muhammara': ['Muhammara', 'Muhammara dip'],
 'barbunya': ['Barbunya pilaki', 'Barbunya beans'],
 'bugulama': ['Balık buğulama', 'Steamed fish Turkish tomatoes'],
 'hamsi': ['Hamsi tava', 'Fried anchovies Turkish'],
 'uskumru': ['Uskumru ızgara', 'Grilled mackerel'],
 'kabakdolma': ['Kabak dolması', 'Stuffed zucchini Turkish'],
 'lahana': ['Lahana sarması', 'Turkish cabbage rolls'],
 'sarma': ['Yaprak sarma', 'Stuffed grape leaves'],
 'bamya': ['Bamya yemeği', 'Okra stew'],
 'bezelye': ['Bezelye yemeği', 'Peas stew Turkish'],
 'firintavuk': ['Fırında tavuk', 'Roast chicken legs vegetables'],
 'ispanakliyumurta': ['Ispanaklı yumurta', 'Spinach eggs pan'],
 'lahmacun': ['Lahmacun', 'Lahmacun Turkish pizza'],
 'kanat': ['Chicken wings air fryer', 'Grilled chicken wings'],
 'gulaschsuppe': ['Gulaschsuppe', 'Goulash soup bowl'],
 'huehnersuppe': ['Hühnersuppe', 'Chicken vegetable soup'],
 'kuerbissuppe': ['Kürbissuppe', 'Pumpkin soup bowl'],
 'brokkolisuppe': ['Broccoli soup', 'Brokkolisuppe'],
 'wirsing': ['Wirsingeintopf', 'Savoy cabbage stew'],
 'bohneneintopf': ['Bohneneintopf', 'Green bean stew'],
 'gemuesesuppe': ['Gemüsesuppe', 'Vegetable soup bowl'],
 'kassler': ['Kassler Sauerkraut', 'Sauerkraut Kassler'],
 'schweinefilet': ['Schweinefilet Champignons', 'Pork tenderloin mushrooms'],
 'putengeschnetzeltes': ['Putengeschnetzeltes', 'Turkey strips sauce'],
 'schnitzel': ['Schnitzel', 'Chicken schnitzel'],
 'hackbraten': ['Hackbraten', 'Meatloaf German'],
 'klopse': ['Königsberger Klopse', 'Königsberger Klopse Kapern'],
 'gulasch': ['Rindergulasch', 'Beef goulash'],
 'tafelspitz': ['Tafelspitz', 'Tafelspitz Meerrettich'],
 'forelle': ['Forelle', 'Baked trout'],
 'kabeljau': ['Kabeljau Senfsoße', 'Cod fillet mustard sauce'],
 'matjes': ['Matjes', 'Matjes Hering'],
 'fischfrikadellen': ['Fischfrikadellen', 'Fish cakes'],
 'seelachs': ['Seelachs', 'Pollock fillet baked'],
 'spinatei': ['Spinat Spiegelei', 'Creamed spinach fried egg'],
 'ruehreilachs': ['Rührei Lachs', 'Scrambled eggs smoked salmon'],
 'bauernfruehstueck': ['Bauernfrühstück', "German farmer's breakfast"],
 'krautsalat': ['Krautsalat', 'Coleslaw cabbage salad'],
 'feldsalat': ['Feldsalat', "Lamb's lettuce salad chicken"],
 'rotebete': ['Rote Bete Salat', 'Beetroot salad feta'],
 'wurstsalat': ['Wurstsalat', 'Swabian sausage salad'],
 'eiersalat': ['Eiersalat', 'Egg salad'],
 'zucchinifeta': ['Gefüllte Zucchini', 'Stuffed zucchini feta'],
 'rosenkohl': ['Rosenkohl', 'Roasted Brussels sprouts'],
 'gruenkohl': ['Grünkohl', 'Kale stew German'],
 'spitzkohl': ['Spitzkohl', 'Pointed cabbage minced meat'],
 'kohlrabi': ['Kohlrabi', 'Kohlrabi slices'],
 'champignons': ['Gefüllte Champignons', 'Stuffed mushrooms'],
 'ofenkuerbis': ['Roasted pumpkin', 'Ofenkürbis'],
 'spargel': ['Spargel Schinken', 'White asparagus ham'],
 'maultaschen': ['Maultaschen', 'Maultaschen Brühe'],
 'linsensalat': ['Linsensalat', 'Lentil salad feta'],
}

def get(url, timeout=40):
    for versuch in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and versuch < 5:
                time.sleep(10 * (versuch + 1)); continue
            raise

def commons(q, n=4):
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
ip = os.path.join(OUT, "index.json")
index = json.load(open(ip)) if os.path.exists(ip) else {}
for key, qs in SUCHE.items():
    if index.get(key):
        continue   # schon vorhanden
    seen, k = set(), 0
    index[key] = []
    for q in qs:
        try:
            cands = commons(q)
        except Exception as e:
            print("Fehler", key, q, e, file=sys.stderr); continue
        for c in cands:
            if c["title"] in seen or k >= 5:
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
            time.sleep(2)
    print(key, k, file=sys.stderr)
json.dump(index, open(os.path.join(OUT, "index.json"), "w"), ensure_ascii=False, indent=1)
