
import os, sys, json, time, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "lit-survey/1.0"})
titles = [
 "A theory of learning from different domains",
 "Frustratingly Easy Domain Adaptation",
 "Accurate uncertainties for deep learning using calibrated regression",
 "Deep learning scaling is predictable empirically",
 "Revisiting the unreasonable effectiveness of data",
 "Machine learning pipeline for battery state-of-health estimation",
 "Data-driven prediction of battery cycle life before capacity degradation",
 "Closed-loop optimization of fast-charging protocols for batteries with machine learning",
 "A comprehensive study on battery aging dataset",
 "Transfer learning for battery state of health estimation review",
 "Few-shot learning for battery state of health: a review",
 "active learning battery aging experiment",
]
for t in titles:
    try:
        j = S.get("https://api.openalex.org/works",
                  params={"search": t, "per-page": 3, "select": "title,doi,publication_year,primary_location,cited_by_count,authorships"},
                  timeout=60).json()
    except Exception as e:
        print("ERR", t, e); continue
    print("Q:", t)
    for w in j.get("results", [])[:2]:
        pl = w.get("primary_location") or {}
        au = [a["author"]["display_name"] for a in (w.get("authorships") or [])[:4]]
        print("   %s | %s | %s | %s | cites=%s" % (w.get("publication_year"), w.get("title")[:100],
              (pl.get("source") or {}).get("display_name"), w.get("doi"), w.get("cited_by_count")))
        print("      ", ", ".join(au))
    time.sleep(0.2)
