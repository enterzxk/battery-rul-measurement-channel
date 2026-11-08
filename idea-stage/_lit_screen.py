
import json, os, re
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
recs = json.load(open(os.path.join(OUT, "openalex.json"), encoding="utf-8"))
print("n=", len(recs))

BATT = r"batter|lithium|li-ion|cell|soh|state of health|remaining useful life|rul|capacity fade|degradation|aging|ageing"
LABEL = r"few-shot|few shot|k-shot|meta-learn|limited label|scarce label|label-efficient|label efficient|active learning|semi-supervised|unlabeled|unlabelled|zero-shot|transfer|domain adapt|domain generali|fine-tun|calibrat|data-efficient|data efficient|sample size|learning curve|limited data|small sample|low-resource|target domain|source domain"

def score(r):
    t = (r["title"] or "").lower(); a = (r["abstract"] or "").lower()
    s = 0
    if re.search(BATT, t): s += 3
    if re.search(LABEL, t): s += 4
    if re.search(LABEL, a): s += 2
    # strong phrases in abstract
    for p, w in [("few-shot", 3), ("few shot", 3), ("number of labeled", 4), ("number of labelled", 4),
                 ("amount of labeled", 4), ("labeled samples", 2), ("labelled samples", 2),
                 ("sample size", 2), ("learning curve", 3), ("how many", 2), ("k = ", 1),
                 ("active learning", 3), ("meta-learning", 2), ("domain adaptation", 2),
                 ("calibration", 1), ("limited labels", 3), ("only a few", 2)]:
        if p in a: s += w
    return s

recs2 = [r for r in recs if re.search(BATT, (r["title"] or "") + " " + (r["abstract"] or ""))]
print("battery-related:", len(recs2))
for r in recs2: r["score"] = score(r)
recs2.sort(key=lambda r: (-r["score"], -(r["year"] or 0)))
with open(os.path.join(OUT, "screened.json"), "w", encoding="utf-8") as f:
    json.dump(recs2, f, ensure_ascii=False, indent=1)
for i, r in enumerate(recs2[:60]):
    print("%2d s=%2d %s | %s | %s | cites=%s" % (i, r["score"], r["year"], (r["title"] or "")[:110], (r["venue"] or "")[:35], r["cites"]))
