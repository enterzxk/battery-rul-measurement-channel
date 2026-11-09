import re
txt = open("peng2026.txt", encoding="utf-8").read()
flat = re.sub(r"\s+", " ", txt)
terms = ["interaction", "joint", "cross the", "crossed", "factorial", "specification space",
         "dominance", "dominat", "largest", "ranking", "rank", "sensitivity", "multiverse",
         "solely", "one at a time", "one-at-a-time", "separately"]
for t in terms:
    n = flat.lower().count(t.lower())
    print(f"{t!r}: {n}")
print("\n" + "="*70)
for t in ["interaction", "joint", "dominance", "largest", "multiverse", "specification"]:
    print(f"\n##### {t}")
    for m in re.finditer(re.escape(t), flat, re.I):
        s=max(0,m.start()-200); e=min(len(flat), m.end()+200)
        print("  ...", flat[s:e].replace("\n"," "), "...")
