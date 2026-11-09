import re
txt = open("peng2026.txt", encoding="utf-8").read()
flat = re.sub(r"\s+", " ", txt)
for pat in ["108", "5.3", "4.5", "16.8", "19.1", "4.3%", "10.4"]:
    print("="*70)
    print(f"### PATTERN: {pat}   (count={flat.count(pat)})")
    for m in re.finditer(re.escape(pat), flat):
        s = max(0, m.start()-260); e = min(len(flat), m.end()+260)
        print("  ...", flat[s:e], "...")
        print("  " + "-"*60)
