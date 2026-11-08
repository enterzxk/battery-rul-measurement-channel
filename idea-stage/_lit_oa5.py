
import os, sys, json, time, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "lit-survey/1.0 (mailto:a@b.c)"})

def inv2text(inv):
    if not inv: return ""
    pos = {}
    for w, idxs in inv.items():
        for i in idxs: pos[i] = w
    return " ".join(pos[i] for i in sorted(pos))

Q = [
 "minimum data required battery state of health estimation",
 "number of training cells battery life prediction",
 "small sample battery health estimation deep learning",
 "learning curve battery degradation prediction accuracy",
 "transfer learning how many samples target domain battery",
 "label shift battery state of health",
 "annotation cost battery health labels",
 "cross condition battery remaining useful life generalization evaluation",
 "HUST battery dataset state of health",
 "data volume effect deep learning battery capacity estimation",
]
seen = {}
for q in Q:
    for attempt in range(3):
        r = S.get("https://api.openalex.org/works", params={"search": q, "per-page": 15,
                 "select": "title,doi,publication_year,cited_by_count,primary_location,authorships,abstract_inverted_index"},
                 timeout=60)
        if r.status_code == 200: break
        time.sleep(4)
    if r.status_code != 200:
        print("FAIL", q, r.status_code); continue
    j = r.json()
    print("\n### Q:", q, "count=", j.get("meta", {}).get("count"))
    for w in j.get("results", [])[:12]:
        pl = w.get("primary_location") or {}
        print("  %s | %s | %s | c=%s" % (w.get("publication_year"), (w.get("title") or "")[:105],
              ((pl.get("source") or {}).get("display_name") or "")[:30], w.get("cited_by_count")))
        seen[w.get("doi") or w.get("title")] = w
    time.sleep(1.2)
json.dump({k: {"title": v.get("title"), "doi": v.get("doi"), "year": v.get("publication_year"),
               "venue": ((v.get("primary_location") or {}).get("source") or {}).get("display_name"),
               "abstract": inv2text(v.get("abstract_inverted_index"))} for k, v in seen.items()},
          open(os.path.join(OUT, "round3.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
