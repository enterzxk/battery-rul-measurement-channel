
import os, sys, re, json, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
ax = json.load(open(os.path.join(OUT, "arxiv.json"), encoding="utf-8"))
print("=== arXiv active learning battery ===")
for r in ax:
    if r["query"] == 'all:"battery" AND all:"active learning"':
        print("%s | %s" % (r["published"][:7], r["title"][:120]))
print()
print("=== arXiv 'battery sample size' ===")
for r in ax:
    if r["query"] == 'all:"battery" AND all:"sample size"':
        print("%s | %s" % (r["published"][:7], r["title"][:120]))
