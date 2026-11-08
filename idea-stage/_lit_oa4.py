
import os, sys, json, time, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "lit-survey/1.0 (mailto:a@b.c)"})
r = S.get("https://api.openalex.org/works/https://doi.org/10.1016/j.joule.2024.02.020", timeout=60)
print("status", r.status_code)
if r.status_code == 200:
    j = r.json()
    inv = j.get("abstract_inverted_index")
    if inv:
        pos = {}
        for w, idxs in inv.items():
            for i in idxs: pos[i] = w
        print(" ".join(pos[i] for i in sorted(pos))[:1500])
    else:
        print("no abstract")
else:
    print(r.text[:300])
