
import json, time, sys, os, urllib.parse, re
import requests

OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
os.makedirs(OUT, exist_ok=True)
S = requests.Session()
S.headers.update({"User-Agent": "lit-survey/1.0 (mailto:research@example.org)"})
S.trust_env = False

OA = "https://api.openalex.org/works"

QUERIES = {
 "D1_fewshot": [
   "few-shot battery state of health estimation",
   "few-shot remaining useful life lithium battery",
   "meta-learning battery state of health few-shot",
   "k-shot calibration battery state of health",
 ],
 "D2_domain_adapt": [
   "domain adaptation battery state of health operating condition",
   "transfer learning battery remaining useful life operating conditions",
   "unsupervised domain adaptation battery capacity estimation",
   "domain generalization battery health estimation",
 ],
 "D3_active": [
   "active learning battery state of health",
   "label-efficient battery health estimation",
   "data-efficient battery lifetime prediction",
   "sample selection battery aging experiment design",
 ],
 "D4_sample_complexity": [
   "sample size learning curve remaining useful life prediction",
   "training data size battery cycle life prediction accuracy",
   "data requirement machine learning battery lifetime prediction",
 ],
 "D5_calibration": [
   "transfer calibration regression model new domain few labels",
   "bias correction pretrained model domain shift regression",
   "few-shot regression adaptation calibration",
   "test-time adaptation regression distribution shift",
 ],
 "D6_benchmark": [
   "battery life prediction benchmark cross-condition",
   "cross-domain battery state of health benchmark",
   "generalization battery degradation dataset benchmark",
 ],
 "D7_ml_general": [
   "learning curve sample efficiency transfer learning regression",
   "how many labels fine-tuning target domain",
   "sample complexity domain adaptation labeled target samples",
 ],
}

def inv2text(inv):
    if not inv: return ""
    pos = {}
    for w, idxs in inv.items():
        for i in idxs: pos[i] = w
    return " ".join(pos[i] for i in sorted(pos))

allrec = {}
log = []
for tag, qs in QUERIES.items():
    for q in qs:
        params = {"search": q, "per-page": 25, "sort": "relevance_score:desc",
                  "select": "id,doi,title,publication_year,cited_by_count,primary_location,authorships,abstract_inverted_index,type"}
        try:
            r = S.get(OA, params=params, timeout=60)
            j = r.json()
        except Exception as e:
            log.append((tag, q, "ERR " + str(e))); continue
        n = 0
        for w in j.get("results", []):
            did = (w.get("doi") or w.get("id"))
            rec = allrec.get(did)
            if rec is None:
                pl = w.get("primary_location") or {}
                src = (pl.get("source") or {}).get("display_name")
                auth = [a["author"]["display_name"] for a in (w.get("authorships") or [])[:8]]
                rec = {"doi": w.get("doi"), "title": w.get("title"), "year": w.get("publication_year"),
                       "cites": w.get("cited_by_count"), "venue": src, "authors": auth,
                       "abstract": inv2text(w.get("abstract_inverted_index")), "tags": [], "queries": []}
                allrec[did] = rec
            if tag not in rec["tags"]: rec["tags"].append(tag)
            if q not in rec["queries"]: rec["queries"].append(q)
            n += 1
        log.append((tag, q, "ok %d" % n))
        time.sleep(0.25)

with open(os.path.join(OUT, "openalex.json"), "w", encoding="utf-8") as f:
    json.dump(list(allrec.values()), f, ensure_ascii=False, indent=1)
with open(os.path.join(OUT, "openalex_log.txt"), "w", encoding="utf-8") as f:
    for t in log: f.write(" | ".join(t) + "\n")

print("total unique:", len(allrec))
for t in log: print(t[0], "|", t[1][:60], "|", t[2])