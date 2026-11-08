
import os, sys, json, re, time, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "lit-survey/1.0"})
recs = json.load(open(os.path.join(OUT, "openalex.json"), encoding="utf-8"))
for r in recs:
    if "3460418.3480409" in (r["doi"] or ""):
        print("FULL ABSTRACT (OpenAlex):")
        print(r["abstract"])
print("\n--- arXiv search Semi-JDOT ---")
import xml.etree.ElementTree as ET
ns = {"a": "http://www.w3.org/2005/Atom"}
for q in ['all:"Semi-JDOT"', 'all:"cross domain" AND all:"battery capacity"', 'all:"battery" AND all:"domain adaptation"']:
    try:
        r = S.get("http://export.arxiv.org/api/query", params={"search_query": q, "max_results": 20}, timeout=60)
        root = ET.fromstring(r.text)
        print("Q:", q)
        for e in root.findall("a:entry", ns):
            print("   ", e.find("a:published", ns).text[:7], "|", " ".join(e.find("a:title", ns).text.split())[:110])
    except Exception as ex:
        print("ERR", q, ex)
    time.sleep(3)
