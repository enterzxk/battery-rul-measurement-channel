
import os, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
def load(n): return re.sub(r"\s+", " ", open(os.path.join(OUT, n + ".txt"), encoding="utf-8").read())

a = load("arxiv_2107_sample_size")
print("=== 2107.07881 head ===")
print(a[:2200])
print("\n=== key terms ===")
for kw in ["sample size", "how many", "cells are required", "confidence interval", "we find that"]:
    ms = list(re.finditer(kw, a, re.I))[:3]
    for m in ms:
        print("[%s] ..." % kw, a[max(0,m.start()-220):m.start()+320], "...\n")

c = load("arxiv_2603_conformal_transfer")
print("\n=== 2603.24475 head ===")
print(c[:1800])
print("\n=== calibration size? ===")
for kw in ["calibration", "few-shot", "number of", "label"]:
    ms = list(re.finditer(kw, c, re.I))[:3]
    for m in ms:
        print("[%s] ..." % kw, c[max(0,m.start()-200):m.start()+280], "...\n")
