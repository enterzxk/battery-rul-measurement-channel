
import json, os, time, re, urllib.parse
import requests
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
os.makedirs(OUT, exist_ok=True)
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "lit-survey/1.0"})

def inv2text(inv):
    if not inv: return ""
    pos = {}
    for w, idxs in inv.items():
        for i in idxs: pos[i] = w
    return " ".join(pos[i] for i in sorted(pos))

Q2 = [
 # label count as explicit variable
 "number of labeled samples battery state of health",
 "effect of training data size battery state of health estimation",
 "how much data battery lifetime prediction model needs",
 "learning curve battery capacity estimation number of cells",
 "shots few-shot battery state of health number of samples",
 # benchmarks
 "BatteryLife benchmark battery life prediction",
 "cross-condition generalization battery state of health evaluation",
 "benchmarking battery state of health estimation generalization",
 # calibration / bias correction
 "calibration transfer regression model limited target labels",
 "bias correction domain shift regression few samples",
 "linear probe fine-tuning few labels regression transfer",
 "prior correction regression model new operating condition",
 # theory
 "theory of learning from different domains labeled target samples bound",
 "sample complexity domain adaptation target labels",
 "active learning regression label cost",
]
recs = json.load(open(os.path.join(OUT, "openalex.json"), encoding="utf-8"))
by_doi = {(r["doi"] or ""): r for r in recs}
new = 0
for q in Q2:
    params = {"search": q, "per-page": 25, "sort": "relevance_score:desc",
              "select": "id,doi,title,publication_year,cited_by_count,primary_location,authorships,abstract_inverted_index"}
    try:
        j = S.get("https://api.openalex.org/works", params=params, timeout=60).json()
    except Exception as e:
        print("ERR", q, e); continue
    for w in j.get("results", []):
        d = w.get("doi") or w.get("id")
        if d in by_doi: continue
        pl = w.get("primary_location") or {}
        rec = {"doi": w.get("doi"), "title": w.get("title"), "year": w.get("publication_year"),
               "cites": w.get("cited_by_count"), "venue": (pl.get("source") or {}).get("display_name"),
               "authors": [a["author"]["display_name"] for a in (w.get("authorships") or [])[:8]],
               "abstract": inv2text(w.get("abstract_inverted_index")), "tags": ["R2"], "queries": [q]}
        recs.append(rec); by_doi[d] = rec; new += 1
    time.sleep(0.25)
print("new:", new, "total:", len(recs))
json.dump(recs, open(os.path.join(OUT, "openalex.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---- arXiv ----
AX = "http://export.arxiv.org/api/query"
aq = [
 'all:"battery" AND all:"few-shot"',
 'all:"battery" AND all:"label" AND all:"budget"',
 'all:"battery" AND all:"transfer learning" AND all:"state of health"',
 'all:"battery" AND all:"sample size"',
 'all:"battery" AND all:"active learning"',
 'all:"few-shot regression"',
 'all:"label budget"',
 'all:"learning curve" AND all:"transfer"',
]
import xml.etree.ElementTree as ET
ns = {"a": "http://www.w3.org/2005/Atom"}
out = []
for q in aq:
    try:
        r = S.get(AX, params={"search_query": q, "start": 0, "max_results": 40}, timeout=60)
        root = ET.fromstring(r.text)
    except Exception as e:
        print("AXERR", q, e); continue
    n = 0
    for e in root.findall("a:entry", ns):
        t = " ".join(e.find("a:title", ns).text.split())
        s = " ".join(e.find("a:summary", ns).text.split())
        out.append({"query": q, "title": t, "summary": s,
                    "published": e.find("a:published", ns).text,
                    "id": e.find("a:id", ns).text})
        n += 1
    print("arxiv", q, "->", n)
    time.sleep(3)
json.dump(out, open(os.path.join(OUT, "arxiv.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("arxiv total:", len(out))
