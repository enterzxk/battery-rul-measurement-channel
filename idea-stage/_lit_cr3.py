
import os, sys, json, time, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "lit-survey/1.0 (mailto:a@b.c)"})
Q = [
 "few-shot battery state of health estimation",
 "few-shot battery remaining useful life",
 "label-efficient battery state of health",
 "active learning battery state of health estimation",
 "sample size battery degradation test cells required",
 "number of labeled samples transfer learning battery",
 "domain adaptation battery state of health limited target labels",
 "semi-supervised battery state of health few labels",
 "learning curve data efficiency battery lifetime prediction",
 "k-shot battery state of health",
]
out = {}
for q in Q:
    try:
        j = S.get("https://api.crossref.org/works", params={"query.bibliographic": q, "rows": 15},
                  timeout=90).json()
    except Exception as e:
        print("ERR", q, str(e)[:80]); continue
    print("\n### Q:", q)
    for it in j.get("message", {}).get("items", []):
        try:
            t = (it.get("title") or [""])[0]
            if not t: continue
            yr = (it.get("issued", {}).get("date-parts") or [[None]])[0][0]
            ct = (it.get("container-title") or [""])
            ct = ct[0] if ct else ""
            d = it.get("DOI")
            print("  %s | %s | %s | %s" % (yr, t[:98], ct[:26], d))
            out[d] = {"title": t, "year": yr, "venue": ct,
                      "authors": [(a.get("family") or "") + " " + (a.get("given") or "")[:1] for a in (it.get("author") or [])[:6]],
                      "abstract": it.get("abstract") or "", "cites": it.get("cited-by-count")}
        except Exception as e:
            continue
    time.sleep(0.6)
json.dump(out, open(os.path.join(OUT, "crossref_round.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nsaved", len(out))
