
import os, sys, re, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "lit-survey/1.0 (mailto:a@b.c)"})
j = S.get("https://api.crossref.org/works/10.3390/batteries8120204", timeout=60).json()["message"]
print("ETH/MDPI paper:", (j.get("title") or [""])[0], "|", (j.get("container-title") or [""])[0],
      "|", (j.get("issued", {}).get("date-parts") or [[None]])[0][0])
print("authors:", ", ".join((a.get("family") or "") for a in j.get("author", [])))

def load(n): return re.sub(r"\s+", " ", open(os.path.join(OUT, n + ".txt"), encoding="utf-8").read())
th = load("chalmers_thesis")
print("\n=== Chalmers thesis: label-count experiments ===")
for kw in ["number of cells", "training cells", "labeled cells", "k =", "shots", "fine-tun"]:
    ms = list(re.finditer(kw, th, re.I))[:4]
    for m in ms:
        print("[%s] ..." % kw, th[max(0,m.start()-220):m.start()+300], "...\n")
