
import os, sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
t = re.sub(r"\s+", " ", open(os.path.join(OUT, "when_labels_shift.txt"), encoding="utf-8").read())
i = t.find("Table 1")
print("=== around Table 1 ===")
print(t[max(0,i-200):i+2200])
print("\n=== k results mentions ===")
for m in re.finditer(r"k\s*=\s*(5|10|20)", t):
    print("...", t[max(0,m.start()-260):m.start()+300], "...\n")
