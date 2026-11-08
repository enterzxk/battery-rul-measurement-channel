
import os, sys, json, time, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "lit-survey/1.0"})
dois = ["10.1016/j.jechem.2023.10.056", "10.1016/j.ress.2025.110850", "10.1016/j.etran.2026.100582",
        "10.1016/j.energy.2025.138263", "10.1016/j.energy.2023.126726", "10.1016/j.joule.2024.02.020"]
for d in dois:
    ok = False
    for attempt in range(4):
        try:
            r = S.get("https://api.semanticscholar.org/graph/v1/paper/DOI:" + d,
                      params={"fields": "title,abstract,year,venue,citationCount"}, timeout=60)
            if r.status_code == 200:
                j = r.json()
                print("### %s | %s | %s | cites=%s" % (d, j.get("year"), (j.get("title") or "")[:90], j.get("citationCount")))
                print("   ABS:", (j.get("abstract") or "(none)")[:1000].replace("\n", " "))
                print()
                ok = True; break
            else:
                time.sleep(6)
        except Exception as e:
            time.sleep(6)
    if not ok: print("FAIL", d)
    time.sleep(3)
