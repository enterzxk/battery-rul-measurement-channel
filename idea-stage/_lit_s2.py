
import os, sys, json, time, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "lit-survey/1.0"})
dois = ["10.1109/tte.2024.3470551", "10.1109/tpel.2025.3538469", "10.1109/taes.2025.3540806",
        "10.1109/tii.2026.3658872", "10.1109/tpel.2024.3398063", "10.1145/3460418.3480409",
        "10.1016/j.esci.2024.100280", "10.1016/j.egyai.2025.100575"]
try:
    r = S.post("https://api.semanticscholar.org/graph/v1/paper/batch",
               params={"fields": "title,abstract,year,venue,externalIds,citationCount"},
               json={"ids": ["DOI:" + d for d in dois]}, timeout=90)
    print("status", r.status_code)
    j = r.json()
    for d, p in zip(dois, j if isinstance(j, list) else []):
        if not p: print("MISS", d); continue
        print("###", d, "|", p.get("title"))
        print("   ", p.get("year"), p.get("venue"), "cites=", p.get("citationCount"))
        ab = (p.get("abstract") or "")
        print("   ABS:", ab[:900].replace("\n", " "))
        print()
except Exception as e:
    print("S2 ERR", e)
