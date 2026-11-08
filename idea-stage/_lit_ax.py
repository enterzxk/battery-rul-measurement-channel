
import json, os, re
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
ax = json.load(open(os.path.join(OUT, "arxiv.json"), encoding="utf-8"))
BATT = re.compile(r"batter|lithium|li-ion|cell|soh|state of health|remaining useful life|rul|capacity", re.I)
seen = set(); n = 0
print("======= arXiv battery-related =======")
for r in ax:
    if not BATT.search(r["title"]): continue
    if r["title"] in seen: continue
    seen.add(r["title"]); n += 1
    print("%s | %s" % (r["published"][:7], r["title"][:120]))
    print("    ", r["id"])
print("count:", n)
print()
print("======= arXiv 'label budget' / few-shot regression (non-battery ML) =======")
for r in ax:
    if r["query"] in ('all:"label budget"', 'all:"few-shot regression"', 'all:"learning curve" AND all:"transfer"'):
        if BATT.search(r["title"]): continue
        if r["title"] in seen: continue
        seen.add(r["title"])
        print("%s | %s" % (r["published"][:7], r["title"][:120]))
