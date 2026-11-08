
import os, sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
def load(n): return re.sub(r"\s+", " ", open(os.path.join(OUT, n + ".txt"), encoding="utf-8").read())
th = load("chalmers_thesis")
i = th.find("2.5.3 Sensitivity to Fine-Tuning Battery Selection")
print("=== Chalmers 2.5.3 ===")
print(th[i:i+1600])
print("\n=== Chalmers: fine-tune size results ===")
for kw in ["number of fine-tuning", "fine-tuning cells", "one cell", "three cells", "five cells", "k = 1", "1, 3, 5"]:
    for m in list(re.finditer(kw, th, re.I))[:3]:
        print("[%s] ..." % kw, th[max(0,m.start()-250):m.start()+320], "...\n")
dt = load("dtu_data_efficient")
print("\n=== DTU number of batteries sweep ===")
j = dt.find("number of batteries in the training")
print(dt[max(0,j-600):j+1400])
