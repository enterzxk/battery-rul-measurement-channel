
import os, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
t = open(os.path.join(OUT, "when_labels_shift.txt"), encoding="utf-8").read()
t2 = re.sub(r"\s+", " ", t)
def ctx(kw, w=300, maxn=6):
    print("#####", kw)
    for i, m in enumerate(re.finditer(kw, t2, re.I)):
        if i >= maxn: break
        print("...", t2[max(0,m.start()-w):m.start()+w], "...")
        print()
for k in ["shot", "budget"]:
    ctx(k, 300, 6)
