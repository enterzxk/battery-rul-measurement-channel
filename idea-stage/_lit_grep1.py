
import os, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
def load(n): return re.sub(r"\s+", " ", open(os.path.join(OUT, n + ".txt"), encoding="utf-8").read())

bl = load("batterylife_kdd")
print("### BatteryLife 'shot' context")
for m in re.finditer("shot", bl, re.I):
    print("...", bl[max(0,m.start()-250):m.start()+250], "...\n")

print("\n### BatteryLife: does it vary training data amount? search 'data size'/'number of cells'/'amount of'")
for kw in ["data size", "amount of data", "number of training", "training data", "data efficiency"]:
    for m in list(re.finditer(kw, bl, re.I))[:2]:
        print("[%s] ..." % kw, bl[max(0,m.start()-200):m.start()+260], "...\n")

bn = load("batlinet")
print("\n### BatLiNet 'shot' context")
for m in re.finditer("shot", bn, re.I):
    print("...", bn[max(0,m.start()-250):m.start()+250], "...\n")
print("### BatLiNet reference-cell count passages")
for m in list(re.finditer("reference cell", bn, re.I))[:6]:
    print("...", bn[max(0,m.start()-200):m.start()+260], "...\n")
