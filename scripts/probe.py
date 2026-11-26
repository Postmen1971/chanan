import json, os, re, urllib.request, urllib.parse
UA={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36","Accept-Language":"de-DE,de;q=0.9"}
os.makedirs("probe2",exist_ok=True)
def get(u,h=None):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers={**UA,**(h or {})}),timeout=40)
        return r.status, r.geturl(), r.read().decode("utf-8","replace")
    except Exception as e:
        return 0, u, "FEHLER "+repr(e)
def save(name,u,t=None,h=None):
    st,final,t=get(u,h)
    open(f"probe2/{name}.txt","w").write(f"URL {u}\nFINAL {final}\nSTATUS {st}\nLEN {len(t)}\n\n"+t[:150000])
    return t
# Göppingen: Struktur der großen Seite
st,fin,big=get("https://eventkalender.erlebe-dein-goeppingen.de/eventkalender")
out=[f"LEN {len(big)}"]
for m in re.finditer(r"<script\b[^>]*>(.*?)</script>", big, re.S):
    out.append(f"SCRIPT len={len(m.group(1))} start={m.start()} head={m.group(1)[:300]!r}")
for kw in ["h2suz6b91v","Stadtführungen","Historische","12.12.2026","2026-12","\"title\"","\"start\"","dates"]:
    i=big.find(kw); out.append(f"KW {kw} at {i}: {big[max(0,i-400):i+600]!r}" if i>=0 else f"KW {kw} none")
open("probe2/goe_struktur.txt","w").write("\n\n".join(out))
open("probe2/goe_tail.txt","w").write(big[-60000:])
# Ebersbach Detailseiten mit doppeltem Schrägstrich
save("eb_detail_dd","https://www.ebersbach.de//Adventskonzert-event-appointment3680")
save("eb_detail_single","https://www.ebersbach.de/Adventskonzert-event-appointment3680")
save("eb_news_dd","https://www.ebersbach.de//40-Millionen-Euro-fuer-das-Raichberg-Schulzentrum-Was-die-Machbarkeitsstudie-zeigt-und-wie-es-weitergeht-article4956")
# Göppingen Stadtseite: Veranstaltungs-Links
st,fin,g=get("https://www.goeppingen.de/start.html")
links=sorted(set(re.findall(r'href="([^"]*(?:eranstalt|vent|alender)[^"]*)"',g)))
open("probe2/goe_stadt_links.txt","w").write("\n".join(links))
