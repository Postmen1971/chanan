import json, os, re, urllib.request, urllib.parse
UA={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36","Accept-Language":"de-DE,de;q=0.9"}
os.makedirs("probe",exist_ok=True)
def get(u,h=None):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers={**UA,**(h or {})}),timeout=40)
        return r.status, r.geturl(), r.read().decode("utf-8","replace")
    except Exception as e:
        return 0, u, "FEHLER "+repr(e)
def save(name,u,h=None):
    st,final,t=get(u,h)
    open(f"probe/{name}.txt","w").write(f"URL {u}\nFINAL {final}\nSTATUS {st}\nLEN {len(t)}\n\n"+t[:200000])
    return t
save("goe_kalender","https://eventkalender.erlebe-dein-goeppingen.de/eventkalender")
save("goe_event","https://eventkalender.erlebe-dein-goeppingen.de/h2suz6b91v")
save("goe_erlebe","https://www.erlebe-dein-goeppingen.de/veranstaltungskalender")
save("rausgegangen","https://rausgegangen.de/goppingen/")
save("goe_stadt","https://www.goeppingen.de/")
page=save("eb_veranst","https://www.ebersbach.de/veranstaltung")
m=re.search(r'document="([^"]+)"',page)
if m:
    from datetime import date
    api=("https://www.ebersbach.de/api/event/list/event-appointment?document="+urllib.parse.quote(m.group(1))
         +"&limit=24&page=1&filters[date][from]="+urllib.parse.quote(date.today().isoformat()+" 00:00:00"))
    t=save("eb_api",api,{"Accept":"application/json","X-Requested-With":"XMLHttpRequest"})
    try:
        html=json.loads(t)["results"]
        links=re.findall(r'href="([^"]+)"',html)
        open("probe/eb_links.txt","w").write("\n".join(links[:40]))
        det=[l for l in links if "event" in l][:1]
        if det:
            u=det[0] if det[0].startswith("http") else "https://www.ebersbach.de"+("/" if not det[0].startswith("/") else "")+det[0]
            save("eb_detail",u)
    except Exception as e:
        open("probe/eb_err.txt","w").write(repr(e))
news=json.load(open("data/news.json"))["items"]
for i,n in enumerate(news[:5]):
    save(f"news_{i}",n["link"])
