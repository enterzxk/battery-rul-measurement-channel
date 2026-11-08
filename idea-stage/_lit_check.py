
import os, sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
bl = re.sub(r"\s+", " ", open(os.path.join(OUT, "batterylife_kdd.txt"), encoding="utf-8").read())
print("3.153 in BatteryLife:", "3.153" in bl, "| 0.515:", "0.515" in bl)
for m in list(re.finditer("3\\.153", bl))[:2]:
    print("...", bl[max(0,m.start()-300):m.start()+300], "...")
bn = re.sub(r"\s+", " ", open(os.path.join(OUT, "batlinet.txt"), encoding="utf-8").read())
for kw in ["64 reference", "batch of 64", "64"]:
    ms = [m for m in re.finditer(kw, bn) if "reference" in bn[max(0,m.start()-80):m.start()+80]]
    for m in ms[:2]:
        print("[%s] ..." % kw, bn[max(0,m.start()-250):m.start()+250], "...")
