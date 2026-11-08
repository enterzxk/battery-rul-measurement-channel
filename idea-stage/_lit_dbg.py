
import os, sys, json, time, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": "lit-survey/1.0 (mailto:a@b.c)"})
r = S.get("https://api.openalex.org/works", params={"search": "theory of learning from different domains", "per-page": 2}, timeout=60)
print("status", r.status_code)
j = r.json()
print("keys", list(j.keys())[:6])
print("count", j.get("meta", {}).get("count"))
for w in j.get("results", [])[:2]:
    print(w.get("publication_year"), "|", w.get("title"), "|", w.get("doi"))
