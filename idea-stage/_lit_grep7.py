
import os, sys, re, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "lit-survey/1.0 (mailto:a@b.c)"})
try:
    j = S.get("https://api.crossref.org/works/10.1039/d2dd00067a", timeout=60).json()["message"]
    print("DTU/RSC:", (j.get("title") or [""])[0])
    print("  ", (j.get("container-title") or [""])[0], (j.get("issued", {}).get("date-parts") or [[None]])[0][0])
    print("  ", ", ".join((a.get("given","")[:1] + ". " + (a.get("family") or "")) for a in j.get("author", [])))
except Exception as e:
    print("ERR", str(e)[:120])

def load(n): return re.sub(r"\s+", " ", open(os.path.join(OUT, n + ".txt"), encoding="utf-8").read())
th = load("chalmers_thesis")
print("\n=== Chalmers: 5.6 body ===")
occ = [m.start() for m in re.finditer("Influence of Fine-Tuning Cell Selection", th)]
print("occurrences:", len(occ))
if len(occ) > 1:
    print(th[occ[-1]:occ[-1]+1800])
print("\n=== Chalmers: 'random target-cell' ===")
for m in list(re.finditer("random", th, re.I))[:8]:
    seg = th[max(0,m.start()-200):m.start()+260]
    if "cell" in seg.lower():
        print("...", seg, "...\n")
