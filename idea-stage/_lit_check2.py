
import os, sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
bn = re.sub(r"\s+", " ", open(os.path.join(OUT, "batlinet.txt"), encoding="utf-8").read())
i = bn.find("Fig. 5 | Analysis of reference cell selection")
print("=== Fig 5 caption ===")
print(bn[i:i+1400])
print("\n=== preceding text ===")
print(bn[max(0,i-1800):i])
