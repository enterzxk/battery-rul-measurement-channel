
import os, sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
th = re.sub(r"\s+", " ", open(os.path.join(OUT, "chalmers_thesis.txt"), encoding="utf-8").read())
for kw in ["three target", "3 target", "fine-tuning cells were", "number of fine-tuning cells", "limited target", "small number of target"]:
    for m in list(re.finditer(kw, th, re.I))[:3]:
        print("[%s] ..." % kw, th[max(0,m.start()-260):m.start()+320], "...\n")
print("=== thesis abstract ===")
i = th.find("Abstract")
print(th[i:i+1200])
