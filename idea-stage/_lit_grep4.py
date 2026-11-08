
import os, sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
def load(n): return re.sub(r"\s+", " ", open(os.path.join(OUT, n + ".txt"), encoding="utf-8").read())
th = load("chalmers_thesis")
print("=== Chalmers thesis ===")
for kw in ["number of cells", "training cells", "labeled cells", "k = ", "shots", "how many"]:
    for m in list(re.finditer(kw, th, re.I))[:3]:
        print("[%s] ..." % kw, th[max(0,m.start()-240):m.start()+320], "...\n")
dt = load("dtu_data_efficient")
print("\n=== DTU paper ===")
print(dt[:600])
for kw in ["how much data", "number of cells", "training set size", "data efficiency"]:
    for m in list(re.finditer(kw, dt, re.I))[:3]:
        print("[%s] ..." % kw, dt[max(0,m.start()-220):m.start()+300], "...\n")
