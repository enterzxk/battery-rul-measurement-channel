
import os, sys, json, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
# search local corpora for titles of interest
corp = {}
for n in ["openalex.json"]:
    corp[n] = json.load(open(os.path.join(OUT, n), encoding="utf-8"))
keys = ["limited labels and domain adaptation", "survey on few-shot learning for remaining useful life",
        "Masked Autoencoder", "knowledge-guided intelligence", "label-free cross-domain battery",
        "Transferability-Aware Framework"]
for r in corp["openalex.json"]:
    for k in keys:
        if k.lower() in (r["title"] or "").lower():
            print("###", r["title"])
            print("   ", r["year"], r["venue"], r["doi"], "cites=", r["cites"])
            print("   ABS:", (r["abstract"] or "")[:900])
            print()
            break
print("=== crossref_round battery-ish entries ===")
cr = json.load(open(os.path.join(OUT, "crossref_round.json"), encoding="utf-8"))
for d, v in cr.items():
    t = (v["title"] or "").lower()
    if any(k in t for k in ["battery", "soh", "state of health", "remaining useful life", "rul"]):
        print("%s | %s | %s | %s" % (v["year"], v["title"][:95], v["venue"][:30], d))
