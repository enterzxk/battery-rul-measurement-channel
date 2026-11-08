
import os, sys, re, requests, time
import xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "lit-survey/1.0 (mailto:a@b.c)"})
ns = {"a": "http://www.w3.org/2005/Atom"}
print("=== arXiv id checks ===")
for aid in ["1807.00263", "1703.03400", "2211.05697", "2402.00068", "2107.07881"]:
    try:
        r = S.get("http://export.arxiv.org/api/query", params={"id_list": aid}, timeout=60)
        root = ET.fromstring(r.text)
        e = root.find("a:entry", ns)
        t = " ".join(e.find("a:title", ns).text.split())
        au = [x.find("a:name", ns).text for x in e.findall("a:author", ns)][:4]
        print(" %s | %s | %s" % (aid, t[:95], ", ".join(au)))
    except Exception as ex:
        print(" ERR", aid, str(ex)[:80])
    time.sleep(3)

print("\n=== Crossref title checks ===")
for q in ["Battery health prediction under data scarcity cross-domain physics-informed 5-shot framework GRU-Transformer",
          "Physics-aligned transfer learning for cross-condition remaining useful life prediction",
          "A survey on few-shot learning for remaining useful life prediction",
          "Rapid health estimation of in-service battery packs based on limited labels and domain adaptation"]:
    try:
        j = S.get("https://api.crossref.org/works", params={"query.bibliographic": q, "rows": 2}, timeout=60).json()
        print("Q:", q[:60])
        for it in j["message"]["items"]:
            print("   %s | %s | %s | %s" % ((it.get("issued", {}).get("date-parts") or [[None]])[0][0],
                  (it.get("title") or [""])[0][:90], (it.get("container-title") or [""])[0][:35], it.get("DOI")))
    except Exception as ex:
        print(" ERR", str(ex)[:80])
    time.sleep(0.5)
