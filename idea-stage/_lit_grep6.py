
import os, sys, re, requests, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = os.path.join(os.environ.get("TEMP", "."), "lit_survey")
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

def load(n): return re.sub(r"\s+", " ", open(os.path.join(OUT, n + ".txt"), encoding="utf-8").read())
th = load("chalmers_thesis")
i = th.find("4.4 Sensitivity and Robustness Analyses", 3000)
print("=== Chalmers 4.4 ===")
print(th[i:i+2500] if i>0 else "not found")

print("\n=== DTU metadata via Crossref ===")
j = S.get("https://api.crossref.org/works", params={"query.bibliographic": "data-efficient autoregressive model early prediction battery degradation",
      "rows": 3}, timeout=60).json()
for it in j["message"]["items"]:
    print(" ", (it.get("issued", {}).get("date-parts") or [[None]])[0][0], "|", (it.get("title") or [""])[0][:100],
          "|", (it.get("container-title") or [""])[0][:40], "|", it.get("DOI"),
          "|", ", ".join((a.get("family") or "") for a in it.get("author", [])[:5]))

print("\n=== ETH record page ===")
try:
    r = S.get("https://www.research-collection.ethz.ch/handle/20.500.11850/582225", timeout=60)
    t = re.sub(r"<[^>]+>", " ", r.text); t = re.sub(r"\s+", " ", t)
    m = re.search(r"(Batteries[^|]{0,80})", t)
    print(r.status_code, t[:600])
except Exception as e:
    print("ERR", str(e)[:100])
