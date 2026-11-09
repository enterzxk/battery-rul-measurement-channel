import re
txt = open("peng2026.txt", encoding="utf-8").read()
flat = re.sub(r"\s+", " ", txt)
print("##### factorial")
for m in re.finditer("factorial", flat, re.I):
    s=max(0,m.start()-320); e=min(len(flat), m.end()+320)
    print("  ...", flat[s:e], "...\n")
print("="*70)
print("##### Introduction paragraphs 1-3")
i = flat.find("1. Introduction")
print(flat[i:i+3400])
